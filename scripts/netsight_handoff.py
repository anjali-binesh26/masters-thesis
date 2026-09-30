"""Review one NetSight proposal, approve copying it, then optionally run UC1.

No LLM calls or file watching. Controller CONNECT/APPLY approvals remain intact.
Raw source evidence is archived privately under project logs/handoff-<ID>/.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))
from controller.validation import normalize_message, strict_json, positive_timeout
from scripts.controller_uc1 import write_json


def extract_proposal(text):
    """Fail closed: one READY status outside fences and one JSON fence only."""
    blocks = []
    outside = []
    current = None
    for line in text.splitlines():
        if line.strip().startswith(('```', '~~~')):
            fence = line.strip()
            if current is None:
                if fence.lower() != '```json':
                    raise ValueError('Expected exactly one ```json block; other code blocks are not accepted')
                current = []
            else:
                if fence != '```':
                    raise ValueError('Malformed JSON code fence')
                blocks.append('\n'.join(current))
                current = None
        elif current is not None:
            current.append(line)
        else:
            outside.append(line)
    if current is not None:
        raise ValueError('Unclosed JSON code fence')
    statuses = re.findall(r'^\s*Status:\s*([A-Z_]+)\s*$', '\n'.join(outside), re.MULTILINE)
    if len(statuses) != 1 or statuses[0] not in ('READY', 'NEEDS_INPUT', 'UNSUPPORTED'):
        raise ValueError('Expected exactly one Status: READY, NEEDS_INPUT or UNSUPPORTED line')
    status = statuses[0]
    if status != 'READY':
        if blocks:
            raise ValueError('Refusal/clarification includes code: do not execute it')
        return status, None
    if len(blocks) != 1:
        raise ValueError('READY output must contain exactly one JSON block')
    value = strict_json(blocks[0])
    # The existing controller contract remains the authority; prose cannot set
    # host, baseline, approval flags, execution commands or recovery policies.
    return status, normalize_message(value, qos_patch=True)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unchanged(path, original):
    if path.read_bytes() != original:
        raise ValueError('A source file changed during review. Start the handoff again.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netsight-dir', type=Path, default=PROJECT.parent/'netsight')
    parser.add_argument('--output', type=Path, help='Override NetSight output/interfaces.md')
    parser.add_argument('--operator-request', type=Path, help='Override NetSight attachments/operator_request.txt')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=9000)
    parser.add_argument('--timeout', type=float, default=5.0)
    parser.add_argument('--baseline', type=Path, help='Trusted local baseline if required by this operation')
    args = parser.parse_args(argv)
    manifest = None
    manifest_path = None
    try:
        positive_timeout(args.timeout)
        source = (args.output or args.netsight_dir/'output'/'interfaces.md').resolve()
        instruction = (args.operator_request or args.netsight_dir/'attachments'/'operator_request.txt').resolve()
        raw = source.read_bytes()
        operator_raw = instruction.read_bytes()
        if not operator_raw.decode('utf-8-sig').strip():
            raise ValueError('Operator request is empty')
        if source.stat().st_mtime_ns < instruction.stat().st_mtime_ns:
            raise ValueError('Model output is older than the operator request. Run NetSight again.')
        print(f'Operator input: {instruction}')
        print(operator_raw.decode('utf-8-sig'))
        print(f'\nModel output: {source}')
        print(raw.decode('utf-8-sig'))
        print('\nTimestamps cannot prove these files belong to the same run. Check the instruction against the response.')
        status, request = extract_proposal(raw.decode('utf-8-sig'))
        if request is None:
            print(f'{status}: no executable proposal. request.json is unchanged.')
            return 0
        print('\nValidated proposal to copy to project request.json:')
        print(json.dumps(request, indent=2))
        print(f'Execution endpoint if later approved: ws://{args.host}:{args.port}')
        print('COPY confirms that you reviewed the proposal against this operator instruction.')
        if input('Type COPY to replace request.json, or anything else to cancel: ').strip() != 'COPY':
            print('Cancelled. No files changed and no controller started.')
            return 0
        unchanged(source, raw)
        unchanged(instruction, operator_raw)
        identifier = uuid4().hex
        archive = PROJECT/'logs'/f'handoff-{identifier}'
        archive.mkdir(parents=True, exist_ok=False)
        (archive/'llm_output.md').write_bytes(raw)
        (archive/'operator_request.txt').write_bytes(operator_raw)
        snapshot = archive/'request.json'
        write_json(snapshot, request)
        snapshot_raw = snapshot.read_bytes()
        report = PROJECT/'logs'/f'uc1-{identifier}.json'
        manifest_path = archive/'handoff.json'
        manifest = {
            'handoff_id': identifier, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'operator_request_sha256': digest(operator_raw), 'llm_output_sha256': digest(raw),
            'approved_request_sha256': digest(snapshot_raw),
            'association': 'Operator confirmed COPY after reviewing source instruction and model response.',
            'copy_approved': True, 'launch_approved': False,
            'controller_report': str(report), 'status': 'archived'}
        write_json(manifest_path, manifest)
        # Write the same bytes as the immutable run snapshot. Execute that snapshot
        # to avoid an unrelated edit to shared request.json changing this trial.
        write_json(PROJECT/'request.json', request)
        manifest['status'] = 'copied'
        write_json(manifest_path, manifest)
        print(f'Copied. Private evidence: {archive}')
        print('Running next will still ask CONNECT and, for changes, APPLY. It does not call the LLM.')
        if input('Type RUN to launch the controller, or anything else to stop here: ').strip() != 'RUN':
            return 0
        unchanged(snapshot, snapshot_raw)
        command = [sys.executable, str(PROJECT/'scripts'/'controller_uc1.py'),
                   '--request', str(snapshot), '--execute', '--host', args.host,
                   '--port', str(args.port), '--timeout', str(args.timeout), '--report', str(report)]
        if args.baseline:
            baseline_raw = args.baseline.read_bytes()
            normalize_message(strict_json(baseline_raw.decode('utf-8-sig')))
            baseline_copy = archive/'baseline.json'
            baseline_copy.write_bytes(baseline_raw)
            manifest['baseline_sha256'] = digest(baseline_raw)
            command.extend(['--baseline', str(baseline_copy)])
        manifest.update(launch_approved=True, status='controller_launch_requested')
        write_json(manifest_path, manifest)
        completed = subprocess.run(command, shell=False)
        manifest.update(status='controller_returned', controller_exit_code=completed.returncode)
        print(f'Controller report: {report}')
        print('Use the normal evidence recorder/exporter to save this report. Raw handoff files remain private.')
        return completed.returncode
    except (Exception, KeyboardInterrupt) as exc:
        print(f'Handoff stopped: {exc}', file=sys.stderr)
        if manifest is not None:
            manifest['handoff_error'] = str(exc)
        return 2
    finally:
        if manifest_path is not None:
            write_json(manifest_path, manifest)


if __name__ == '__main__':
    raise SystemExit(main())
