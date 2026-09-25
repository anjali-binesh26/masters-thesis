"""UC1 command-line UI: manual JSON input, preview, confirm, execute.

Run from any directory; imports resolve relative to this file. No network calls
occur at import time, during --prepare, or during the default offline preview.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import sys
from uuid import uuid4

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0,str(PROJECT))

from controller.amarisoft_api import AmarisoftAPI
from controller.executor import prepare_execution, execute_plan
from controller.validation import ValidationError, normalize_message, strict_json, positive_timeout


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    temporary.replace(path)


def read_json(path):
    return strict_json(Path(path).read_text(encoding='utf-8-sig'))


def load_manual_request(path):
    text = Path(path).read_text(encoding='utf-8-sig').strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    return normalize_message(strict_json(text),qos_patch=True)


def load_proposal(path, expected_id):
    text = Path(path).read_text(encoding='utf-8-sig').strip()
    # A single enclosing JSON code fence is allowed; prose or multiple objects
    # are not. Do not search for executable fragments inside an LLM response.
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    proposal = strict_json(text)
    if not isinstance(proposal,dict):
        raise ValidationError('Proposal must be an object')
    if set(proposal) - {'schema_version','request_id','status','intent','request','questions','reason'}:
        raise ValidationError('Unexpected proposal fields; LLM cannot define verification or rollback')
    if type(proposal.get('schema_version')) is not int or proposal['schema_version'] != 1:
        raise ValidationError('Expected schema_version 1')
    if proposal.get('request_id') != expected_id:
        raise ValidationError('Stale or unrelated output: request_id does not match the current operator input')
    if proposal.get('status') not in ('ready','needs_input','unsupported'):
        raise ValidationError('Unknown proposal status')
    if not isinstance(proposal.get('intent'),str) or not proposal['intent'].strip():
        raise ValidationError('Proposal needs a readable intent')
    if proposal['status'] == 'ready':
        proposal['request'] = normalize_message(proposal.get('request'),qos_patch=True)
    elif proposal.get('request') is not None:
        raise ValidationError('Incomplete/unsupported proposal must not contain an executable request')
    return proposal


def prepare_input(netsight, instruction):
    if not instruction.strip():
        raise ValidationError('Operator instruction cannot be empty')
    identifier = uuid4().hex
    payload = {'schema_version':1,'request_id':identifier,
               'created_at':datetime.now(timezone.utc).isoformat(),
               'operator_request':instruction}
    write_json(netsight/'attachments'/'operator_request.json',payload)
    # Never silently overwrite a customized prompt/reference on subsequent runs.
    for source,destination in (
        (PROJECT/'prompts'/'uc1_system_prompt.md',netsight/'prompts'/'uc1_system_prompt.md'),
        (PROJECT/'prompts'/'uc1_api_reference.md',netsight/'attachments'/'uc1_api_reference.md')):
        destination.parent.mkdir(parents=True,exist_ok=True)
        if not destination.exists():
            shutil.copyfile(source,destination)
    print(f'Prepared request {identifier}.')
    print('NetSight .env: PROMPT_FILE=prompts/uc1_system_prompt.md; OUTPUT_FILE=output/action.json')
    print('Run bash scripts/run_netsight_uc1.sh from masters-thesis, then preview with --proposal <NetSight output/action.json>.')
    return payload


def confirmation(summary):
    print('\nActual request, baseline, recovery and verification policy:')
    print(json.dumps(summary,indent=2))
    print('Approval includes verification reads. Recovery writes require separate ROLLBACK approval.')
    return input('Type APPLY to send this change, or anything else to cancel: ').strip() == 'APPLY'


def registration_step(summary):
    print('\nTimer update sent. Manually re-register EVERY listed UE (airplane mode off/on).')
    print('Wait until all are registered. This does not restart the Callbox.')
    print(json.dumps(summary['targets'],indent=2))
    return input('Type CHECK when ready, or anything else to leave verification pending: ').strip() == 'CHECK'


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--netsight-dir',type=Path,default=PROJECT.parent/'netsight')
    modes = result.add_mutually_exclusive_group()
    modes.add_argument('--prepare',metavar='NATURAL_LANGUAGE_REQUEST')
    modes.add_argument('--inspect',action='store_true',help='Confirm live reads; save project logs/live_state.json')
    modes.add_argument('--request',type=Path,help='Raw API JSON file; default: project request.json')
    modes.add_argument('--proposal',type=Path,help='Optional NetSight envelope file; requires current operator_request.json')
    modes.add_argument('--restore-from',type=Path,help='Review compensation from a previous run report')
    result.add_argument('--execute',action='store_true',help='Connect, preflight, and ask before writing')
    result.add_argument('--baseline',type=Path,help='Operator-confirmed current full API request, never LLM generated')
    result.add_argument('--host',default='127.0.0.1',help='Default uses local/SSH-forwarded API')
    result.add_argument('--port',type=int,default=9000)
    result.add_argument('--timeout',type=float,default=5.0)
    result.add_argument('--report',type=Path,help='Default: logs/uc1-<run ID>.json')
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    api = None
    report = None
    report_path = None
    try:
        positive_timeout(args.timeout)
        if args.prepare is not None:
            if args.execute:
                raise ValidationError('--prepare cannot execute changes')
            prepare_input(args.netsight_dir,args.prepare)
            return 0
        run_id = uuid4().hex
        report_path = args.report or PROJECT/'logs'/f'uc1-{run_id}.json'
        report = {'run_id':run_id,'started_at':datetime.now(timezone.utc).isoformat(),'events':[]}
        def audit(event, payload):
            report['events'].append({'at':datetime.now(timezone.utc).isoformat(),
                                     'event':event,'payload':copy.deepcopy(payload)})
            # Persist send intent before I/O so crashes retain the exact planned
            # message. This records intent, not proof the server received it.
            write_json(report_path,report)
        baseline = read_json(args.baseline) if args.baseline else None
        previous = None
        if args.restore_from:
            previous = read_json(args.restore_from)
            request = normalize_message(previous['plan']['compensation'])
            if baseline is None:
                baseline = previous['plan']['request']
            print('RESTORATION: confirm the saved baseline still describes this lab session.')
            print('Restoration is a new operation and is not automatically considered successful.')
            report['restore_from'] = str(args.restore_from)
        elif not args.inspect and args.proposal:
            current_input = read_json(args.netsight_dir/'attachments'/'operator_request.json')
            report['operator_input'] = current_input
            path = args.proposal or args.netsight_dir/'output'/'action.json'
            proposal = load_proposal(path,current_input['request_id'])
            report['proposal_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            report['proposal'] = proposal
            print('Operator request:',current_input['operator_request'])
            print('LLM interpretation:',proposal['intent'])
            if proposal['status'] != 'ready':
                print(json.dumps(proposal,indent=2))
                report['result'] = {'status':proposal['status']}
                return 2
            request = proposal['request']
        elif not args.inspect:
            path = args.request or PROJECT/'request.json'
            request = load_manual_request(path)
            report['input_mode'] = 'manual'
            report['request_file'] = str(path.resolve())
            report['request_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            report['manual_request'] = copy.deepcopy(request)
            print('Manual request file:',path)
        if not args.inspect and not args.execute:
            print(json.dumps(request,indent=2))
            print('Offline schema preview only. Use --execute for live preflight and confirmation.')
            report['result'] = {'status':'preview','request':request}
            return 0
        print(f'\nEndpoint: ws://{args.host}:{args.port}')
        print('This permits connection, authentication and read-only requests for this run.')
        print(json.dumps({'message':'config_get'} if args.inspect else request,indent=2))
        allowed = input('Type CONNECT to allow live reads, or anything else to cancel: ').strip() == 'CONNECT'
        audit('connection_confirmation',{'approved':allowed})
        if not allowed:
            report['result'] = {'status':'cancelled','write_sent':False}
            return 0
        api = AmarisoftAPI(args.host,args.port,password=os.environ.get('AMARISOFT_PASSWORD'),audit=audit)
        report['endpoint'] = api.url
        if previous and previous.get('endpoint') != api.url:
            raise ValidationError('Restoration endpoint differs from original report')
        api.connect(args.timeout)
        if args.inspect:
            snapshot = {'captured_at':datetime.now(timezone.utc).isoformat(),
                        'endpoint':api.url,
                        'config':api.send({'message':'config_get'},args.timeout),
                        'ues':api.send({'message':'ue_get'},args.timeout)}
            write_json(PROJECT/'logs'/'live_state.json',snapshot)
            report['result'] = {'status':'read_complete','snapshot':snapshot}
            print(json.dumps(snapshot,indent=2))
            return 0
        plan = prepare_execution(api,request,baseline=baseline,timeout=args.timeout)
        report['plan'] = plan.summary()
        write_json(report_path,report)
        def confirmed(summary):
            approved = confirmation(summary)
            audit('operator_confirmation',{'approved':approved})
            return approved
        def rollback_confirmed(summary):
            print('\nPartial application detected. Proposed recovery:')
            print(json.dumps(summary,indent=2))
            approved = input('Type ROLLBACK to restore these values, or anything else to leave recovery pending: ').strip() == 'ROLLBACK'
            audit('rollback_confirmation',{'approved':approved})
            return approved
        result = execute_plan(api,plan,confirm=confirmed,timeout=args.timeout,
                              after_apply=registration_step,confirm_rollback=rollback_confirmed)
        report['result'] = result
        print(json.dumps(result,indent=2))
        return 0 if result['status'] in ('verified','read_complete','cancelled') else 2
    except (Exception,KeyboardInterrupt) as exc:
        print(f'Controller stopped: {exc}',file=sys.stderr)
        if report is not None:
            # Some failures/interrupts occur after sending a write. Never imply
            # an unchanged network merely because the CLI raised an exception.
            writes = [e for e in report['events'] if e['event'] == 'send'
                      and e['payload'].get('message') not in ('config_get','ue_get','stats','log_get')]
            report['result'] = {'status':'unknown' if writes else 'rejected', 'error':str(exc)}
        return 2
    finally:
        if api is not None:
            try:
                api.disconnect()
            except Exception as exc:
                if report is not None:
                    report['disconnect_error'] = str(exc)
        if report is not None:
            write_json(report_path,report)
            print(f'Report: {report_path}')


if __name__ == '__main__':
    raise SystemExit(main())
