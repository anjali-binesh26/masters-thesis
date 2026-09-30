"""Export selected UC1 evidence to Markdown without copying raw lab data.

Offline only. Preview by default; --write saves under project llm_outputs.
Existing Markdown text is preserved, NOT sanitized by this exporter.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))
from controller.validation import normalize_message, strict_json, MESSAGE_SCHEMAS, BLOCKED_MESSAGES

STATUSES = {'preview', 'read_complete', 'verified', 'cancelled', 'rejected',
            'needs_input', 'unsupported', 'unknown', 'not_applied', 'conflict',
            'accepted_unverified', 'pending_verification', 'verification_failed',
            'recovery_pending', 'rolled_back', 'rollback_failed'}
MODES = {'read', 'config', 'config_manual', 'timer', 'qos_manual'}
OPERATIONS = set(MESSAGE_SCHEMAS) | set(BLOCKED_MESSAGES)
IDENTIFIERS = {'imsi', 'nai', 'imei', 'message_id', 'ue_id'}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return dt.astimezone(timezone.utc).isoformat()


def safe_request(value):
    """Export only validated supported parameters, excluding target identifiers.

    Validation is an allowlist: unknown fields and arbitrary strings never pass
    through, apart from subscriber identifiers which are explicitly removed.
    Invalid/rejected requests are omitted rather than copying error text.
    """
    try:
        normalized = normalize_message(value, qos_patch=True)
    except (ValueError, TypeError, PermissionError):
        operation = value.get('message') if isinstance(value, dict) else None
        return {'message': operation if operation in OPERATIONS else 'omitted',
                'parameters': 'omitted: request did not pass export validation'}
    return {key: val for key, val in normalized.items() if key not in IDENTIFIERS}


def safe_values(value):
    # Executor config read-back uses flattened paths. Validate each leaf through
    # the same request allowlist; never copy arbitrary response fields or keys.
    output = {}
    if not isinstance(value, dict):
        return output
    for path, item in value.items():
        if not isinstance(path, str):
            continue
        parts = path.split('.')
        if len(parts) not in (1, 4) or any(not p for p in parts):
            continue
        request = {'message': 'config_set'}
        target = request
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = item
        try:
            normalize_message(request)
        except (ValueError, TypeError, PermissionError):
            continue
        output[path] = item
    return output


def read_report(path):
    raw = Path(path).read_bytes()
    report = strict_json(raw.decode('utf-8-sig'))
    if not isinstance(report, dict) or not re.fullmatch(r'[0-9a-f]{32}', str(report.get('run_id', ''))):
        raise ValueError('Expected a UC1 report with a 32-character hexadecimal run_id')
    timestamp(report.get('started_at'))
    if not isinstance(report.get('result'), dict):
        raise ValueError('Report is incomplete: no final result')
    if not isinstance(report.get('events', []), list):
        raise ValueError('Invalid events list')
    return report, hashlib.sha256(raw).hexdigest()


def summarize(report):
    result = report['result']
    plan = report.get('plan', {})
    if not isinstance(plan, dict):
        plan = {}
    out = {'run_id': report['run_id'], 'started_at_utc': timestamp(report['started_at']),
           'status': result.get('status') if result.get('status') in STATUSES else 'unrecognized'}
    if plan.get('mode') in MODES:
        out['mode'] = plan['mode']
    for key in ('verified', 'write_sent', 'rollback_attempted', 'rollback_succeeded'):
        if type(result.get(key)) is bool:
            out[key] = result[key]
    proposal = report.get('proposal', {})
    candidate = report.get('manual_request')
    if candidate is None and isinstance(proposal, dict):
        candidate = proposal.get('request')
    if candidate is not None:
        out['input_request_without_identifiers'] = safe_request(candidate)
    for key in ('request', 'compensation'):
        value = plan.get(key) or result.get(key)
        if isinstance(value, dict):
            out[key + '_without_identifiers'] = safe_request(value)
    for key in ('before', 'after', 'restored'):
        value = safe_values(result.get(key, plan.get(key)))
        if value:
            out[key] = value
    # Error/warning text may include credentials, addresses or identifiers.
    out['error_recorded'] = any(key in result for key in (
        'error', 'apply_error', 'verification_error', 'rollback_error'))
    out['warning_recorded'] = False
    timeline = []
    for event in report.get('events', []):
        if not isinstance(event, dict) or not isinstance(event.get('payload'), dict):
            continue
        kind, payload = event.get('event'), event['payload']
        row = {}
        try:
            row['at_utc'] = timestamp(event.get('at'))
        except (ValueError, TypeError):
            pass
        if kind in ('connection_confirmation', 'operator_confirmation', 'rollback_confirmation'):
            row['event'] = kind
            if type(payload.get('approved')) is bool:
                row['approved'] = payload['approved']
        elif kind in ('send', 'response'):
            row['event'] = 'send_intent' if kind == 'send' else 'response'
            operation = payload.get('message')
            row['message'] = operation if operation in OPERATIONS else 'omitted'
            if kind == 'response':
                row['error_present'] = 'error' in payload
                row['warning_present'] = 'warning' in payload
                out['warning_recorded'] |= row['warning_present']
        else:
            continue
        timeline.append(row)
    out['timeline'] = timeline
    response = result.get('response', {})
    if isinstance(response, dict):
        out['warning_recorded'] |= 'warning' in response
    out['recorded_write_send_intents'] = sum(
        row.get('event') == 'send_intent' and row.get('message') in
        {'config_set', 'ue_modify_bearer', 'ue_modify_pdu_session'} for row in timeline)
    out['send_intent_note'] = 'Intent is not proof of delivery. Counts cover recognized writes in this report only.'
    # Timer verification retains values and number of observations, not UE keys.
    observed = result.get('observed')
    if isinstance(observed, list):
        timers = [{k: row[k] for k in ('t3512', 't3412') if type(row.get(k)) is int}
                  for row in observed if isinstance(row, dict)]
        out['timer_observations_without_identifiers'] = [row for row in timers if row]
    snapshot = result.get('snapshot', {})
    if isinstance(snapshot, dict) and isinstance(snapshot.get('ues'), dict):
        rows = snapshot['ues'].get('ue_list')
        if isinstance(rows, list):
            out['ue_count'] = len(rows)
            out['registered_ue_count'] = sum(isinstance(row, dict) and row.get('registered') is True for row in rows)
    restore = report.get('restore_from')
    if isinstance(restore, str):
        match = re.search(r'(?:^|[/\\])uc1-([0-9a-f]{32})\.json$', restore)
        if match:
            out['restores_run_id'] = match.group(1)
    return out


def render(report, digest, kind):
    linkage = {
        'independent': 'Independent controller evidence; no LLM-to-execution association asserted.',
        'llm-trial': 'Operator assigned this run to the LLM trial in this document. The exporter has not verified that the model JSON was copied unchanged.',
        'restoration': 'Operator assigned this run as restoration evidence. This is not by itself proof of automatic failure recovery.',
    }[kind]
    return (f"\n\n<!-- uc1-evidence:{report['run_id']} -->\n"
            f"## Controller evidence — {timestamp(report['started_at'])}\n\n"
            f"{linkage}\n\nRaw report SHA-256: `{digest}`\n\n"
            "Allowlisted export: identities, endpoints, file paths, raw responses and free-text errors are omitted. "
            "Keep the original report privately. Existing document content is not sanitized.\n\n"
            "```json\n" + json.dumps(summarize(report), indent=2) + '\n```\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', nargs='*', type=Path, help='Exact report files; when omitted, use project logs/uc1-*.json')
    parser.add_argument('--list', action='store_true', help='List runs chronologically without exporting')
    parser.add_argument('--output', type=Path, help='Markdown file under project llm_outputs; existing content is preserved')
    parser.add_argument('--kind', choices=('independent', 'llm-trial', 'restoration'), default='independent')
    parser.add_argument('--write', action='store_true', help='Write the previewed evidence; never connects to the Callbox')
    args = parser.parse_args(argv)
    try:
        if not args.list and not args.reports:
            raise ValueError('Select report files explicitly for export; use --list to find them')
        paths = args.reports or sorted((PROJECT/'logs').glob('uc1-*.json'))
        reports = [read_report(path) for path in paths]
        reports.sort(key=lambda pair: timestamp(pair[0]['started_at']))
        if args.list:
            for report, _ in reports:
                summary = summarize(report)
                request = summary.get('request_without_identifiers', summary.get('input_request_without_identifiers', {}))
                print(summary['started_at_utc'], report['run_id'], summary['status'], json.dumps(request, separators=(',', ':')))
            return 0
        root = (PROJECT/'llm_outputs').resolve()
        destinations = {}
        for report, digest in reports:
            stamp = datetime.fromisoformat(timestamp(report['started_at'])).strftime('%Y-%m-%d_%H%M%SZ')
            target = (args.output or root/'controller evidence'/f'{stamp}_{report["run_id"]}.md').resolve()
            if not target.is_relative_to(root) or target.suffix.lower() != '.md':
                raise ValueError('Output must be a .md file inside this project llm_outputs folder')
            if target not in destinations:
                destinations[target] = target.read_text(encoding='utf-8-sig') if target.exists() else ''
            marker = f"<!-- uc1-evidence:{report['run_id']} -->"
            if marker in destinations[target]:
                print(f'Already recorded: {report["run_id"]}; skipped.')
                continue
            block = render(report, digest, args.kind)
            destinations[target] += block
            print(block)
        if args.write:
            for target, content in destinations.items():
                if target.exists() and target.read_text(encoding='utf-8-sig') == content:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + '.tmp')
                temporary.write_text(content, encoding='utf-8')
                temporary.replace(target)
                print(f'Saved: {target}')
        else:
            print('Preview only. Add --write to save. Review existing Markdown separately before publishing.')
        return 0
    except (ValueError, OSError, TypeError) as exc:
        print(f'Export stopped: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
