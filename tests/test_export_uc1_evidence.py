import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.export_uc1_evidence import main, render, summarize, safe_request


class TestEvidenceExport(unittest.TestCase):
    def setUp(self):
        self.report = {
            'run_id': 'a'*32, 'started_at': '2026-09-30T14:00:00+02:00',
            'endpoint': 'ws://private.example:9000',
            'request_file': '/home/private-user/request.json',
            'manual_request': {'message': 'config_set', 'logs': {'layers': {'nas': {'level': 'info'}}}},
            'plan': {'mode': 'config', 'request': {'message': 'config_set', 'logs': {'layers': {'NAS': {'level': 'info'}}}},
                     'compensation': {'message': 'config_set', 'logs': {'layers': {'NAS': {'level': 'debug'}}}}},
            'events': [
                {'at': '2026-09-30T12:00:01Z', 'event': 'operator_confirmation', 'payload': {'approved': True}},
                {'at': '2026-09-30T12:00:02Z', 'event': 'send', 'payload': {'message': 'config_set'}},
                {'at': '2026-09-30T12:00:03Z', 'event': 'response', 'payload': {'message': 'config_get',
                    'license_id': 'license-secret', 'imsi': '001019999999999', 'warning': 'password=secret-text'}}],
            'result': {'status': 'verified', 'verified': True,
                       'before': {'logs.layers.NAS.level': 'debug'},
                       'after': {'logs.layers.NAS.level': 'info'},
                       'response': {'license_user': 'private-org'}}}

    def test_allowlist_keeps_evidence_without_raw_secrets(self):
        original = copy.deepcopy(self.report)
        output = render(self.report, 'b'*64, 'independent')
        for secret in ('private.example', 'private-user', 'license-secret', '001019999999999', 'secret-text', 'private-org'):
            self.assertNotIn(secret, output)
        result = summarize(self.report)
        self.assertEqual(result['started_at_utc'], '2026-09-30T12:00:00+00:00')
        self.assertEqual(result['after'], {'logs.layers.NAS.level': 'info'})
        self.assertEqual(result['recorded_write_send_intents'], 1)
        self.assertTrue(result['warning_recorded'])
        self.assertEqual(self.report, original)

    def test_unknown_fields_and_invalid_strings_not_exported(self):
        self.report['manual_request']['secret'] = 'hidden-secret'
        self.report['result']['after'] = {'logs.layers.NAS.level': 'hidden-secret',
                                        'license_id': 'license-secret'}
        output = render(self.report, 'b'*64, 'independent')
        self.assertNotIn('hidden-secret', output)
        self.assertNotIn('license-secret', output)

    def test_identity_fields_removed_from_valid_request(self):
        result = safe_request({'message': 'ue_get', 'imsi': '001019999999999', 'imei': '123456789012345', 'message_id': 'private-id'})
        self.assertEqual(result, {'message': 'ue_get'})

    def test_rejected_report_has_no_invented_confirmation_or_reason(self):
        self.report['events'] = []
        self.report.pop('plan')
        self.report.pop('manual_request')
        self.report['result'] = {'status': 'rejected', 'error': 'private-user password=secret-text'}
        result = summarize(self.report)
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['timeline'], [])
        self.assertTrue(result['error_recorded'])
        self.assertNotIn('secret-text', json.dumps(result))
        self.assertNotIn('write_sent', result)

    def test_restoration_link_and_timer_values_without_identity(self):
        self.report['restore_from'] = '/home/private-user/logs/uc1-' + 'c'*32 + '.json'
        self.report['result']['observed'] = [{'identity': ['private-subscriber'], 't3512': 600}]
        result = summarize(self.report)
        self.assertEqual(result['restores_run_id'], 'c'*32)
        self.assertEqual(result['timer_observations_without_identifiers'], [{'t3512': 600}])
        self.assertNotIn('private-subscriber', json.dumps(result))

    def test_preview_append_preserve_existing_text_and_skip_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'report.json'
            source.write_text(json.dumps(self.report), encoding='utf-8')
            target = root/'llm_outputs'/'trial.md'
            target.parent.mkdir()
            target.write_text('# Original model output\n', encoding='utf-8')
            argv = [str(source), '--output', str(target), '--kind', 'llm-trial']
            with patch('scripts.export_uc1_evidence.PROJECT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
                self.assertEqual(target.read_text(), '# Original model output\n')
                self.assertEqual(main(argv + ['--write']), 0)
                first = target.read_bytes()
                self.assertEqual(main(argv + ['--write']), 0)
                self.assertEqual(target.read_bytes(), first)
            text = target.read_text()
            self.assertTrue(text.startswith('# Original model output\n'))
            self.assertEqual(text.count('<!-- uc1-evidence:'), 1)
            self.assertIn('Operator assigned', text)

    def test_output_cannot_escape_llm_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'report.json'
            source.write_text(json.dumps(self.report))
            with patch('scripts.export_uc1_evidence.PROJECT', root), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(source), '--output', str(root/'outside.md'), '--write']), 2)
            self.assertFalse((root/'outside.md').exists())

    def test_list_chronological_and_default_file_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'logs').mkdir()
            later = copy.deepcopy(self.report)
            later['run_id'] = 'd'*32
            later['started_at'] = '2026-09-30T15:00:00Z'
            for report in (later, self.report):
                (root/'logs'/f'uc1-{report["run_id"]}.json').write_text(json.dumps(report))
            capture = io.StringIO()
            with patch('scripts.export_uc1_evidence.PROJECT', root), contextlib.redirect_stdout(capture):
                self.assertEqual(main(['--list']), 0)
                lines = capture.getvalue().splitlines()
                self.assertIn('a'*32, lines[0])
                self.assertIn('d'*32, lines[1])
                self.assertEqual(main([str(root/'logs'/f'uc1-{"a"*32}.json'), '--write']), 0)
            self.assertTrue((root/'llm_outputs'/'controller evidence'/f'2026-09-30_120000Z_{"a"*32}.md').exists())


if __name__ == '__main__':
    unittest.main()
