"""Explicit revised continuation; blinded candidate creation and sealed selection."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_courtroom_v2 import fixture, event
from coverage_fixture import certify
import courtroom_v2 as c
import courtroom_sessions as s
from courtroom_backend import DeterministicBackend


class AmendmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.case=fixture()
        self.case['amendment_envelopes']={'shelf_label':{'target_layer':'witness','entry':'W9','topic':'The label attached to the paper shelf.',
            'constraints':['A plain inventory label; no person name, date or time.'], 'refs':['W9.relevant_activities.0.actions']}}
        self.case['roles']['WitnessX']['knowledge'].append('OTHER_WITNESS_LABEL_TRUTH: the label was on the upper shelf.')
        self.case['amendment_consistency']={'shelf_label':{
            'W9':['W9.relevant_activities.0.actions'], 'WitnessX':['WitnessX.knowledge.1']}}
        certify(self.case)
        self.world=c.initialise(self.root,'amended',self.case,allow_mock_rehearsal=True)
        self.backend=DeterministicBackend(self.root/'sessions');self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.runtime.amendment_max_attempts=1
        self.runtime.human(event('private','player',['player'],text='SECRET_PLAYER_THEORY'))
        self.backend.queue('W9',{'text':'','data':{},'authoring_gap':'QUESTION_DIRECTION_SECRET'})
        with self.assertRaises(c.CourtError):self.runtime.turn('W9','dialogue',['player','W9'])

    def tearDown(self):self.tmp.cleanup()

    def candidates(self, consistent=True):
        for number,word in enumerate(('PAPER_CANARY','STOCK_CANARY','SUPPLIES_CANARY'),1):
            self.backend.queue(f'amendment_author_{number}_witness_W9',{'text':'','data':{
                'candidate':{'addition':'The shelf label read '+word+'.'}}})
        self.backend.queue('amendment_checker_witness_W9',{'text':'','data':{'checks':[
            {'consistent':value,'reason':'Synthetic consistency decision.'} for value in (consistent,True,True)]}})

    def rehearsal(self, case, backend, **kwargs):
        return certify(deepcopy(case))['coverage_rehearsal']

    def test_unsupported_substrate_layer_fails_closed(self):
        import courtroom_amendments as a
        with self.assertRaisesRegex(c.CourtError,'Unsupported amendment layer'):
            a.apply_entry(self.case,'space','west-room',{'addition':'A new doorway.'})
        changed=a.apply_entry(self.case,'witness','W9',{'addition':'A committed new personal detail.'})
        self.assertIn('A committed new personal detail.',changed['roles']['W9']['knowledge'])
        self.assertNotIn('A committed new personal detail.',self.case['roles']['W9']['knowledge'])

    def test_strict_play_and_missing_topic_refuse_before_author_call(self):
        with self.assertRaisesRegex(c.CourtError,'explicit'):self.runtime.amend('shelf_label')
        with self.assertRaisesRegex(c.CourtError,'precommitted'):self.runtime.amend('unprepared',confirmed=True)
        self.assertEqual(self.runtime.state()['technical_sessions'],[])
        self.assertEqual(c.replay(self.case,c.read_events(self.world))['history_mode'],'strict')

    def test_fresh_author_is_blind_and_random_selection_preserves_original_commitment(self):
        original=(self.world/c.AREA/'case.json').read_bytes()
        before=self.runtime.state()['sessions']
        self.candidates()
        with patch('courtroom_rehearsal.rehearse',side_effect=self.rehearsal), patch('secrets.randbelow',return_value=1):
            self.runtime.amend('shelf_label',confirmed=True)
        self.assertEqual((self.world/c.AREA/'case.json').read_bytes(),original)
        events=c.read_events(self.world);state=c.replay(self.case,events)
        self.assertEqual(state['history_mode'],'amended')
        self.assertFalse(state['paused'])
        effective=c.effective_case(self.case,events)
        self.assertIn('The shelf label read STOCK_CANARY.',effective['roles']['W9']['knowledge'])
        self.assertNotIn('PAPER_CANARY',json.dumps(s.routed_packet(self.case,events,'W9')))
        self.assertNotIn('STOCK_CANARY',json.dumps(s.routed_packet(self.case,events,'judge_merits')))
        player=json.dumps(self.runtime.player_packet())
        for value in ('PAPER_CANARY','STOCK_CANARY','SUPPLIES_CANARY'):self.assertNotIn(value,player)
        for name in ('private-record.md','transcript.md'):
            record=(self.world/c.PUBLIC/name).read_text()
            for value in ('PAPER_CANARY','STOCK_CANARY','SUPPLIES_CANARY'):self.assertNotIn(value,record)
        after=self.runtime.state()['sessions']
        self.assertNotEqual(before['W9']['session_id'],after['W9']['session_id'])
        self.assertEqual(before['WitnessX']['session_id'],after['WitnessX']['session_id'])
        audit=self.runtime.state()['technical_audit'][0]
        source=json.dumps({'packet':audit['packet'],'request':audit['request']})
        for value in ('SECRET_PLAYER_THEORY','QUESTION_DIRECTION_SECRET','player_side','AUTHOR_TRUTH_NEVER_EXPORT_563'):
            self.assertNotIn(value,source)
        restarted=s.Orchestrator.start(self.world,self.backend)
        self.assertIn('STOCK_CANARY',json.dumps(self.backend.inspect(restarted.state()['sessions']['W9']['session_id'])))

    def test_failed_rehearsal_cannot_commit_selected_addition(self):
        self.candidates()
        def failed(case, backend, **kwargs):
            report=self.rehearsal(case,backend)
            row=report['witnesses']['W9']['answers'][0];row['answer']=''
            for grade in row['assessments'].values():grade.update(bin='gap',refs=[])
            __import__('courtroom_rehearsal').seal_report(report)
            return report
        with patch('courtroom_rehearsal.rehearse',side_effect=failed),self.assertRaises(c.CourtError):
            self.runtime.amend('shelf_label',confirmed=True)
        events=c.read_events(self.world)
        self.assertFalse(any(e['type']=='amendment' for e in events))
        self.assertTrue(c.replay(self.case,events)['paused'])
        self.assertEqual(c.effective_case(self.case,events)['roles']['W9']['knowledge'],self.case['roles']['W9']['knowledge'])

    def test_revision_receipt_cannot_change_parent_or_selection_after_recording(self):
        self.candidates()
        with patch('courtroom_rehearsal.rehearse',side_effect=self.rehearsal):
            self.runtime.amend('shelf_label',confirmed=True)
        events=c.read_events(self.world)
        for field,value in (('parent','wrong-parent'),('selected',7),('attempt_count',0),('attempt_limit',0)):
            altered=deepcopy(events)
            altered[-1]['private_note']['amendment'][field]=value
            with self.subTest(field=field),self.assertRaises(c.CourtError):c.replay(self.case,altered)

    def test_inconsistent_set_cannot_be_cherry_picked_or_applied(self):
        self.candidates(False)
        with self.assertRaisesRegex(c.CourtError,'consistent'):
            self.runtime.amend('shelf_label',confirmed=True)
        self.assertTrue(c.replay(self.case,c.read_events(self.world))['paused'])
        self.assertEqual(c.effective_case(self.case,c.read_events(self.world))['roles']['W9']['knowledge'],self.case['roles']['W9']['knowledge'])

    def test_retry_uses_fresh_authors_with_identical_blinded_inputs_and_records_attempts(self):
        self.runtime.amendment_max_attempts=2
        self.candidates(False);self.candidates(True)
        with patch('courtroom_rehearsal.rehearse',side_effect=self.rehearsal),patch('secrets.randbelow',return_value=0) as choose:
            self.runtime.amend('shelf_label',confirmed=True)
        choose.assert_called_once_with(3)
        state=self.runtime.state();authors=[a for a in state['technical_audit'] if 'amendment_author_' in a['request']['identity']]
        self.assertEqual(len(authors),6)
        self.assertEqual(len({a['session_id'] for a in authors}),6)
        self.assertTrue(all(a['packet']==authors[0]['packet'] for a in authors))
        for a in authors:
            self.assertEqual(a['request']['task'],{'produce':1})
            self.assertNotIn('OTHER_WITNESS_LABEL_TRUTH',json.dumps(a['packet']))
            self.assertTrue(c.load(self.backend._path(a['session_id']))['closed'])
        receipt=c.read_events(self.world)[-1]['private_note']['amendment']
        self.assertEqual(receipt['attempt_count'],2)
        self.assertEqual([a['status'] for a in receipt['attempts']],['rejected','accepted'])
        self.assertEqual(receipt['attempt_limit'],2)

    def test_checker_gets_scoped_other_witness_truth_and_no_other_session_does(self):
        self.candidates()
        with patch('courtroom_rehearsal.rehearse',side_effect=self.rehearsal):self.runtime.amend('shelf_label',confirmed=True)
        audits=self.runtime.state()['technical_audit']
        checker=next(a for a in audits if a['request']['identity']=='amendment_checker_witness_W9')
        encoded=json.dumps(checker['packet'])
        self.assertIn('OTHER_WITNESS_LABEL_TRUTH',encoded)
        for secret in ('OTHER_MEMORY_211','AUTHOR_TRUTH_NEVER_EXPORT_563','SECRET_PLAYER_THEORY','QUESTION_DIRECTION_SECRET'):
            self.assertNotIn(secret,encoded)
        for a in audits:
            if a is not checker:self.assertNotIn('OTHER_WITNESS_LABEL_TRUTH',json.dumps(a['packet']))
        self.assertNotIn('OTHER_WITNESS_LABEL_TRUTH',json.dumps(s.routed_packet(self.case,c.read_events(self.world),'W9')))
        self.assertTrue(c.load(self.backend._path(checker['session_id']))['closed'])

    def test_missing_cross_witness_scope_blocks_commitment(self):
        case=deepcopy(self.case);case['amendment_consistency']['shelf_label'].pop('WitnessX')
        certify(case)
        with self.assertRaisesRegex(c.CourtError,'consistency scope'):c.validate_readiness(case)

    def test_failed_sets_stop_at_cap_and_remain_sealed_and_paused(self):
        self.runtime.amendment_max_attempts=2
        self.candidates(False);self.candidates(False)
        with patch('secrets.randbelow') as choose,self.assertRaisesRegex(c.CourtError,'2 attempts'):
            self.runtime.amend('shelf_label',confirmed=True)
        choose.assert_not_called()
        state=self.runtime.state();self.assertEqual(state['amendment_attempts'][-1]['attempt_count'],2)
        self.assertEqual(state['amendment_attempts'][-1]['status'],'exhausted')
        events=c.read_events(self.world)
        self.assertFalse(any(e['type']=='amendment' for e in events))
        self.assertTrue(c.replay(self.case,events)['paused'])
        self.assertNotIn('OTHER_WITNESS_LABEL_TRUTH',json.dumps(self.runtime.player_packet()))

    def test_duplicate_completions_retry_as_a_whole_set(self):
        self.runtime.amendment_max_attempts=2
        for number in range(1,4):
            self.backend.queue(f'amendment_author_{number}_witness_W9',{'text':'','data':{
                'candidate':{'addition':'The same completion from every independent author.'}}})
        self.candidates(True)
        with patch('courtroom_rehearsal.rehearse',side_effect=self.rehearsal):self.runtime.amend('shelf_label',confirmed=True)
        receipt=c.read_events(self.world)[-1]['private_note']['amendment']
        self.assertEqual(receipt['attempt_count'],2)
        self.assertNotIn('checker',receipt['attempts'][0])
        self.assertEqual(receipt['attempts'][0]['status'],'rejected')

    def test_cross_witness_source_cannot_be_misattributed(self):
        import courtroom_amendments as a
        case=deepcopy(self.case)
        case['amendment_consistency']['shelf_label']['W9'].append('WitnessX.knowledge.1')
        with self.assertRaisesRegex(c.CourtError,'consistency source'):
            a.context(case,case['amendment_envelopes']['shelf_label'],'shelf_label')

    def test_receipt_cannot_reuse_an_author_session_between_attempts(self):
        self.runtime.amendment_max_attempts=2
        self.candidates(False);self.candidates(True)
        with patch('courtroom_rehearsal.rehearse',side_effect=self.rehearsal):self.runtime.amend('shelf_label',confirmed=True)
        events=c.read_events(self.world);receipt=events[-1]['private_note']['amendment']
        receipt['attempts'][1]['authors'][0]=deepcopy(receipt['attempts'][0]['authors'][0])
        events[-1]['data']['revision']=c.digest(c.encode(receipt))
        with self.assertRaisesRegex(c.CourtError,'fresh independent'):c.replay(self.case,events)


if __name__=='__main__':unittest.main()
