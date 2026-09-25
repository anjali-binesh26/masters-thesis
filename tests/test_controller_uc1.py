import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.controller_uc1 import load_manual_request, load_proposal, main, write_json
from controller.validation import ValidationError


class TestController(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root/'output'/'action.json'
        self.input_path = self.root/'attachments'/'operator_request.json'
        write_json(self.input_path,{'request_id':'current','operator_request':'Set NAS logging to info'})
        self.proposal = {'schema_version':1,'request_id':'current','status':'ready',
                         'intent':'Set NAS logging to info',
                         'request':{'message':'config_set','logs':{'layers':{'nas':{'level':'info'}}}}}
        write_json(self.path,self.proposal)
        self.report = self.root/'report.json'

    def cli(self,*args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            source = [] if any(a in args for a in ('--request','--prepare','--restore-from','--inspect')) else ['--proposal',str(self.path)]
            return main(['--netsight-dir',str(self.root),'--report',str(self.report),*source,*args])

    def test_load_current_proposal(self):
        self.assertEqual(load_proposal(self.path,'current')['request']['message'],'config_set')

    def test_stale_output_rejected(self):
        with self.assertRaises(ValidationError):
            load_proposal(self.path,'other')

    def test_llm_verification_directive_rejected(self):
        write_json(self.path,dict(self.proposal,verify_message={'message':'quit'}))
        with self.assertRaises(ValidationError):
            load_proposal(self.path,'current')

    def test_needs_input_does_not_connect(self):
        write_json(self.path,dict(self.proposal,status='needs_input',request=None,questions=['Which UE?']))
        with patch('scripts.controller_uc1.AmarisoftAPI') as api:
            self.assertEqual(self.cli('--execute'),2)
            api.assert_not_called()

    def test_invalid_rejected_before_connection(self):
        write_json(self.path,dict(self.proposal,request={'message':'quit'}))
        with patch('scripts.controller_uc1.AmarisoftAPI') as api:
            self.assertEqual(self.cli('--execute'),2)
            api.assert_not_called()

    def test_default_preview_never_connects(self):
        with patch('scripts.controller_uc1.AmarisoftAPI') as api:
            self.assertEqual(self.cli(),0)
            api.assert_not_called()
        self.assertEqual(json.loads(self.report.read_text())['result']['status'],'preview')

    def test_prepare_creates_input_and_prompt_without_network(self):
        with patch('scripts.controller_uc1.AmarisoftAPI') as api:
            self.assertEqual(self.cli('--prepare','Set timer to 10 minutes'),0)
            api.assert_not_called()
        self.assertTrue((self.root/'prompts'/'uc1_system_prompt.md').exists())
        self.assertNotEqual(json.loads(self.input_path.read_text())['request_id'],'current')

    def test_single_code_fence_accepted_prose_rejected(self):
        self.path.write_text('```json\n'+json.dumps(self.proposal)+'\n```')
        load_proposal(self.path,'current')
        self.path.write_text('Here is the answer: '+json.dumps(self.proposal))
        with self.assertRaises(ValidationError):
            load_proposal(self.path,'current')

    def test_full_cli_success_reports_and_disconnects(self):
        before = {'logs':{'layers':{'nas':{'level':'debug'}}}}
        after = {'logs':{'layers':{'nas':{'level':'info'}}}}
        with patch('scripts.controller_uc1.AmarisoftAPI') as constructor, patch('builtins.input',side_effect=['CONNECT','APPLY']):
            api = constructor.return_value
            api.url = 'ws://127.0.0.1:9000'
            api.send.side_effect = [before,before,{},after]
            self.assertEqual(self.cli('--execute'),0)
            api.disconnect.assert_called_once()
        report = json.loads(self.report.read_text())
        self.assertEqual(report['result']['status'],'verified')
        self.assertEqual(report['plan']['compensation']['logs']['layers']['nas']['level'],'debug')

    def test_cancel_sends_no_write(self):
        before = {'logs':{'layers':{'nas':{'level':'debug'}}}}
        with patch('scripts.controller_uc1.AmarisoftAPI') as constructor, patch('builtins.input',side_effect=['CONNECT','no']):
            api = constructor.return_value
            api.url = 'ws://127.0.0.1:9000'
            api.send.return_value = before
            self.assertEqual(self.cli('--execute'),0)
            self.assertEqual(api.send.call_count,1)
        self.assertEqual(json.loads(self.report.read_text())['result']['status'],'cancelled')

    def test_duplicate_json_key_rejected(self):
        self.path.write_text('{"schema_version":1,"schema_version":2}')
        with self.assertRaises(ValidationError):
            load_proposal(self.path,'current')

    def test_real_pipeline_over_mocked_websocket_and_restoration(self):
        """Exercise file parser, validator, executor, transport and report together."""
        write_json(self.path,self.proposal['request'])
        self.input_path.unlink()
        state = {'level':'debug'}
        sent = []
        with patch('controller.amarisoft_api.websocket.create_connection') as connect:
            ws = connect.return_value
            pending = []
            def open_socket(*args, **kwargs):
                pending.append({'message':'ready','type':'MME'})
                return ws
            connect.side_effect = open_socket
            def send(raw):
                request = json.loads(raw)
                sent.append(request)
                response = {'message':request['message'],'message_id':request['message_id']}
                if request['message'] == 'config_get':
                    response['logs'] = {'layers':{'nas':dict(state)}}
                else:
                    state.update(request['logs']['layers']['nas'])
                pending.append(response)
            ws.send.side_effect = send
            ws.recv.side_effect = lambda:json.dumps(pending.pop(0))
            with patch('builtins.input',side_effect=['CONNECT','APPLY','CONNECT','APPLY']):
                self.assertEqual(self.cli('--request',str(self.path),'--execute'),0)
                original_report = self.root/'original.json'
                original_report.write_bytes(self.report.read_bytes())
                self.assertEqual(state['level'],'info')
                self.assertEqual(self.cli('--restore-from',str(original_report),'--execute'),0)
            self.assertEqual(state['level'],'debug')
        report = json.loads(self.report.read_text())
        self.assertEqual(report['result']['status'],'verified')
        writes = [r for r in sent if r['message'] == 'config_set']
        self.assertEqual(len(writes),2)
        self.assertEqual(len({r['message_id'] for r in sent}),len(sent))
        self.assertTrue(any(e['event'] == 'operator_confirmation' for e in report['events']))

    def test_manual_preview_without_netsight(self):
        self.input_path.unlink()
        write_json(self.path,self.proposal['request'])
        with patch('scripts.controller_uc1.AmarisoftAPI') as api:
            self.assertEqual(self.cli('--request',str(self.path)),0)
            api.assert_not_called()
        self.assertEqual(json.loads(self.report.read_text())['input_mode'],'manual')

    def test_default_reads_project_request_without_netsight(self):
        write_json(self.root/'request.json',{'message':'ue_get'})
        with patch('scripts.controller_uc1.PROJECT',self.root), patch('scripts.controller_uc1.AmarisoftAPI') as api:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--report',str(self.report)]),0)
            api.assert_not_called()
        self.assertEqual(json.loads(self.report.read_text())['result']['request'],{'message':'ue_get'})

    def test_manual_recovery_requires_separate_approval(self):
        def state(nas,ip):
            return {'logs':{'layers':{'nas':{'level':nas},'ip':{'level':ip}}}}
        before,partial,after = state('debug','debug'),state('info','debug'),state('info','info')
        write_json(self.path,{'message':'config_set',**after})
        for answer,status,writes in [('no','recovery_pending',1),('ROLLBACK','rolled_back',2)]:
            with self.subTest(answer=answer):
                with patch('scripts.controller_uc1.AmarisoftAPI') as constructor, patch('builtins.input',side_effect=['CONNECT','APPLY',answer]):
                    api = constructor.return_value
                    api.url = 'ws://127.0.0.1:9000'
                    api.send.side_effect = [before,before,{},partial,partial,{},before]
                    self.assertEqual(self.cli('--request',str(self.path),'--execute'),2)
                    self.assertEqual(len([c for c in api.send.call_args_list if c.args[0]['message']=='config_set']),writes)
                report = json.loads(self.report.read_text())
                self.assertEqual(report['result']['status'],status)
                self.assertTrue(any(e['event']=='rollback_confirmation' for e in report['events']))

    def test_manual_rejects_prose_batches_duplicates_and_blocked_messages(self):
        for raw in ('Here is JSON: {"message":"ue_get"}', '[{"message":"ue_get"}]',
                    '{"message":"ue_get","message":"stats"}', '{"message":"quit"}'):
            with self.subTest(raw=raw):
                self.path.write_text(raw)
                with patch('scripts.controller_uc1.AmarisoftAPI') as api:
                    self.assertEqual(self.cli('--request',str(self.path),'--execute'),2)
                    api.assert_not_called()

    def test_manual_fence_accepted(self):
        self.path.write_text('```json\n{"message":"ue_get"}\n```')
        self.assertEqual(load_manual_request(self.path),{'message':'ue_get'})

    def test_declining_connection_sends_nothing(self):
        write_json(self.path,{'message':'ue_get'})
        with patch('scripts.controller_uc1.AmarisoftAPI') as api, patch('builtins.input',return_value='no'):
            self.assertEqual(self.cli('--request',str(self.path),'--execute'),0)
            api.assert_not_called()
        self.assertEqual(json.loads(self.report.read_text())['result']['status'],'cancelled')

    def test_closed_stdin_never_connects(self):
        write_json(self.path,{'message':'ue_get'})
        with patch('scripts.controller_uc1.AmarisoftAPI') as api, patch('builtins.input',side_effect=EOFError):
            self.assertEqual(self.cli('--request',str(self.path),'--execute'),2)
            api.assert_not_called()

    def test_manual_read_requires_connect_only(self):
        write_json(self.path,{'message':'ue_get'})
        with patch('scripts.controller_uc1.AmarisoftAPI') as constructor, patch('builtins.input',side_effect=['CONNECT']) as ask:
            api = constructor.return_value
            api.url = 'ws://127.0.0.1:9000'
            api.send.return_value = {'ue_list':[]}
            self.assertEqual(self.cli('--request',str(self.path),'--execute'),0)
            self.assertEqual(ask.call_count,1)
            self.assertEqual(api.send.call_args.args[0],{'message':'ue_get'})


if __name__ == '__main__':
    unittest.main()
