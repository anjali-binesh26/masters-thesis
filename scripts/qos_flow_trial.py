"""Human-approved, one-phone QoS lifecycle feasibility. See tests/uc2_qos_feasibility.md."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0,str(PROJECT))

from controller.amarisoft_api import AmarisoftAPI
from controller import qos_trial
from controller.validation import strict_json, positive_timeout, ValidationError


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    tmp.replace(path)


def approve(token, value):
    print(json.dumps(value,indent=2))
    return input(f'Type {token} to approve, or anything else to stop: ').strip() == token


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',required=True)
    parser.add_argument('--port',type=int,default=9000)
    parser.add_argument('--timeout',type=float,default=5)
    parser.add_argument('--imsi')
    parser.add_argument('--imei',help='14 or 15 digits; not the 16-digit IMEISV')
    parser.add_argument('--apn',default='internet')
    parser.add_argument('--remote-port',type=int,default=55000,
                        help='Isolated UDP test port; no traffic generator is started')
    parser.add_argument('--five-qi',type=int,choices=range(5,10),default=9)
    parser.add_argument('--execute',action='store_true',help='Otherwise read-only preflight')
    parser.add_argument('--assume-release-default',action='store_true',
                        help='Allow explicit approval of the documented false default, not verified runtime policy')
    parser.add_argument('--cleanup-from',type=Path,help='Trusted private trial report; never LLM output')
    parser.add_argument('--reconcile-qfi',type=int,
                        help='With --cleanup-from: reconcile one observed flow after a recorded creation timeout')
    args = parser.parse_args(argv)
    positive_timeout(args.timeout)
    if args.reconcile_qfi is not None and not args.cleanup_from:
        parser.error('--reconcile-qfi requires --cleanup-from')
    if not args.cleanup_from and (not args.imsi or not args.imei):
        parser.error('--imsi and --imei are required for a new trial')
    report = {'schema_version':1,'kind':'qos_flow_feasibility','run_id':uuid4().hex,
              'started_at':stamp(),'events':[],'qos_verified':False}
    path = PROJECT/'logs'/('qos-trial-'+report['run_id']+'.json')

    def record(event, payload):
        report['events'].append({'timestamp':stamp(),'event':event,'payload':payload})
        save(path,report)

    def confirmed(token, value):
        allowed = approve(token,value)
        record('approval',{'token':token,'approved':allowed})
        return allowed

    def policy():
        print('Cleanup can release the entire PDU session if automatic_release=true.')
        assumed = args.assume_release_default
        if assumed:
            print('You are relying on the documented false default after checking configuration.')
            print('Runtime policy remains unverified. Approval accepts possible loss of this')
            print('test phone\'s internet PDU session during cleanup; preservation is not guaranteed.')
        else:
            print('Only confirm if you established automatic_release=false for this APN;')
            print('a vendor default or UE snapshot alone does not establish the current policy.')
        source = input('Record your release-policy evidence and its limitations (blank cancels): ').strip()
        if not source:
            return False
        evidence = {'basis':'documented_default_assumption' if assumed else 'operator_established',
                    'automatic_release_expected':False,'runtime_verified_by_runner':False,
                    'apn':report['plan']['before']['apn'],'source':source,
                    'session_release_risk_accepted':False}
        allowed = confirmed('ASSUME_DEFAULT' if assumed else 'POLICY',evidence)
        evidence['session_release_risk_accepted'] = assumed and allowed
        report['release_policy'] = {**evidence,'operator_confirmed':allowed,'checked_at':stamp()}
        save(path,report)
        return allowed

    api = None
    try:
        previous = None
        if args.cleanup_from:
            previous = strict_json(args.cleanup_from.read_text(encoding='utf-8-sig'))
            if (previous.get('kind') != 'qos_flow_feasibility'
                    or previous.get('schema_version') != 1):
                raise ValidationError('Expected a private QoS trial report')
        api = AmarisoftAPI(args.host,args.port,password=os.environ.get('AMARISOFT_PASSWORD'),audit=record)
        report['endpoint'] = api.url
        if previous and previous.get('endpoint') != api.url:
            raise ValidationError('Cleanup endpoint must match the original trial')
        if not confirmed('CONNECT',{'endpoint':api.url,'permission':'connect and read state'}):
            report['result'] = {'status':'cancelled','write_sent':False}
            return 0
        api.connect(args.timeout)
        if previous:
            report['source_run_id'] = previous['run_id']
            report['plan'] = previous['plan']
            if args.reconcile_qfi is not None:
                report['reconciliation'] = qos_trial.reconcile_timeout(api,previous,args.reconcile_qfi,args.timeout)
                cleanup_evidence = report['reconciliation']
            else:
                report['creation'] = previous['creation']
                responses = [e['payload'] for e in previous['events'] if e['event']=='creation_response']
                if len(responses) != 1 or any(responses[0].get(k) != report['creation'].get(k)
                        for k in ('pdu_session_id','qos_flow_id')) or 'warning' in responses[0]:
                    raise ValidationError('Missing or inconsistent saved creation response')
                qos_trial.observe(api,report['plan'],report['creation'],args.timeout)
                cleanup_evidence = report['creation']
        else:
            report['plan'] = qos_trial.prepare(api,args.imsi,args.imei,args.apn,
                args.remote_port,args.five_qi,args.timeout)
        print(json.dumps(report['plan'],indent=2))
        save(path,report)
        if not args.execute:
            report['result'] = {'status':'preflight_only','write_sent':False}
            return 0
        if not policy():
            report['result'] = {'status':'policy_not_established','write_sent':False}
            return 2
        if args.reconcile_qfi is not None:
            print('Confirm this sole new flow belongs to your timed-out trial and no other operator created it.')
            if not confirmed('RECONCILE',report['reconciliation']):
                report['result'] = {'status':'cleanup_pending','write_sent':False}
                return 2
        if not previous:
            report['creation'] = qos_trial.create(api,report['plan'],
                confirm=lambda p:confirmed('CREATE',p), record=record,
                policy_confirmed=True,timeout=args.timeout)
            save(path,report)
            if report['creation']['status'] != 'accepted_unverified':
                report['result'] = report['creation']
                return 2
            if not confirmed('CHECK',{'instruction':'Wait for signalling to settle, then check flow presence.'}):
                report['result'] = {'status':'cleanup_pending','qos_verified':False}
                return 2
            report['observed'] = qos_trial.observe(api,report['plan'],report['creation'],args.timeout)
            print('Test flow exists. QoS values and throughput are NOT verified by this observation.')
            save(path,report)
            cleanup_evidence = report['creation']
        report['cleanup'] = qos_trial.cleanup(api,report['plan'],cleanup_evidence,
            confirm=lambda r:confirmed('CLEANUP',r),record=record,policy_confirmed=True,timeout=args.timeout)
        save(path,report)
        if report['cleanup']['status'] != 'cleanup_sent':
            report['result'] = report['cleanup']
            return 2
        if not confirmed('CHECK',{'instruction':'Wait for release signalling, then check original session remains.'}):
            report['result'] = {'status':'cleanup_verification_pending'}
            return 2
        report['result'] = qos_trial.verify_cleanup(api,report['plan'],args.timeout)
        print(json.dumps(report['result'],indent=2))
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        report['result'] = {'status':'unknown' if any(e['event'] in ('creation_intent','cleanup_intent')
                            for e in report['events']) or args.cleanup_from else 'stopped',
                            'error':str(exc),'qos_verified':False}
        print('Stopped:',exc,file=sys.stderr)
        print('Do not retry a creation after an uncertain outcome. Inspect state and the saved report.')
        return 2
    finally:
        if api is not None:
            try:
                api.disconnect()
            except Exception as exc:
                report['disconnect_error'] = str(exc)
        save(path,report)
        print('Private report:',path)


if __name__ == '__main__':
    raise SystemExit(main())
