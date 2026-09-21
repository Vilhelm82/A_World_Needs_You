"""Witnesses have committed personal knowledge; missing authoring is not testimony."""
from copy import deepcopy
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_courtroom_v2 import fixture, event
import courtroom_v2 as c
import courtroom_sessions as s
import courtroom_cases as builder
from courtroom_backend import DeterministicBackend


class WitnessFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.case = fixture()
        self.backend = DeterministicBackend(self.root / 'sessions')

    def tearDown(self):
        self.tmp.cleanup()

    def start(self):
        self.world = c.initialise(self.root, 'court', self.case)
        self.runtime = s.Orchestrator.start(self.world, self.backend)
        return self.runtime

    def test_missing_personal_background_cannot_create_world(self):
        del self.case['roles']['W9']['background']
        with self.assertRaisesRegex(c.CourtError, 'W9.*background'):
            c.initialise(self.root, 'incomplete', self.case)
        self.assertFalse((self.root / 'worlds' / 'incomplete').exists())

    def test_legacy_underwritten_world_cannot_open_model_sessions(self):
        del self.case['roles']['W9']['background']
        with patch.object(c, 'validate_readiness', side_effect=c.validate):
            world = c.initialise(self.root, 'legacy', self.case)
        with self.assertRaisesRegex(c.CourtError, 'background'):
            s.Orchestrator.start(world, self.backend)
        self.assertEqual(list(self.backend.directory.glob('*.json')), [])

    def test_scaffold_placeholders_cannot_be_made_ready_by_clearing_draft(self):
        self.case['roles']['W9'] = builder.witness_scaffold('Witness nine')
        self.case['draft'] = False
        with self.assertRaisesRegex(c.CourtError, 'background'):
            c.validate_readiness(self.case)

    def test_validate_command_rejects_underwritten_case(self):
        del self.case['roles']['W9']['background']
        path = self.root / 'incomplete.json'
        path.write_bytes(c.encode(self.case))
        tool = Path(__file__).resolve().parents[1] / 'tools/courtroom_v2.py'
        result = subprocess.run([sys.executable, str(tool), 'validate', '--case', str(path)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('background', result.stderr)

    def test_missing_qualification_or_activity_details_fail_readiness(self):
        for field in ('training_and_qualifications', 'occupation', 'relationships', 'personal_stakes', 'life_history'):
            case = deepcopy(self.case)
            del case['roles']['W9']['background'][field]
            with self.subTest(field=field), self.assertRaises(c.CourtError):
                c.validate_readiness(case)
        for field in ('description', 'purpose', 'actions', 'tools_and_materials', 'authority', 'limits'):
            case = deepcopy(self.case)
            case['roles']['W9']['relevant_activities'][0][field] = ' '
            with self.subTest(field=field), self.assertRaises(c.CourtError):
                c.validate_readiness(case)

    def test_legacy_examples_are_not_advertised_as_playable(self):
        root = Path(__file__).resolve().parents[1]
        for name in ('last-light', 'second-signature'):
            case = c.load(root / 'modules/courtroom-v2/.sealed' / (name + '.json'))
            c.validate(case)  # Historical records remain readable.
            with self.subTest(name=name), self.assertRaisesRegex(c.CourtError, 'background'):
                c.validate_readiness(case)

    def test_personal_background_routes_only_to_its_witness_and_survives_rebuild(self):
        self.case['roles']['W9']['background']['life_history'] = 'W9_PRIVATE_BACKGROUND_581'
        self.case['roles']['WitnessX']['background']['life_history'] = 'WX_PRIVATE_BACKGROUND_274'
        r = self.start()
        for who, entry in r.state()['sessions'].items():
            history = json.dumps(self.backend.inspect(entry['session_id']))
            self.assertEqual('W9_PRIVATE_BACKGROUND_581' in history, who == 'W9')
            self.assertEqual('WX_PRIVATE_BACKGROUND_274' in history, who == 'WitnessX')
        self.backend.lose(r.state()['sessions']['W9']['session_id'])
        r = s.Orchestrator.start(self.world, self.backend)
        packet = self.backend.inspect(r.state()['sessions']['W9']['session_id'])[0]['packet']
        self.assertEqual(packet['role']['background'], self.case['roles']['W9']['background'])
        self.assertEqual(packet['role']['relevant_activities'], self.case['roles']['W9']['relevant_activities'])
        self.assertNotIn('WX_PRIVATE_BACKGROUND_274', json.dumps(packet))

    def test_conference_gap_pauses_without_fabricated_dialogue_or_private_leak(self):
        r = self.start()
        self.backend.queue('W9', {'text': '', 'data': {}, 'authoring_gap': 'PRIVATE_GAP_DETAIL_681'})
        with self.assertRaisesRegex(c.CourtError, 'authoring gap'):
            r.turn('W9', 'dialogue', ['player', 'W9'])
        events = c.read_events(self.world)
        self.assertEqual([e['type'] for e in events], ['gap'])
        self.assertEqual(events[0]['actor'], 'engine')
        self.assertEqual(events[0]['audience'], ['player'])
        self.assertNotIn('PRIVATE_GAP_DETAIL_681', json.dumps(r.player_packet()))
        self.assertTrue(c.replay(self.case, events)['paused'])
        self.assertEqual(r.state()['inflight'], [])
        self.backend.queue('W9', {'text': 'MUST_NOT_BE_CALLED', 'data': {}})
        r = s.Orchestrator.start(self.world, self.backend)
        with self.assertRaisesRegex(c.CourtError, 'paused'):
            r.turn('W9', 'dialogue', ['player', 'W9'])
        self.assertEqual(len(self.backend.scripts['W9']), 1)

    def test_examination_gap_never_becomes_an_answer(self):
        r = self.start()
        for phase in ('opening', 'evidence'):
            r.control(event('phase', to=phase))
        self.backend.queue('W9', {'text': '', 'data': {}, 'authoring_gap': 'Activity not authored.'})
        with self.assertRaisesRegex(c.CourtError, 'authoring gap'):
            r.examine('player', 'W9', 'What work did you do?')
        events = c.read_events(self.world)
        self.assertEqual(events[-2]['type'], 'exchange')
        self.assertEqual(events[-1]['type'], 'gap')
        self.assertFalse(any(e['type'] in {'answer', 'provisional_answer'} for e in events))
        for who in ('judge_merits', *c.jurors(self.case)):
            self.assertFalse(any(e['type'] == 'gap' for e in s.routed_packet(self.case, events, who)['events']))

    def test_genuine_authored_memory_limit_is_still_valid_testimony(self):
        r = self.start()
        self.backend.queue('W9', {'text': 'I remember counting the packs, not the background sounds.', 'data': {}})
        r.turn('W9', 'dialogue', ['player', 'W9'])
        self.assertFalse(c.replay(self.case, c.read_events(self.world))['paused'])

    def test_gap_must_not_be_mixed_with_testimony(self):
        r = self.start()
        self.backend.queue('W9', {'text': 'The documents do not say.', 'data': {}, 'authoring_gap': 'Missing activity.'})
        with self.assertRaises(c.CourtError):
            r.turn('W9', 'dialogue', ['player', 'W9'])
        self.assertEqual(c.read_events(self.world), [])

    def test_other_identity_cannot_use_witness_gap_protocol(self):
        r = self.start()
        self.backend.queue('opponent', {'text': '', 'data': {}, 'authoring_gap': 'Missing witness facts.'})
        with self.assertRaises(c.CourtError):
            r.turn('opponent', 'dialogue', ['player', 'opponent'])
        self.assertEqual(c.read_events(self.world), [])

    def test_gap_journal_commit_survives_interrupted_runtime_save(self):
        r = self.start()
        self.backend.queue('W9', {'text': '', 'data': {}, 'authoring_gap': 'PRIVATE_DETAIL_984'})
        with patch.object(r, '_finish', side_effect=OSError('interrupted after journal commit')):
            with self.assertRaises(OSError):
                r.turn('W9', 'dialogue', ['player', 'W9'])
        r = s.Orchestrator.start(self.world, self.backend)
        self.assertEqual([e['type'] for e in c.read_events(self.world)], ['gap'])
        self.assertTrue(c.replay(self.case, c.read_events(self.world))['paused'])
        self.assertEqual(r.state()['inflight'], [])
        self.assertNotIn('PRIVATE_DETAIL_984', json.dumps(r.player_packet()))


if __name__ == '__main__':
    unittest.main()
