import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.netsight_handoff import extract_proposal, main

READY = 'Status: READY\nInterpretation: Read UEs\n\n```json\n{"message":"ue_get"}\n```\nVerification: read only.'


class TestHandoff(unittest.TestCase):
    def test_extract_valid_and_refusal(self):
        self.assertEqual(extract_proposal(READY), ('READY', {'message': 'ue_get'}))
        for status in ('NEEDS_INPUT', 'UNSUPPORTED'):
            self.assertEqual(extract_proposal(f'Status: {status}\nExplain why.'), (status, None))

    def test_ambiguous_invalid_and_blocked_never_accepted(self):
        for text in (READY + '\n```json\n{"message":"stats"}\n```',
                     READY.replace('READY', 'UNSUPPORTED'),
                     READY.replace('ue_get', 'quit'),
                     READY.replace('"message":"ue_get"', '"message":"ue_get","message":"stats"'),
                     READY.replace('{"message":"ue_get"}', '[{"message":"ue_get"}]'),
                     READY + '\nStatus: UNSUPPORTED',
                     READY.replace('```json', '```bash'),
                     READY.replace('```\nVerification', 'Verification'),
                     READY.replace('{"message":"ue_get"}', '{"message":"ue_get","host":"evil"}')):
            with self.subTest(text=text), self.assertRaises((ValueError, PermissionError)):
                extract_proposal(text)

    def setup_files(self, root, text=READY):
        netsight = root/'netsight'
        (netsight/'attachments').mkdir(parents=True)
        (netsight/'output').mkdir()
        instruction = netsight/'attachments'/'operator_request.txt'
        output = netsight/'output'/'interfaces.md'
        instruction.write_text('Show registered phones.')
        output.write_text(text)
        os.utime(instruction, (1000, 1000))
        os.utime(output, (2000, 2000))
        (root/'request.json').write_text('{"message":"stats"}')
        return netsight, instruction, output

    def test_copy_and_run_archives_and_launches_without_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            netsight, instruction, output = self.setup_files(root)
            with patch('scripts.netsight_handoff.PROJECT', root), patch('builtins.input', side_effect=['COPY', 'RUN']), \
                 patch('scripts.netsight_handoff.subprocess.run') as run, contextlib.redirect_stdout(io.StringIO()):
                run.return_value.returncode = 0
                self.assertEqual(main(['--netsight-dir', str(netsight)]), 0)
                command = run.call_args.args[0]
                self.assertFalse(run.call_args.kwargs['shell'])
                self.assertIn('--execute', command)
                snapshot = Path(command[command.index('--request') + 1])
                self.assertEqual(snapshot.read_bytes(), (root/'request.json').read_bytes())
                self.assertEqual((snapshot.parent/'llm_output.md').read_bytes(), output.read_bytes())
                manifest = json.loads((snapshot.parent/'handoff.json').read_text())
                self.assertTrue(manifest['copy_approved'])
                self.assertTrue(manifest['launch_approved'])

    def test_copy_declined_or_refused_does_not_mutate(self):
        for text in (READY, 'Status: NEEDS_INPUT\nWhich layer?'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                netsight, _, _ = self.setup_files(root, text)
                before = (root/'request.json').read_bytes()
                with patch('scripts.netsight_handoff.PROJECT', root), patch('builtins.input', return_value='NO'), \
                     patch('scripts.netsight_handoff.subprocess.run') as run, contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['--netsight-dir', str(netsight)]), 0)
                    run.assert_not_called()
                self.assertEqual((root/'request.json').read_bytes(), before)
                self.assertFalse((root/'logs').exists())

    def test_run_declined_leaves_copy_but_no_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            netsight, _, _ = self.setup_files(root)
            with patch('scripts.netsight_handoff.PROJECT', root), patch('builtins.input', side_effect=['COPY', 'NO']), \
                 patch('scripts.netsight_handoff.subprocess.run') as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--netsight-dir', str(netsight)]), 0)
                run.assert_not_called()
            self.assertEqual(json.loads((root/'request.json').read_text()), {'message': 'ue_get'})

    def test_stale_or_changed_source_never_copied(self):
        for stale in (True, False):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                netsight, instruction, output = self.setup_files(root)
                if stale:
                    os.utime(instruction, (3000, 3000))
                def approve(prompt):
                    output.write_text(READY.replace('ue_get', 'stats'))
                    return 'COPY'
                with patch('scripts.netsight_handoff.PROJECT', root), patch('builtins.input', side_effect=approve), \
                     patch('scripts.netsight_handoff.subprocess.run') as run, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(['--netsight-dir', str(netsight)]), 2)
                    run.assert_not_called()
                self.assertEqual(json.loads((root/'request.json').read_text()), {'message': 'stats'})

    def test_eof_does_not_copy_or_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            netsight, _, _ = self.setup_files(root)
            with patch('scripts.netsight_handoff.PROJECT', root), patch('builtins.input', side_effect=EOFError), \
                 patch('scripts.netsight_handoff.subprocess.run') as run, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['--netsight-dir', str(netsight)]), 2)
                run.assert_not_called()
            self.assertFalse((root/'logs').exists())


if __name__ == '__main__':
    unittest.main()
