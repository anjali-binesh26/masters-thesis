import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts.export_uc1_evidence import (
    main, render, summarize, safe_request, run_interactive, parse_netsight_log, _fence_for)


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


def _make_report(run_id, started_at, status='verified', extra=None):
    report = {
        'run_id': run_id, 'started_at': started_at,
        'endpoint': 'ws://private.example:9000',
        'plan': {'mode': 'config',
                 'request': {'message': 'config_set', 'logs': {'layers': {'NAS': {'level': 'info'}}}}},
        'events': [
            {'at': started_at, 'event': 'send', 'payload': {'message': 'config_set'}},
            {'at': started_at, 'event': 'response', 'payload': {
                'message': 'config_set', 'license_id': 'license-secret',
                'imsi': '001019999999999'}},
        ],
        'result': {'status': status, 'verified': True,
                   'before': {'logs.layers.NAS.level': 'debug'},
                   'after': {'logs.layers.NAS.level': 'info'},
                   'response': {'license_user': 'private-org'}},
    }
    if extra:
        report.update(extra)
    return report


class TestInteractiveTrial(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.project = self.tmp / 'masters-thesis'
        self.netsight = self.tmp / 'netsight'
        (self.project / 'logs').mkdir(parents=True)
        (self.project / 'llm_outputs' / 'use case 1').mkdir(parents=True)
        (self.netsight / 'attachments').mkdir(parents=True)
        (self.netsight / 'output').mkdir(parents=True)
        (self.netsight / 'logs').mkdir(parents=True)
        (self.netsight / 'attachments' / 'operator_request.txt').write_text(
            'Set the core-wide T3512 timer to 10 minutes.\n', encoding='utf-8')
        (self.netsight / 'output' / 'interfaces.md').write_text(
            'Status: READY\n\n```json\n{"message": "config_set", "t3512": 600}\n```\n', encoding='utf-8')
        (self.netsight / 'logs' / 'netsight_2026-09-30_12-00-00.log').write_text(
            '2026-09-30 12:00:00 [INFO] Model: gemma4:31b\n'
            '2026-09-30 12:00:01 [INFO] Token usage: input=36357, output=780, total=37137\n'
            '2026-09-30 12:02:20 [INFO] Done. (140.9s)\n', encoding='utf-8')
        self.patchers = [patch('scripts.export_uc1_evidence.PROJECT', self.project)]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run(self, answers, netsight_dir=None):
        queue = iter(answers)
        out = io.StringIO()
        args = SimpleNamespace(netsight_dir=netsight_dir or self.netsight)
        with contextlib.redirect_stdout(out):
            code = run_interactive(args, input_func=lambda prompt: next(queue), print_func=print)
        return code, out.getvalue()

    def _write_report(self, run_id, started_at, status='verified', extra=None):
        report = _make_report(run_id, started_at, status, extra)
        (self.project / 'logs' / f'uc1-{run_id}.json').write_text(json.dumps(report), encoding='utf-8')
        return report

    def test_successful_change_with_restoration(self):
        self._write_report('a' * 32, '2026-09-30T12:00:00Z')
        self._write_report('c' * 32, '2026-09-30T13:00:00Z',
                            extra={'restore_from': f'logs/uc1-{"a"*32}.json'})
        # log select=1, change=1, restoration=default(2), filename, confirm
        code, out = self._run(['1', '1', '', 'trial-one', 'y'])
        self.assertEqual(code, 0)
        target = self.project / 'llm_outputs' / 'use case 1' / 'trial-one.md'
        self.assertTrue(target.exists())
        text = target.read_text(encoding='utf-8')
        self.assertIn('Sanitized controller change evidence', text)
        self.assertIn('Sanitized restoration evidence', text)
        self.assertIn('a' * 32, text)
        self.assertIn('c' * 32, text)
        self.assertIn('Agent elapsed time: 140.9s', text)
        self.assertIn('Model: gemma4:31b', text)
        self.assertIn('Not recorded', text)  # Assessment section
        self.assertIn(out, out)  # preview printed

    def test_clarification_without_execution(self):
        # No controller reports exist at all.
        code, out = self._run(['', 'trial-refusal', 'y'])
        self.assertEqual(code, 0)
        target = self.project / 'llm_outputs' / 'use case 1' / 'trial-refusal.md'
        text = target.read_text(encoding='utf-8')
        self.assertIn('None selected. This trial recorded no controller execution.', text)
        self.assertNotIn('Sanitized restoration evidence', text)

    def test_llm_response_with_fenced_json_block_preserved_verbatim(self):
        # A response embedding its own ```json fence must not corrupt the outer fence.
        fenced_response = (
            'Status: READY\n\nProposal:\n```json\n{"message": "config_set", "t3512": 600}\n```\n')
        (self.netsight / 'output' / 'interfaces.md').write_text(fenced_response, encoding='utf-8')
        code, out = self._run(['', 'trial-fenced', 'y'])
        self.assertEqual(code, 0)
        target = self.project / 'llm_outputs' / 'use case 1' / 'trial-fenced.md'
        text = target.read_text(encoding='utf-8')
        self.assertIn(fenced_response, text)
        outer_fence = _fence_for(fenced_response)
        self.assertIn(f'{outer_fence}\n{fenced_response}\n{outer_fence}', text)
        self.assertGreater(len(outer_fence), 3)

    def test_missing_or_mismatched_source_files(self):
        (self.netsight / 'attachments' / 'operator_request.txt').unlink()
        alt = self.tmp / 'alt_request.txt'
        alt.write_text('Alternate operator request text.\n', encoding='utf-8')
        # operator missing -> supply alt path; interfaces present; log=1;
        # no reports exist, so no report-selection prompt; filename; confirm
        code, out = self._run([str(alt), '1', 'trial-alt', 'y'])
        self.assertEqual(code, 0)
        target = self.project / 'llm_outputs' / 'use case 1' / 'trial-alt.md'
        text = target.read_text(encoding='utf-8')
        self.assertIn('Alternate operator request text.', text)
        self.assertIn(str(alt.name), text)

        # Now test skipping a missing file entirely (blank answer -> Not recorded).
        (self.netsight / 'output' / 'interfaces.md').unlink()
        code, out = self._run([str(alt), '', '1', 'trial-skip', 'y'])
        self.assertEqual(code, 0)
        text = (self.project / 'llm_outputs' / 'use case 1' / 'trial-skip.md').read_text(encoding='utf-8')
        self.assertIn('Not recorded: source file unavailable at export time.', text)

    def test_secret_exclusion_from_controller_evidence(self):
        self._write_report('a' * 32, '2026-09-30T12:00:00Z')
        code, out = self._run(['1', '1', '', 'trial-secret', 'y'])
        self.assertEqual(code, 0)
        text = (self.project / 'llm_outputs' / 'use case 1' / 'trial-secret.md').read_text(encoding='utf-8')
        for secret in ('license-secret', '001019999999999', 'private-org', 'private.example'):
            self.assertNotIn(secret, text)

    def test_overwrite_and_path_traversal_protection(self):
        existing = self.project / 'llm_outputs' / 'use case 1' / 'existing.md'
        existing.write_text('# Pre-existing\n', encoding='utf-8')
        original = existing.read_text(encoding='utf-8')
        # log=1, no reports, traversal filename rejected, existing filename rejected,
        # then a valid new filename succeeds.
        code, out = self._run(['1', '../evil.md', 'existing', 'trial-ok', 'y'])
        self.assertEqual(code, 0)
        self.assertEqual(existing.read_text(encoding='utf-8'), original)
        self.assertFalse((self.tmp / 'evil.md').exists())
        self.assertTrue((self.project / 'llm_outputs' / 'use case 1' / 'trial-ok.md').exists())

    def test_preserves_original_files(self):
        report = self._write_report('a' * 32, '2026-09-30T12:00:00Z')
        operator_before = (self.netsight / 'attachments' / 'operator_request.txt').read_bytes()
        interfaces_before = (self.netsight / 'output' / 'interfaces.md').read_bytes()
        log_before = (self.netsight / 'logs' / 'netsight_2026-09-30_12-00-00.log').read_bytes()
        report_before = (self.project / 'logs' / f'uc1-{"a"*32}.json').read_bytes()
        code, out = self._run(['1', '1', '', 'trial-preserve', 'y'])
        self.assertEqual(code, 0)
        self.assertEqual((self.netsight / 'attachments' / 'operator_request.txt').read_bytes(), operator_before)
        self.assertEqual((self.netsight / 'output' / 'interfaces.md').read_bytes(), interfaces_before)
        self.assertEqual((self.netsight / 'logs' / 'netsight_2026-09-30_12-00-00.log').read_bytes(), log_before)
        self.assertEqual((self.project / 'logs' / f'uc1-{"a"*32}.json').read_bytes(), report_before)

    def test_parse_netsight_log_missing_fields_not_invented(self):
        info = parse_netsight_log('2026-09-30 12:00:00 [INFO] Something unrelated\n')
        self.assertEqual(info, {})


if __name__ == '__main__':
    unittest.main()
