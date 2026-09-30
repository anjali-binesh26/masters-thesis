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


if __name__ == '__main__':
    unittest.main()
