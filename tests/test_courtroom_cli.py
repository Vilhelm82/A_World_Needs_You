"""The live CLI must preflight before creating a world or starting role sessions."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import courtroom
import courtroom_v2 as c
from courtroom_backend import DeterministicBackend
from test_courtroom_v2 import fixture


class CourtroomCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.case = fixture()
        self.casefile = self.root / 'case.json'
        self.casefile.write_bytes(c.encode(self.case))
        self.config = self.root / 'models.json'
        self.config.write_bytes(c.encode({'storage_root': str(self.root / 'external'), 'defaults': {
            kind: {'provider': 'configured-provider', 'model': 'configured-model'}
            for kind in ('witness', 'juror', 'counsel', 'bench', 'support')}}))
        self.calls = []
        self.available = {('configured-provider', 'configured-model')}
        self.preflight_error = None
        owner = self

        class LocalTransport(DeterministicBackend):
            def __init__(self, config, assignments):
                super().__init__(config.storage_root / 'fake-transport')
                self.config, self.assignments = config, assignments
                self.reasoning_levels = {('configured-provider', 'configured-model'): ('medium', 'high')}
                owner.calls.append(('construct', set(assignments)))
                self.queue('W9', {'text': 'MODEL_SPEECH_PRIVATE_TO_AUDIENCE', 'data': {}})

            def preflight(self):
                owner.calls.append(('preflight',))
                if owner.preflight_error:
                    raise c.CourtError(owner.preflight_error)
                self.config.validate_models(self.assignments, self.list_models())
                return {'ready': True, 'version': '1.18.31'}

            def list_models(self):
                owner.calls.append(('catalog',))
                return owner.available

            def create_session(self, *args):
                owner.calls.append(('create_session', args[0]))
                return super().create_session(*args)

        module = ModuleType('courtroom_opencode')
        module.OpenCodeBackend = LocalTransport
        self.backend_module = patch.dict(sys.modules, {'courtroom_opencode': module})
        self.backend_module.start()

    def tearDown(self):
        self.backend_module.stop()
        self.tmp.cleanup()

    def run_cli(self, command, *extra, config=True, backend='opencode'):
        args = [command, '--root', str(self.root), '--world', 'cli-test', '--backend', backend]
        if config:
            args += ['--config', str(self.config)]
        args.extend(extra)
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = courtroom.main(args)
        return code, output.getvalue(), error.getvalue()

    def test_live_start_requires_config_before_world_creation(self):
        code, _, error = self.run_cli('start', '--case', str(self.casefile), config=False)
        self.assertEqual(code, 2)
        self.assertIn('--config', error)
        self.assertFalse((self.root / 'worlds').exists())
        self.assertEqual(self.calls, [])

    def test_failed_preflight_cannot_create_a_world_or_role_sessions(self):
        self.preflight_error = 'Server unavailable.'
        code, _, error = self.run_cli('start', '--case', str(self.casefile))
        self.assertEqual(code, 2)
        self.assertIn('Server unavailable', error)
        self.assertFalse((self.root / 'worlds').exists())
        self.assertFalse(any(call[0] == 'create_session' for call in self.calls))

    def test_missing_witness_foundation_fails_before_backend_construction(self):
        case = fixture()
        del case['roles']['W9']['background']
        self.casefile.write_bytes(c.encode(case))
        for command in ('start', 'backend-check'):
            with self.subTest(command=command):
                code, _, error = self.run_cli(command, '--case', str(self.casefile))
                self.assertEqual(code, 2)
                self.assertIn('background', error)
                self.assertEqual(self.calls, [])
                self.assertFalse((self.root / 'worlds').exists())

    def test_unavailable_model_cannot_create_a_world(self):
        self.available = {('wrong-provider', 'configured-model')}
        code, _, error = self.run_cli('start', '--case', str(self.casefile))
        self.assertEqual(code, 2)
        self.assertIn('Unavailable model assignments', error)
        self.assertFalse((self.root / 'worlds').exists())

    def test_backend_check_validates_assignments_without_initialising_world(self):
        code, output, error = self.run_cli('backend-check', '--case', str(self.casefile))
        self.assertEqual((code, error), (0, ''))
        self.assertIn('1.18.31', output)
        self.assertFalse((self.root / 'worlds').exists())
        self.assertFalse(any(call[0] == 'create_session' for call in self.calls))

    def test_unwritable_world_storage_fails_before_case_commit(self):
        with patch.object(courtroom, '_check_world_storage', side_effect=PermissionError('Read-only runtime.')):
            code, _, error = self.run_cli('start', '--case', str(self.casefile))
        self.assertEqual(code, 2)
        self.assertIn('Read-only runtime', error)
        self.assertFalse((self.root / 'worlds').exists())

    def test_list_models_requires_no_case_and_returns_only_catalog(self):
        code, output, error = self.run_cli('list-models')
        self.assertEqual((code, error), (0, ''))
        self.assertEqual(json.loads(output), {'models': [
            {'provider': 'configured-provider', 'model': 'configured-model', 'reasoning_levels': ['medium', 'high']}]})
        self.assertEqual(self.calls[0], ('construct', set()))
        self.assertFalse((self.root / 'worlds').exists())

    def test_start_resume_and_turn_preserve_sessions_without_printing_speech(self):
        code, _, error = self.run_cli('start', '--case', str(self.casefile))
        self.assertEqual((code, error), (0, ''))
        world = c.world_path(self.root, 'cli-test')
        before = c.load(world / c.AREA / 'runtime.json')['sessions']
        self.assertLess(self.calls.index(('preflight',)),
                        next(i for i, call in enumerate(self.calls) if call[0] == 'create_session'))
        code, _, error = self.run_cli('resume')
        self.assertEqual((code, error), (0, ''))
        after = c.load(world / c.AREA / 'runtime.json')['sessions']
        self.assertEqual({who: entry['session_id'] for who, entry in before.items()},
                         {who: entry['session_id'] for who, entry in after.items()})
        code, output, error = self.run_cli('turn', '--identity', 'W9', '--kind', 'dialogue',
                                         '--audience', 'player', 'W9')
        self.assertEqual((code, error), (0, ''))
        self.assertNotIn('MODEL_SPEECH_PRIVATE_TO_AUDIENCE', output)
        self.assertEqual(c.read_events(world)[-1]['text'], 'MODEL_SPEECH_PRIVATE_TO_AUDIENCE')

    def test_existing_world_cannot_be_replaced_by_another_case(self):
        self.assertEqual(self.run_cli('start', '--case', str(self.casefile))[0], 0)
        changed = fixture()
        changed['case_id'] = 'another-case'
        self.casefile.write_bytes(c.encode(changed))
        code, _, error = self.run_cli('start', '--case', str(self.casefile))
        self.assertEqual(code, 2)
        self.assertIn('committed case', error)
        self.assertEqual(c.read_case(c.world_path(self.root, 'cli-test')), self.case)

    def test_missing_operation_arguments_fail_before_starting_sessions(self):
        for command in ('turn', 'human', 'control', 'examine'):
            with self.subTest(command=command):
                code, _, _ = self.run_cli(command)
                self.assertEqual(code, 2)
                self.assertEqual(self.calls, [])

    def test_mock_start_and_scripted_turn_need_no_config_or_opencode(self):
        code, output, error = self.run_cli('start', '--case', str(self.casefile), '--allow-mock',
                                         config=False, backend='mock')
        self.assertEqual((code, error), (0, ''))
        self.assertIn('mock', output)
        script = self.root / 'script.json'
        script.write_bytes(c.encode({'W9': [{'text': 'SCRIPTED_SPEECH', 'data': {}}]}))
        code, output, error = self.run_cli('turn', '--allow-mock', '--script', str(script),
                                         '--identity', 'W9', '--kind', 'dialogue',
                                         '--audience', 'player', 'W9', config=False, backend='mock')
        self.assertEqual((code, error), (0, ''))
        self.assertNotIn('SCRIPTED_SPEECH', output)
        self.assertEqual(self.calls, [])

    def test_mock_requires_explicit_opt_in(self):
        code, _, error = self.run_cli('start', '--case', str(self.casefile), config=False, backend='mock')
        self.assertEqual(code, 2)
        self.assertIn('--allow-mock', error)
        self.assertFalse((self.root / 'worlds').exists())

    def test_backend_serve_delegates_to_isolated_launcher_without_case(self):
        served = []
        module = ModuleType('courtroom_opencode_host')
        module.serve = lambda config, executable='opencode': served.append((config.base_url, executable)) or 0
        with patch.dict(sys.modules, {'courtroom_opencode_host': module}):
            code, _, error = self.run_cli('backend-serve', '--executable', '/example/opencode')
        self.assertEqual((code, error), (0, ''))
        self.assertEqual(served, [('http://127.0.0.1:4096', '/example/opencode')])
        self.assertEqual(self.calls, [])

    def test_command_line_help_does_not_import_backend_or_need_config(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/courtroom.py'), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('backend-check', result.stdout)
        self.assertIn('backend-serve', result.stdout)
        self.assertIn('deliberate', result.stdout)


if __name__ == '__main__':
    unittest.main()
