"""Grounding checks catch confident invention after speech, without global truth."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_courtroom_v2 import fixture, event
import courtroom_v2 as c
import courtroom_sessions as s
from courtroom_backend import DeterministicBackend


class GroundingCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.case=fixture();self.world=c.initialise(self.root,'ground',self.case,allow_mock_rehearsal=True)
        self.backend=DeterministicBackend(self.root/'backend')
        self.runtime=s.Orchestrator.start(self.world,self.backend)

    def tearDown(self):self.tmp.cleanup()

    def answer(self, text='I counted paper packs.'):
        self.backend.queue('W9',{'text':text,'data':{}})
        return self.runtime.turn('W9','dialogue',['player','W9'])[-1]

    def grade(self, result='supported', refs=None):
        self.backend.queue('grounding_W9',{'text':'','data':{'result':result,
            'refs':['W9.relevant_activities.0.actions'] if refs is None else refs}})

    def test_player_command_uses_only_sources_available_before_answer(self):
        target=self.answer()
        self.runtime.human(event('private','player',['player'],text='PLAYER_THEORY_CANARY'))
        self.grade()
        self.runtime.human(event('dialogue','player',['player'],text='// ground '+target))
        checks=self.runtime.state()['technical_sessions']
        history=json.dumps(self.backend.inspect(checks[-1]['session_id']))
        for secret in ('AUTHOR_TRUTH_NEVER_EXPORT_563','OTHER_MEMORY_211','PLAYER_THEORY_CANARY','OPPONENT_ONLY_813'):
            self.assertNotIn(secret,history)
        self.assertNotIn('event:'+target,history)
        self.assertEqual(c.read_events(self.world)[-1]['data']['result'],'supported')

    def test_failed_check_preserves_original_and_rebuilds_affected_witness(self):
        before=self.runtime.state()['sessions']
        target=self.answer('INVENTED_PAST_978')
        self.grade('missing_coverage',[])
        self.runtime.ground(target)
        events=c.read_events(self.world)
        self.assertEqual(events[0]['text'],'INVENTED_PAST_978')
        self.assertIn(target,c.replay(self.case,events)['corrections'])
        self.assertTrue(c.replay(self.case,events)['paused'])
        after=self.runtime.state()['sessions']
        self.assertNotEqual(before['W9']['session_id'],after['W9']['session_id'])
        self.assertEqual(before['WitnessX']['session_id'],after['WitnessX']['session_id'])
        self.assertNotIn('INVENTED_PAST_978',json.dumps(self.backend.inspect(after['W9']['session_id'])))
        self.assertNotIn('grounding_check',[e['type'] for e in s.routed_packet(self.case,events,'W9')['events']])

    def test_sampling_checks_confident_answer_without_gap_signal(self):
        self.runtime.grounding_sample_rate=1.0
        self.grade('missing_coverage',[])
        self.answer('Confident unauthored detail.')
        self.assertTrue(c.replay(self.case,c.read_events(self.world))['paused'])
        self.assertEqual(self.runtime.state()['checks_pending'],[])

    def test_foreign_source_and_replacement_fact_rejected(self):
        target=self.answer();self.grade('supported',['WitnessX.knowledge.0'])
        with self.assertRaisesRegex(c.CourtError,'source'):self.runtime.ground(target)
        self.assertFalse(c.replay(self.case,c.read_events(self.world))['paused'])
        self.backend.queue('grounding_W9',{'text':'Invent a different historical detail.','data':{'result':'supported','refs':['W9.knowledge.0']}})
        with self.assertRaises(c.CourtError):self.runtime.ground(target)

    def test_sample_survives_restart_when_checker_is_temporarily_unavailable(self):
        self.runtime.grounding_sample_rate=1
        with self.assertRaises(c.CourtError):self.answer('A confident claim.')
        self.assertEqual(self.runtime.state()['checks_pending'],['T0001'])
        with self.assertRaisesRegex(c.CourtError,'sampled grounding'):
            self.answer('Must not bypass outstanding check.')
        self.grade()
        resumed=s.Orchestrator.start(self.world,self.backend)
        self.assertEqual(resumed.state()['checks_pending'],[])
        self.assertEqual(c.read_events(self.world)[-1]['data']['result'],'supported')

    def test_court_answer_correction_removes_embedded_answer_and_dependent_contexts(self):
        for phase in ('opening','evidence'):self.runtime.control(event('phase',to=phase))
        before=self.runtime.state()['sessions']
        self.backend.queue('W9',{'text':'INVENTED_TESTIMONY_642','data':{}})
        ids=self.runtime.examine('player','W9','What did you personally do?')
        self.grade('missing_coverage',[])
        self.runtime.ground(ids[-1])
        events=c.read_events(self.world)
        after=self.runtime.state()['sessions']
        for who in ('W9','opponent','judge_admissibility','judge_merits'):
            self.assertNotEqual(before[who]['session_id'],after[who]['session_id'])
            history=json.dumps(self.backend.inspect(after[who]['session_id']))
            self.assertNotIn('INVENTED_TESTIMONY_642',history)
            self.assertNotIn('grounding_quarantine',history)
            self.assertNotIn('simulation could not ground',history)
        self.assertNotIn('INVENTED_TESTIMONY_642',json.dumps(s.routed_packet(self.case,events,'judge_merits')))
        self.assertIn('INVENTED_TESTIMONY_642',json.dumps(events))

    def test_withdrawn_answer_cannot_justify_its_own_repair(self):
        target=self.answer('Invented history.');self.grade('missing_coverage',[]);self.runtime.ground(target)
        fault=c.read_events(self.world)[-1]['id']
        with self.assertRaisesRegex(c.CourtError,'permitted sources'):
            self.runtime.control(event('repair',audience=['player'],resolution={
                'kind':'supported_resolution','fault':fault,'witness':'W9','refs':['event:'+target]}))
        self.assertTrue(c.replay(self.case,c.read_events(self.world))['paused'])

    def test_uncertainty_check_requires_an_owned_boundary_reference(self):
        target=self.answer('I cannot recall the sounds.')
        self.grade('supported_uncertainty',['W9.memory'])
        with self.assertRaisesRegex(c.CourtError,'boundary'):self.runtime.ground(target)
        self.grade('supported_uncertainty',['boundary:W9:sounds'])
        self.runtime.ground(target)
        self.assertFalse(c.replay(self.case,c.read_events(self.world))['paused'])

    def test_private_answer_unavailable_to_player_control(self):
        self.backend.queue('WitnessX',{'text':'PRIVATE_WX_ANSWER','data':{}})
        target=self.runtime.turn('WitnessX','dialogue',['WitnessX','opponent'])[-1]
        with self.assertRaisesRegex(c.CourtError,'heard'):self.runtime.ground(target)


if __name__=='__main__':unittest.main()
