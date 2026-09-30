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
from uuid import uuid4

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


def parse_netsight_log(text):
    """Pull only the fields this exporter understands from a NetSight agent log.

    Missing fields are simply absent; nothing is guessed or defaulted.
    """
    info = {}
    match = re.search(r'\bModel: (\S+)', text)
    if match:
        info['model'] = match.group(1)
    match = re.search(r'Token usage: input=(\d+), output=(\d+), total=(\d+)', text)
    if match:
        info['input_tokens'] = int(match.group(1))
        info['output_tokens'] = int(match.group(2))
        info['total_tokens'] = int(match.group(3))
    match = re.search(r'Done\. \(([\d.]+)s\)', text)
    if match:
        # Wall-clock time for the whole agent run, not a model inference metric.
        info['agent_elapsed_seconds'] = float(match.group(1))
    return info


def _fence_for(text):
    # Fenced code containing its own ``` (e.g. a JSON block) needs a longer outer fence.
    longest = max((len(run) for run in re.findall(r'`+', text)), default=0)
    return '`' * max(3, longest + 1)


def _file_provenance(label, path, base_dir):
    try:
        rel = path.relative_to(base_dir)
    except ValueError:
        rel = path.name
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f'{label}: `{rel}` (netsight repo), modified {modified}, SHA-256 `{digest}`'


def _resolve_source_file(label, default_path, input_func, print_func):
    path = default_path
    while True:
        if path is not None and path.is_file():
            return path
        print_func(f'{label} not found at: {path}')
        answer = input_func(f'Enter a path for {label}, or leave blank to skip: ').strip()
        if not answer:
            return None
        path = Path(answer).expanduser()


def _list_netsight_logs(netsight_dir):
    logs_dir = netsight_dir / 'logs'
    if not logs_dir.is_dir():
        return []
    return sorted(logs_dir.glob('netsight_*.log'))


def _select_netsight_log(candidates, input_func, print_func):
    if not candidates:
        print_func('No NetSight agent logs found.')
        return None
    print_func('Available NetSight logs (not assumed to match the current output):')
    for index, path in enumerate(candidates, 1):
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        print_func(f'  [{index}] {path.name}  (modified {modified})')
    answer = input_func('Select a NetSight log by number, or leave blank to skip: ').strip()
    if not answer:
        return None
    try:
        index = int(answer)
    except ValueError:
        return None
    if 1 <= index <= len(candidates):
        return candidates[index - 1]
    return None


def _list_controller_reports():
    entries = []
    for path in sorted((PROJECT / 'logs').glob('uc1-*.json')):
        try:
            report, digest = read_report(path)
        except (ValueError, OSError, TypeError) as exc:
            print(f'Skipping unreadable report {path.name}: {exc}', file=sys.stderr)
            continue
        entries.append((report, digest))
    entries.sort(key=lambda pair: timestamp(pair[0]['started_at']))
    return entries


def _print_report_choices(entries, print_func):
    for index, (report, _digest) in enumerate(entries, 1):
        summary = summarize(report)
        request = summary.get('request_without_identifiers') or summary.get('input_request_without_identifiers') or {}
        operation = request.get('message', 'unknown') if isinstance(request, dict) else 'unknown'
        print_func(f'  [{index}] {summary["started_at_utc"]}  operation={operation}  '
                   f'status={summary["status"]}  run_id={report["run_id"]}')


def _select_report(entries, input_func, print_func, prompt, suggested_index=None):
    if not entries:
        print_func('No controller reports available.')
        return None
    hint = f' [default {suggested_index}]' if suggested_index else ''
    answer = input_func(f'{prompt} (number, or "none"{hint}): ').strip().lower()
    if not answer and suggested_index:
        answer = str(suggested_index)
    if not answer or answer == 'none':
        return None
    try:
        index = int(answer)
    except ValueError:
        return None
    if 1 <= index <= len(entries):
        return entries[index - 1]
    return None


def _suggest_restoration_index(entries, change_run_id):
    for index, (report, _digest) in enumerate(entries, 1):
        summary = summarize(report)
        if summary.get('restores_run_id') == change_run_id:
            return index
    return None


def render_trial_evidence(report, digest, heading, note):
    return (f'### {heading}\n\n{note}\n\nRaw report SHA-256: `{digest}`\n\n'
            'Allowlisted export: identities, endpoints, file paths, raw responses and '
            'free-text errors are omitted.\n\n'
            '```json\n' + json.dumps(summarize(report), indent=2) + '\n```\n')


def _resolve_output_path(filename):
    if not filename or filename in ('.', '..') or '/' in filename or '\\' in filename:
        raise ValueError('Enter a plain filename with no path separators')
    if not filename.lower().endswith('.md'):
        filename += '.md'
    root = (PROJECT / 'llm_outputs' / 'use case 1').resolve()
    target = (root / filename).resolve()
    if target.parent != root or not target.is_relative_to(root):
        raise ValueError('Output must stay inside llm_outputs/use case 1')
    if target.exists():
        raise ValueError(f'{target.name} already exists; choose a different name')
    return target


def _generate_trial_id():
    now = datetime.now(timezone.utc)
    return f'UC1-TRIAL-{now.strftime("%Y%m%d-%H%M%S")}-{uuid4().hex[:6]}'


def build_trial_document(trial_id, provenance_lines, operator_section, llm_section,
                          measurements_lines, change_evidence, restoration_evidence):
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    parts = [f'# {trial_id}\n\nDate: {date_str} (UTC)\n']
    parts.append(
        '## Source provenance\n\n' + '\n'.join(f'- {line}' for line in provenance_lines) +
        '\n\nThis record captures only files present at export time. Overwritten NetSight '
        'outputs or operator requests cannot be recovered automatically.\n'
    )
    parts.append('## Operator request\n\n' + operator_section)
    parts.append('## LLM response\n\n' + llm_section)
    parts.append('## NetSight measurements\n\n' + '\n'.join(f'- {line}' for line in measurements_lines) +
                  '\n\n"Agent elapsed time" is wall-clock time for the whole agent run '
                  '(document loading plus generation), not a pure inference measurement.\n')
    parts.append('## Sanitized controller change evidence\n\n' + change_evidence)
    if restoration_evidence is not None:
        parts.append('## Sanitized restoration evidence\n\n' + restoration_evidence)
    parts.append('## Assessment / human corrections\n\nNot recorded\n')
    parts.append('## Operator notes\n\n')
    return '\n'.join(parts)


def run_interactive(args, input_func=input, print_func=print):
    """Combine NetSight files and one selected controller report into one trial record.

    Offline only: reads local files, never connects to the Callbox, calls an LLM,
    or writes to the network. Source files are only ever read, never modified.
    """
    netsight_dir = (args.netsight_dir or (PROJECT.parent / 'netsight')).expanduser().resolve()
    print_func(f'Using NetSight repository: {netsight_dir}')

    operator_path = _resolve_source_file(
        'operator request (attachments/operator_request.txt)',
        netsight_dir / 'attachments' / 'operator_request.txt', input_func, print_func)
    interfaces_path = _resolve_source_file(
        'LLM response (output/interfaces.md)',
        netsight_dir / 'output' / 'interfaces.md', input_func, print_func)

    provenance = []
    if operator_path is not None:
        line = _file_provenance('Operator request', operator_path, netsight_dir)
        print_func(line)
        provenance.append(line)
        operator_text = operator_path.read_text(encoding='utf-8-sig', errors='replace')
        fence = _fence_for(operator_text)
        operator_section = ('Shown exactly as read from the source file; not automatically '
                             'sanitized. It may itself contain sensitive data — review before '
                             f'sharing.\n\n{fence}\n' + operator_text + f'\n{fence}\n')
    else:
        provenance.append('Operator request: not available (source file missing at export time)')
        operator_section = 'Not recorded: source file unavailable at export time.\n'

    if interfaces_path is not None:
        line = _file_provenance('LLM response', interfaces_path, netsight_dir)
        print_func(line)
        provenance.append(line)
        llm_text = interfaces_path.read_text(encoding='utf-8-sig', errors='replace')
        fence = _fence_for(llm_text)
        llm_section = ('Shown exactly as read from the source file; wording is preserved '
                       'verbatim, including any errors in its own explanation. It may itself '
                       f'contain sensitive data — review before sharing.\n\n{fence}\n' + llm_text + f'\n{fence}\n')
    else:
        provenance.append('LLM response: not available (source file missing at export time)')
        llm_section = 'Not recorded: source file unavailable at export time.\n'

    log_candidates = _list_netsight_logs(netsight_dir)
    selected_log = _select_netsight_log(log_candidates, input_func, print_func)
    measurements_lines = []
    if selected_log is not None:
        provenance.append(_file_provenance('NetSight log', selected_log, netsight_dir))
        parsed = parse_netsight_log(selected_log.read_text(encoding='utf-8', errors='replace'))
        measurements_lines.append(f'Source: `{selected_log.relative_to(netsight_dir)}` (netsight repo)')
        measurements_lines.append(f'Model: {parsed.get("model", "Not recorded")}')
        measurements_lines.append(f'Input tokens: {parsed.get("input_tokens", "Not recorded")}')
        measurements_lines.append(f'Output tokens: {parsed.get("output_tokens", "Not recorded")}')
        measurements_lines.append(f'Total tokens: {parsed.get("total_tokens", "Not recorded")}')
        elapsed = parsed.get('agent_elapsed_seconds')
        measurements_lines.append(
            f'Agent elapsed time: {elapsed}s' if elapsed is not None else 'Agent elapsed time: Not recorded')
    else:
        measurements_lines.append('No NetSight log selected: Not recorded')

    entries = _list_controller_reports()
    print_func('Controller reports (chronological):')
    _print_report_choices(entries, print_func)
    change_choice = _select_report(entries, input_func, print_func,
                                    'Select the change report')
    suggested = None
    if change_choice is not None:
        suggested = _suggest_restoration_index(entries, change_choice[0]['run_id'])
    restoration_choice = _select_report(entries, input_func, print_func,
                                         'Select the optional restoration report', suggested)

    if change_choice is not None:
        report, digest = change_choice
        provenance.append(f'Controller change report: run_id `{report["run_id"]}`, '
                           f'started_at {timestamp(report["started_at"])}, SHA-256 `{digest}`')
        change_evidence = render_trial_evidence(
            report, digest, 'Change',
            'Operator selected this run as the change record for this trial. Selection '
            'records the operator\'s association; it is not proof of unchanged copying from the model.')
    else:
        provenance.append('Controller change report: none selected (e.g. clarification/refusal trial)')
        change_evidence = 'None selected. This trial recorded no controller execution.\n'

    restoration_evidence = None
    if restoration_choice is not None:
        report, digest = restoration_choice
        provenance.append(f'Controller restoration report: run_id `{report["run_id"]}`, '
                           f'started_at {timestamp(report["started_at"])}, SHA-256 `{digest}`')
        restoration_evidence = render_trial_evidence(
            report, digest, 'Restoration',
            'Operator selected this run as restoration evidence for this trial. This is not '
            'by itself proof of automatic failure recovery.')

    trial_id = _generate_trial_id()
    document = build_trial_document(trial_id, provenance, operator_section, llm_section,
                                     measurements_lines, change_evidence, restoration_evidence)

    while True:
        filename = input_func('Output filename under llm_outputs/use case 1/ '
                               '(blank to cancel): ').strip()
        if not filename:
            print_func('Cancelled: no output filename provided.')
            return 1
        try:
            target = _resolve_output_path(filename)
            break
        except ValueError as exc:
            print_func(f'Invalid filename: {exc}')

    print_func('----- Preview -----')
    print_func(document)
    print_func('----- End preview -----')
    confirm = input_func('Save this trial record? [y/N]: ').strip().lower()
    if confirm != 'y':
        print_func('Not saved.')
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.tmp')
    temporary.write_text(document, encoding='utf-8')
    temporary.replace(target)
    print_func(f'Saved: {target}')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', nargs='*', type=Path, help='Exact report files; when omitted, use project logs/uc1-*.json')
    parser.add_argument('--list', action='store_true', help='List runs chronologically without exporting')
    parser.add_argument('--output', type=Path, help='Markdown file under project llm_outputs; existing content is preserved')
    parser.add_argument('--kind', choices=('independent', 'llm-trial', 'restoration'), default='independent')
    parser.add_argument('--write', action='store_true', help='Write the previewed evidence; never connects to the Callbox')
    parser.add_argument('--interactive', action='store_true',
                         help='Build one combined trial record from NetSight files and a selected controller report')
    parser.add_argument('--netsight-dir', type=Path, default=None,
                         help='Path to the sibling netsight repository (default: ../netsight next to this project)')
    args = parser.parse_args(argv)
    if args.interactive:
        return run_interactive(args)
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
