import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from scripts import qos_flow_trial as cli
from tests.test_qos_trial import state, IMSI, IMEI


class TestQoSTrialCLI(unittest.TestCase):
    def run_cli(self, root, inputs, responses, extra=()):
        api = MagicMock()
        api.url = 'ws://lab:9000'
        api.send.side_effect = responses
        with patch.object(cli,'PROJECT',Path(root)), patch.object(cli,'AmarisoftAPI',return_value=api), \
                patch('builtins.input',side_effect=inputs), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(['--host','lab','--imsi',IMSI,'--imei',IMEI,*extra])
        reports = list((Path(root)/'logs').glob('qos-trial-*.json'))
        return code,api,json.loads(reports[-1].read_text()),reports[-1]

    def test_read_only_preflight(self):
        with tempfile.TemporaryDirectory() as root:
            code,api,report,_ = self.run_cli(root,['CONNECT'],[state()])
            self.assertEqual(code,0)
            self.assertEqual(report['result']['status'],'preflight_only')
            self.assertEqual([c.args[0]['message'] for c in api.send.call_args_list],['ue_get'])
            api.disconnect.assert_called_once()

    def test_missing_policy_blocks_all_writes(self):
        with tempfile.TemporaryDirectory() as root:
            code,api,report,_ = self.run_cli(root,['CONNECT',''],[state()],['--execute'])
            self.assertEqual(code,2)
            self.assertEqual(report['result']['status'],'policy_not_established')
            self.assertEqual(api.send.call_count,1)

    def test_complete_lifecycle_does_not_claim_qos_verified(self):
        with tempfile.TemporaryDirectory() as root:
            inputs = ['CONNECT','current policy checked by operator','POLICY','CREATE','CHECK','CLEANUP','CHECK']
            responses = [state(),state(),{'pdu_session_id':2,'qos_flow_id':3},
                         state(flows=(3,)),state(flows=(3,)),state(flows=(3,)),{},state()]
            code,api,report,_ = self.run_cli(root,inputs,responses,['--execute'])
            self.assertEqual(code,0)
            self.assertEqual(report['result']['status'],'session_restored')
            self.assertFalse(report['result']['qos_verified'])
            writes = [c.args[0]['message'] for c in api.send.call_args_list if c.args[0]['message']!='ue_get']
            self.assertEqual(writes,['ue_activate_dedicated_bearer','ue_deactivate_bearer'])

    def test_lost_reply_keeps_creation_intent_and_never_retries(self):
        with tempfile.TemporaryDirectory() as root:
            code,api,report,_ = self.run_cli(root,['CONNECT','checked','POLICY','CREATE'],
                [state(),state(),TimeoutError('lost')],['--execute'])
            self.assertEqual(code,2)
            self.assertEqual(report['result']['status'],'unknown')
            self.assertIn('creation_intent',[e['event'] for e in report['events']])
            self.assertEqual(api.send.call_count,3)

    def test_closed_stdin_never_connects(self):
        with tempfile.TemporaryDirectory() as root:
            _,api,_,_ = self.run_cli(root,[EOFError()],[],['--execute'])
            api.connect.assert_not_called()
            api.send.assert_not_called()

    def test_default_assumption_requires_distinct_approval_and_is_recorded(self):
        for token,accepted in [('POLICY',False),('ASSUME_DEFAULT',True)]:
            with self.subTest(token=token), tempfile.TemporaryDirectory() as root:
                inputs = ['CONNECT','No overrides in checked config; runtime unknown',token]
                if accepted:
                    inputs.append('NO')  # decline CREATE; test policy evidence only
                _,api,report,_ = self.run_cli(root,inputs,[state()],
                    ['--execute','--assume-release-default'])
                policy = report['release_policy']
                self.assertEqual(policy['basis'],'documented_default_assumption')
                self.assertEqual(policy['operator_confirmed'],accepted)
                self.assertEqual(policy['session_release_risk_accepted'],accepted)
                self.assertFalse(policy['runtime_verified_by_runner'])
                self.assertEqual(api.send.call_count,1)

    def test_cleanup_from_private_report_never_recreates(self):
        with tempfile.TemporaryDirectory() as root:
            _,_,_,source = self.run_cli(root,['CONNECT','checked','POLICY','CREATE','NO'],
                [state(),state(),{'pdu_session_id':2,'qos_flow_id':3}],['--execute'])
            # Move the source away so run_cli reliably finds the new report.
            stored = Path(root)/'original.json'
            source.rename(stored)
            code,api,report,_ = self.run_cli(root,['CONNECT','checked','POLICY','CLEANUP','CHECK'],
                [state(flows=(3,)),state(flows=(3,)),state(flows=(3,)),{},state()],
                ['--cleanup-from',str(stored),'--execute'])
            self.assertEqual(code,0)
            writes = [c.args[0]['message'] for c in api.send.call_args_list if c.args[0]['message']!='ue_get']
            self.assertEqual(writes,['ue_deactivate_bearer'])
            self.assertTrue(report['result']['restoration_verified'])

    def test_reconciled_cleanup_requires_approval_and_preserves_original(self):
        for approval in ('NO','RECONCILE'):
            with self.subTest(approval=approval), tempfile.TemporaryDirectory() as root:
                _,_,original,source = self.run_cli(root,['CONNECT','checked','POLICY','CREATE'],
                    [state(),state(),TimeoutError('lost')],['--execute'])
                # MagicMock transport does not emit the real API's send/timeout audit events.
                original['events'].extend([
                    {'event':'send','payload':dict(original['plan']['request'],message_id='trial')},
                    {'event':'timeout','payload':{'message':'ue_activate_dedicated_bearer','message_id':'trial'}}])
                source.unlink()
                stored = Path(root)/'original.json'
                saved = json.dumps(original)
                stored.write_text(saved)
                inputs = ['CONNECT','checked','POLICY',approval]
                responses = [state(flows=(3,))]
                if approval == 'RECONCILE':
                    inputs.extend(['CLEANUP','CHECK'])
                    responses.extend([state(flows=(3,)),state(flows=(3,)),{},state()])
                code,api,report,_ = self.run_cli(root,inputs,responses,
                    ['--cleanup-from',str(stored),'--reconcile-qfi','3','--execute'])
                self.assertEqual(stored.read_text(),saved)
                self.assertNotIn('creation',report)
                self.assertFalse(report['reconciliation']['creation_acknowledged'])
                writes = [c.args[0]['message'] for c in api.send.call_args_list if c.args[0]['message']!='ue_get']
                self.assertEqual(writes,['ue_deactivate_bearer'] if approval=='RECONCILE' else [])
                self.assertEqual(code,0 if approval=='RECONCILE' else 2)


if __name__ == '__main__':
    unittest.main()
