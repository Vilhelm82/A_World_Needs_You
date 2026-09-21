"""Storage and state-machine tests, not a claim of passing live-model roleplay."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import courtroom_v2 as c
import courtroom_cases as builder


def fixture(kind='criminal', forum='jury', side=None, style='us-drama', pace='drama', n=3, threshold=None):
    case = builder.skeleton(kind)
    case.update(draft=False, case_id='test-case', title='Artificial controller fixture',
        public_summary='An allegation, not evidence.', brief='COUNSEL_ONLY_BRIEF_729',
        truth='AUTHOR_TRUTH_NEVER_EXPORT_563', opening='A test opening.')
    case['roles'] = {
        'player': {'name':'Will','kind':'counsel','knowledge':['PRIVATE_CLIENT_MARKER_819'],'documents':['E1','E2']},
        'opponent': {'name':'Other counsel','kind':'counsel','knowledge':['OPPONENT_ONLY_813'],'documents':['E1','E2']},
        'bench': {'name':'Judge','kind':'bench','knowledge':[],'documents':[]},
        'S1': {'name':'Solicitor','kind':'support','knowledge':['CLIENT_SUPPORT_632'],'documents':['E1']},
        'W9': {'name':'Witness nine','kind':'witness','knowledge':['OWN_MEMORY_679'],'documents':['E1'], 'knowledge_basis':'Direct observation, limited to fixed fixture.'},
        'WitnessX': {'name':'Other witness','kind':'witness','knowledge':['OTHER_MEMORY_211'],'documents':[], 'knowledge_basis':'Separate fixed observation.'}}
    case['documents'] = {
        'E1': {'title':'Agreed item','text':'ADMITTED_CONTENT_761','provenance':'Fixture stipulation.','status':'admitted','uses':['truth']},
        'E2': {'title':'Contested item','text':'EXCLUDED_CONTENT_301','provenance':'Fixture proposed document.','status':'disclosed','uses':[]}}
    party = 'prosecution' if kind == 'criminal' else 'claimant'
    standard = 'beyond_reasonable_doubt' if kind == 'criminal' else 'balance_of_probabilities'
    case['issues'] = {k:{'text':'Artificial issue '+k,'party':party,'standard':standard} for k in ['I1','I2']}
    case['counts'] = {'C1':{'label':'Artificial charge/claim','elements':['I1','I2'],'bars':[]}}
    if kind == 'civil': case['counts']['C1']['remedy']={'currency':'test units','maximum':100}
    case = builder.configure(case,style,forum,side,pace,n,threshold)
    return c.validate(case)


def event(kind, actor='engine', audience=None, text='Artificial test event.', **data):
    return dict(type=kind, actor=actor, audience=sorted(c.CORE) if audience is None else audience,text=text,data=data)


class CourtroomV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.case = fixture()
        self.world = c.initialise(self.root,'test-court',self.case)
    def tearDown(self): self.tmp.cleanup()
    def add(self, e): return c.record(self.world,e)
    def state(self): return c.replay(c.read_case(self.world),c.read_events(self.world))
    def audience(self, witness=None, jury=True):
        a = set(c.CORE)
        if jury: a |= c.jurors(self.case)
        if witness: a.add(witness)
        return sorted(a)
    def go(self, phase):
        route=['conference','opening','evidence','closing','decision','closed']
        current = self.state()['phase']
        for nxt in route[route.index(current)+1:route.index(phase)+1]:
            if nxt == 'decision' and c.jurors(self.case):
                self.add(event('directions','bench',self.audience(),rule='R1'))
            self.add(event('phase',to=nxt))
    def publish(self,k='E1'):
        self.go('evidence'); self.add(event('publish','bench',self.audience(),document=k))
    def ask(self,actor='opponent',answer='TEST_ANSWER_439'):
        self.go('evidence')
        return self.add(event('exchange',actor,self.audience('W9'),witness='W9',question='Exact test question?',answer=answer))[0]
    def settled(self):
        q=self.ask();self.add(event('accept','player'));return q
    def offer(self,k='E2'):
        self.go('evidence')
        self.add(event('disclose','player',sorted(c.CORE),document=k,to='bench'))
    def admit(self,k='E2',uses=None):
        self.offer(k)
        return self.add(event('ruling','bench',effect='document',document=k,status='admitted' if uses is None else 'limited',uses=['truth'] if uses is None else uses,rule='R5'))
    def findings(self,proved=False,ref='E1'):
        return {k:dict(status='proved' if proved else 'not_proved',reason='Artificial finding for plumbing test, not a case assessment.',refs=[{'id':ref,'use':'truth'}] if proved else []) for k in self.case['issues']}
    def ballot(self,j,proved=False):
        self.add(event('ballot',j,[j],findings=self.findings(proved)))
    def verdict(self,positive=False):
        self.publish();self.go('decision')
        for j in sorted(c.jurors(self.case)):self.ballot(j,positive)
        outcomes=c.aggregate(self.case,self.state()['ballots'])
        return self.add(event('verdict','foreperson',self.audience(),outcomes=outcomes))
    def bench_world(self,kind='criminal'):
        self.case=fixture(kind,'bench');self.world=c.initialise(self.root,'bench-case',self.case)

    def test_full_configuration_matrix(self):
        # 48 independent combinations; forum does not imply civil or local law.
        n=0
        for kind in ('criminal','civil'):
            for forum in ('bench','jury'):
                for style in ('us-drama','nsw-drama','custom'):
                    for side in sorted(c.SIDES[kind]):
                        for pace in ('drama','deliberate'):
                            with self.subTest(kind=kind,forum=forum,style=style,side=side,pace=pace):
                                case=fixture(kind,forum,side,style,pace)
                                w=c.initialise(self.root,f'matrix-{n}',case);n+=1
                                self.assertEqual(c.verify(w)['status'],'PASS')
                                self.assertEqual(c.read_case(w)['config']['player_side'],side)
        self.assertEqual(n,48)
    def test_both_complete_starters_in_both_forums_and_sides(self):
        for file in (ROOT/'modules/courtroom-v2/.sealed').glob('*.json'):
            source=c.load(file);kind=source['config']['case_type']
            for forum in ('bench','jury'):
                for side in sorted(c.SIDES[kind]):
                    for style in ('us-drama','nsw-drama'):
                        with self.subTest(file=file.name,forum=forum,side=side,style=style):
                            c.validate(builder.configure(source,style,forum,side))
    def test_new_scaffold_is_not_falsely_playable(self):
        with self.assertRaises(c.CourtError):c.validate(builder.configure(builder.skeleton('criminal')))
    def test_unlimited_witness_ids_not_four_hardcoded(self):
        self.assertIn('WitnessX',self.case['roles']);self.assertIn('W9',self.case['roles'])
    def test_invalid_side_rejected(self):
        x=deepcopy(self.case);x['config']['player_side']='claimant'
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_prosecution_burden_not_shifted(self):
        x=deepcopy(self.case);x['issues']['I1']['party']='defence'
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_criminal_burden_not_civil(self):
        x=deepcopy(self.case);x['issues']['I1']['standard']='balance_of_probabilities'
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_bar_needs_responding_party(self):
        x=deepcopy(self.case);x['counts']['C1']['elements']=['I1'];x['counts']['C1']['bars']=['I2']
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_explicit_affirmative_defence_bar(self):
        x=deepcopy(self.case);x['counts']['C1']['elements']=['I1'];x['counts']['C1']['bars']=['I2'];x['issues']['I2'].update(party='defence',standard='balance_of_probabilities');c.validate(x)
        self.assertEqual(c.result_for(x,self.findings(True))['C1'],'not_guilty')
    def test_jury_threshold_cannot_be_both_outcomes(self):
        x=deepcopy(self.case);x['config']['verdict_threshold']=1
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_jury_size_matches_people(self):
        x=deepcopy(self.case);x['config']['jury_size']=12
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_bool_not_jury_size(self):
        x=deepcopy(self.case);x['config']['jury_size']=True
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_unknown_issue_rejected(self):
        x=deepcopy(self.case);x['counts']['C1']['elements'].append('MISSING')
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_factfinder_private_knowledge_rejected(self):
        for r in ['bench','J01']:
            x=deepcopy(self.case);x['roles'][r]['knowledge']=['secret']
            with self.assertRaises(c.CourtError):c.validate(x)
    def test_pre_admitted_must_be_disclosed(self):
        x=deepcopy(self.case);x['roles']['opponent']['documents']=[]
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_no_real_law_fidelity_claim(self):
        x=deepcopy(self.case);x['law_status']='verified-complete-NSW-law'
        with self.assertRaises(c.CourtError):c.validate(x)
    def test_draft_historical_commitment(self):
        self.assertEqual(c.verify(self.world)['status'],'PASS')
        before=(self.world/c.AREA/'case.json').read_bytes()
        self.add(event('private','player',['player'],text='A forceful new theory'))
        self.assertEqual(before,(self.world/c.AREA/'case.json').read_bytes())
    def test_init_never_overwrites(self):
        with self.assertRaises(c.CourtError):c.initialise(self.root,'test-court',self.case)
    def test_legacy_world_not_overwritten(self):
        w=self.root/'worlds/legacy';w.mkdir();(w/'keep').write_text('unchanged')
        with self.assertRaises(c.CourtError):c.initialise(self.root,'legacy',self.case)
        self.assertEqual((w/'keep').read_text(),'unchanged')
    def test_path_traversal_and_symlink_rejected(self):
        for name in ('../oops','/tmp/foo','a/b','Upper',''):
            with self.assertRaises(c.CourtError):c.world_path(self.root,name)
        (self.root/'worlds/link').symlink_to(self.world)
        with self.assertRaises(c.CourtError):c.world_path(self.root,'link')
    def test_managed_symlink_rejected(self):
        p=self.world/c.AREA/'case.json';saved=p.read_bytes();p.unlink()
        target=self.root/'elsewhere';target.write_bytes(saved);p.symlink_to(target)
        with self.assertRaises(c.CourtError):c.verify(self.world)
    def test_case_changes_detected(self):
        p=self.world/c.AREA/'case.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(c.CourtError):c.verify(self.world)
    def test_record_changes_detected(self):
        self.add(event('private','player',['player'],text='ORIGINAL_MARKER'))
        p=self.world/c.AREA/'events.jsonl';p.write_text(p.read_text().replace('ORIGINAL_MARKER','ALTERED_MARKER'))
        with self.assertRaises(c.CourtError):c.verify(self.world)
    def test_charter_presentation_mutable(self):
        p=self.world/'charter.md';p.write_text(p.read_text()+'\nShorter narration.\n')
        self.assertEqual(c.verify(self.world)['status'],'PASS')
    def test_packet_does_not_export_author_truth(self):
        for r in self.case['roles']:
            self.assertNotIn('AUTHOR_TRUTH_NEVER_EXPORT_563',json.dumps(c.packet(self.world,r)))
    def test_private_strategy_not_exported(self):
        self.add(event('private','player',['player'],text='PRIVATE_THEORY_975'))
        for r in self.case['roles'].keys()-{'player'}:
            self.assertNotIn('PRIVATE_THEORY_975',json.dumps(c.packet(self.world,r)))
    def test_private_note_not_exported(self):
        e=event('private','player',['player']);e['private_note']='AUTHOR_ONLY_391';self.add(e)
        for r in self.case['roles']:
            self.assertNotIn('AUTHOR_ONLY_391',json.dumps(c.packet(self.world,r)))
    def test_counsel_brief_not_given_to_judge_jury_or_witness(self):
        for r in ('bench','J01','W9','WitnessX'):
            self.assertNotIn('COUNSEL_ONLY_BRIEF_729',json.dumps(c.packet(self.world,r)))
    def test_client_instructions_not_leaked(self):
        for r in self.case['roles'].keys()-{'player'}:
            self.assertNotIn('PRIVATE_CLIENT_MARKER_819',json.dumps(c.packet(self.world,r)))
    def test_pending_answer_not_leaked_to_absent_witness(self):
        self.ask()
        self.assertNotIn('TEST_ANSWER_439',json.dumps(c.packet(self.world,'WitnessX')))
    def test_unpublished_exhibit_absent_from_jury(self):
        self.assertNotIn('ADMITTED_CONTENT_761',json.dumps(c.packet(self.world,'J01')))
        self.assertIn('ADMITTED_CONTENT_761',json.dumps(c.packet(self.world,'bench',True)))
    def test_publish_admitted_document_to_jury(self):
        self.publish()
        self.assertIn('ADMITTED_CONTENT_761',json.dumps(c.packet(self.world,'J01')))
    def test_cannot_publish_unadmitted_document(self):
        self.go('evidence')
        with self.assertRaises(c.CourtError):self.add(event('publish','player',self.audience(),document='E2'))
    def test_bench_can_inspect_offered_not_merits(self):
        self.offer()
        self.assertIn('EXCLUDED_CONTENT_301',json.dumps(c.packet(self.world,'bench')))
        self.assertNotIn('EXCLUDED_CONTENT_301',json.dumps(c.packet(self.world,'bench',True)))
        self.assertNotIn('EXCLUDED_CONTENT_301',json.dumps(c.packet(self.world,'J01')))
    def test_excluded_document_removed_after_publication(self):
        self.admit();self.publish('E2')
        self.add(event('ruling','bench',effect='document',document='E2',status='excluded',uses=[],rule='R5'))
        self.assertNotIn('EXCLUDED_CONTENT_301',json.dumps(c.packet(self.world,'J01')))
    def test_changed_limited_use_requires_republication(self):
        self.admit();self.publish('E2')
        self.add(event('ruling','bench',effect='document',document='E2',status='limited',uses=['notice'],rule='R5'))
        self.assertNotIn('E2',c.packet(self.world,'J01')['documents'])
        self.publish('E2');self.assertEqual(c.packet(self.world,'J01')['documents']['E2']['uses'],['notice'])
    def test_limited_use_not_truth(self):
        self.admit(uses=['notice']);self.publish('E2');self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('ballot','J01',['J01'],findings=self.findings(True,'E2')))
    def test_no_direct_disclosure_to_juror(self):
        with self.assertRaises(c.CourtError):self.add(event('disclose','player',['player','J01'],document='E2',to='J01'))
    def test_no_automatic_opponent_knowledge(self):
        self.add(event('dialogue','W9',['player','W9'],text='PRIVATE_INTERVIEW_286'))
        self.assertNotIn('PRIVATE_INTERVIEW_286',json.dumps(c.packet(self.world,'opponent')))
    def test_flow_answer_provisional_until_opportunity_closes(self):
        q=self.ask()
        self.assertNotIn('TEST_ANSWER_439',json.dumps(c.packet(self.world,'J01')))
        self.add(event('accept','player'))
        self.assertIn('TEST_ANSWER_439',json.dumps(c.packet(self.world,'J01')))
    def test_flow_has_immediate_next_turn_objection(self):
        q=self.ask();self.add(event('objection','player',self.audience(),rule='R4'))
        self.add(event('ruling','bench',self.audience(),effect='objection',result='sustained',rule='R4'))
        self.assertIn(q,self.state()['struck'])
        self.assertNotIn('TEST_ANSWER_439',json.dumps(c.packet(self.world,'J01')))
        self.assertIn('TEST_ANSWER_439',(self.world/c.PUBLIC/'transcript.md').read_text())
    def test_overrule_preserves_actual_answer(self):
        self.ask();self.add(event('objection','player',rule='R4'))
        self.add(event('reply','opponent',rule='R4'))
        self.add(event('ruling','bench',effect='objection',result='overruled',rule='R4'))
        self.assertIsNone(self.state()['pending'])
        self.assertIn('TEST_ANSWER_439',json.dumps(c.packet(self.world,'J01')))
    def test_no_second_question_before_objection_opportunity(self):
        self.ask()
        with self.assertRaises(c.CourtError):self.ask()
    def test_player_questions_have_equal_opponent_opportunity(self):
        self.ask('player');self.add(event('objection','opponent',rule='R4'))
        self.assertTrue(self.state()['pending']['objected'])
    def test_strict_stops_before_answer(self):
        self.add(event('cadence',mode='strict'))
        with self.assertRaises(c.CourtError):self.ask()
        q=self.ask(answer=None)
        with self.assertRaises(c.CourtError):self.add(event('answer','W9',self.audience('W9'),text='too soon'))
        self.add(event('accept','player'));self.add(event('answer','W9',self.audience('W9'),text='STRICT_EXACT_728'))
        self.assertIn('STRICT_EXACT_728',json.dumps(c.packet(self.world,'J01')))
        self.assertIn(q,self.state()['answers'])
    def test_wrong_witness_cannot_answer(self):
        self.ask(answer=None);self.add(event('accept','player'))
        with self.assertRaises(c.CourtError):self.add(event('answer','WitnessX',self.audience('W9')))
    def test_jury_absence_blocks_evidence_leak(self):
        self.go('evidence');self.add(event('jury_presence','bench',present=False))
        with self.assertRaises(c.CourtError):self.ask()
        q=self.add(event('exchange','opponent',self.audience('W9',False),witness='W9',question='Sidebar?',answer='SIDEBAR_FACT_635'))[0]
        self.add(event('accept','player'))
        self.assertNotIn('SIDEBAR_FACT_635',json.dumps(c.packet(self.world,'J01')))
        self.assertIn('SIDEBAR_FACT_635',json.dumps(c.packet(self.world,'bench',True)))
    def test_cannot_silently_omit_seated_jury(self):
        self.go('evidence')
        with self.assertRaises(c.CourtError):self.add(event('exchange','opponent',self.audience('W9',False),witness='W9',question='Q?',answer='A'))
    def test_jury_receives_equal_material(self):
        self.go('evidence')
        with self.assertRaises(c.CourtError):self.add(event('exchange','opponent',sorted(c.CORE|{'W9','J01'}),witness='W9',question='Q?',answer='A'))
    def test_no_unilateral_stipulation(self):
        self.go('evidence')
        with self.assertRaises(c.CourtError):self.add(event('stipulation','player',self.audience(),agreed_by=['player']))
    def test_no_invented_objection_rule(self):
        self.ask()
        with self.assertRaises(c.CourtError):self.add(event('objection','player',rule='MADEUP'))
    def test_unknown_exhibit_rejected(self):
        with self.assertRaises(c.CourtError):self.offer('GHOST')
    def test_jury_directions_required(self):
        self.go('closing')
        with self.assertRaises(c.CourtError):self.add(event('phase',to='decision'))
    def test_sealed_ballots_not_exported_to_counsel_or_bench(self):
        self.publish();self.go('decision')
        f=self.findings();f['I1']['reason']='PRIVATE_BALLOT_REASON_542'
        self.add(event('ballot','J01',['J01'],findings=f))
        for r in ['player','opponent','bench','J02','W9']:
            self.assertNotIn('PRIVATE_BALLOT_REASON_542',json.dumps(c.packet(self.world,r)))
        self.assertIn('PRIVATE_BALLOT_REASON_542',json.dumps(c.packet(self.world,'J01')))
    def test_deliberation_is_not_public(self):
        self.publish();self.go('decision')
        self.add(event('deliberation','J01',sorted(c.jurors(self.case)),text='SEALED_DELIBERATION_842',refs=[]))
        for r in ['player','opponent','bench']:
            self.assertNotIn('SEALED_DELIBERATION_842',json.dumps(c.packet(self.world,r)))
        self.assertNotIn('SEALED_DELIBERATION_842',(self.world/c.PUBLIC/'transcript.md').read_text())
    def test_deliberation_cannot_include_bench(self):
        self.publish();self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('deliberation','J01',sorted(c.jurors(self.case)|{'bench'}),refs=[]))
    def test_judge_cannot_choose_jury_verdict(self):
        self.publish();self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('verdict','bench',self.audience(),outcomes={'C1':'guilty'},findings=self.findings(True)))
    def test_acquittal_is_valid_without_defence_proving_innocence(self):
        self.verdict(False)
        self.assertEqual(self.state()['verdict']['outcomes'],{'C1':'not_guilty'})
    def test_conviction_requires_each_element(self):
        self.publish();self.go('decision')
        for j in sorted(c.jurors(self.case)):
            f=self.findings(True);f['I2']=self.findings(False)['I2'];self.add(event('ballot',j,[j],findings=f))
        self.assertEqual(c.aggregate(self.case,self.state()['ballots']),{'C1':'not_guilty'})
    def test_unanimous_conviction(self):
        self.verdict(True);self.assertEqual(self.state()['verdict']['outcomes']['C1'],'guilty')
    def test_verdict_cannot_change_after_return(self):
        self.verdict(False)
        with self.assertRaises(c.CourtError):self.ballot('J01',True)
    def test_split_first_ballot_not_forced_hung(self):
        self.publish();self.go('decision')
        for j in sorted(c.jurors(self.case)):self.ballot(j,j=='J01')
        with self.assertRaises(c.CourtError):self.add(event('verdict','foreperson',self.audience(),outcomes={'C1':'hung'}))
        with self.assertRaises(c.CourtError):self.add(event('deadlock','foreperson',self.audience(),counts=['C1']))
    def test_genuine_hung_outcome_after_deliberation(self):
        self.publish();self.go('decision')
        self.add(event('deliberation','J01',sorted(c.jurors(self.case)),refs=[]))
        for j in sorted(c.jurors(self.case)):self.ballot(j,j=='J01')
        self.add(event('deadlock','foreperson',self.audience(),counts=['C1']))
        self.add(event('verdict','foreperson',self.audience(),outcomes={'C1':'hung'}))
        self.assertEqual(self.state()['verdict']['outcomes']['C1'],'hung')
    def test_threshold_not_necessarily_unanimity(self):
        self.case=fixture(threshold=2);self.world=c.initialise(self.root,'threshold-case',self.case)
        self.publish();self.go('decision')
        for j in sorted(c.jurors(self.case)):self.ballot(j,j!='J01')
        self.add(event('verdict','foreperson',self.audience(),outcomes={'C1':'guilty'}))
    def test_split_outcomes_by_count(self):
        x=fixture();x['counts']={'C1':dict(label='First',elements=['I1'],bars=[]),'C2':dict(label='Second',elements=['I2'],bars=[])}
        self.case=c.validate(x);self.world=c.initialise(self.root,'mixed',x);self.publish();self.go('decision')
        for j in sorted(c.jurors(x)):
            f=self.findings(True);f['I2']=self.findings(False)['I2'];self.add(event('ballot',j,[j],findings=f))
        self.add(event('verdict','foreperson',self.audience(),outcomes={'C1':'guilty','C2':'not_guilty'}))
    def test_jury_questions_are_public_not_private_coaching(self):
        self.publish();self.go('decision')
        self.add(event('jury_question','foreperson',self.audience(),text='Does the first element have to be proved separately?',refs=[]))
        self.assertIn('Does the first element',(self.world/c.PUBLIC/'transcript.md').read_text())
    def test_new_directions_clear_ballots(self):
        self.publish();self.go('decision');self.ballot('J01')
        self.add(event('jury_presence','bench',present=True))
        self.add(event('directions','bench',self.audience(),rule='R1'))
        self.assertEqual(self.state()['ballots'],{})
    def test_no_late_evidence_to_rescue_deliberation(self):
        self.publish();self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('stipulation','bench',self.audience(),agreed_by=['player','opponent']))
    def test_bench_criminal_judgment(self):
        self.bench_world();self.go('decision')
        self.add(event('verdict','bench',findings=self.findings(False),outcomes={'C1':'not_guilty'}))
        self.assertEqual(c.verify(self.world)['status'],'PASS')
    def test_bench_civil_award(self):
        self.bench_world('civil');self.go('decision')
        self.add(event('verdict','bench',findings=self.findings(True),outcomes={'C1':'liable'},awards={'C1':75}))
        self.assertEqual(self.state()['verdict']['awards']['C1'],75)
    def test_no_damages_without_liability(self):
        self.bench_world('civil');self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('verdict','bench',findings=self.findings(False),outcomes={'C1':'not_liable'},awards={'C1':75}))
    def test_unknown_reference_rejected(self):
        self.bench_world();self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('verdict','bench',findings=self.findings(True,'T9999'),outcomes={'C1':'guilty'}))
    def test_submission_not_evidence(self):
        self.bench_world();self.go('evidence');t=self.add(event('submission','player',refs=[]))[0];self.go('decision')
        with self.assertRaises(c.CourtError):self.add(event('verdict','bench',findings=self.findings(True,t),outcomes={'C1':'guilty'}))
    def test_proved_finding_needs_record_refs(self):
        self.bench_world();self.go('decision');f=self.findings(True);f['I1']['refs']=[]
        with self.assertRaises(c.CourtError):self.add(event('verdict','bench',findings=f,outcomes={'C1':'guilty'}))
    def test_cannot_use_unpublished_exhibit_in_jury_argument(self):
        self.go('evidence')
        with self.assertRaises(c.CourtError):self.add(event('submission','player',self.audience(),refs=[{'id':'E1','use':'truth'}]))
    def test_erratum_never_rewrites_history(self):
        q=self.settled();before=(self.world/c.AREA/'case.json').read_bytes()
        self.add(event('erratum','engine',self.audience('W9'),target=q,replacement='Corrected.'))
        self.assertEqual(before,(self.world/c.AREA/'case.json').read_bytes());self.assertTrue(self.state()['paused'])
        self.assertNotIn('TEST_ANSWER_439',json.dumps(c.packet(self.world,'J01')))
    def test_strict_answer_erratum_invalidates_exchange(self):
        self.ask(answer=None);self.add(event('accept','player'));a=self.add(event('answer','W9',self.audience('W9'),text='WRONG_761'))[0]
        self.add(event('erratum','engine',self.audience('W9'),target=a,replacement='Correction.'))
        self.assertNotIn('WRONG_761',json.dumps(c.packet(self.world,'J01')))
    def test_gap_pauses_play_not_just_assessment(self):
        self.add(event('gap','engine',['player'],detail='Missing material source.'))
        with self.assertRaises(c.CourtError):self.add(event('phase',to='opening'))
    def test_repair_reopens_opportunities_and_clears_decision(self):
        self.verdict(False);t=self.state()['verdict']['turn']
        self.add(event('erratum','engine',self.audience(),target=t,replacement='Review required.'))
        self.add(event('repair','engine',self.audience()))
        self.assertEqual(self.state()['phase'],'evidence');self.assertIsNone(self.state()['verdict'])
        self.assertFalse((self.world/c.AREA/'decision-record.json').exists())
    def test_stale_revision_and_boolean_rejected(self):
        for n in (-1,1,True):
            with self.assertRaises(c.CourtError):c.record(self.world,event('private','player',['player']),expected=n)
    def test_existing_lock_not_broken(self):
        p=self.world/c.AREA/'writer.lock';p.write_text('test')
        with self.assertRaises(c.CourtError):self.add(event('private','player',['player']))
        self.assertTrue(p.exists())
    def test_invalid_batch_has_no_partial_commit(self):
        before=(self.world/c.AREA/'events.jsonl').read_bytes()
        with self.assertRaises(c.CourtError):self.add([event('private','player',['player']),event('phase',to='decision')])
        self.assertEqual(before,(self.world/c.AREA/'events.jsonl').read_bytes())
    def test_unknown_event_fields_rejected(self):
        e=event('private','player',['player']);e['secret_authority']='forbidden'
        with self.assertRaises(c.CourtError):self.add(e)
        with self.assertRaises(c.CourtError):self.add(event('private','player',['player'],new_secret_fact='bad'))
    def test_projection_recovery_after_commit_failure(self):
        with patch.object(c,'render',side_effect=OSError('simulated cache failure')):
            with self.assertRaises(OSError):self.add(event('private','player',['player'],text='SURVIVES_736'))
        self.assertEqual(len(c.read_events(self.world)),1)
        self.assertEqual(c.resume(self.world)['status'],'PASS')
        self.assertIn('SURVIVES_736',(self.world/c.PUBLIC/'private-record.md').read_text())
    def test_resume_preserves_pending_question_exactly(self):
        self.ask();before=self.state()['pending'];p=self.world/c.AREA/'live.json';p.write_text('{}')
        with self.assertRaises(c.CourtError):c.verify(self.world)
        c.resume(self.world);self.assertEqual(self.state()['pending'],before)
    def test_checkpoint_preserves_scene(self):
        self.add(event('checkpoint','engine',['player'],scene={'location':'Room 4','active_witness':'W9','next':'cross'}))
        c.resume(self.world);self.assertEqual(self.state()['scene']['active_witness'],'W9')
    def test_exact_transcript(self):
        self.go('evidence');q='Did you say "may", not "must"?\nThat exact word?';a='I said "may".'
        self.add(event('exchange','player',self.audience('W9'),witness='W9',question=q,answer=a));self.add(event('accept','opponent'))
        t=(self.world/c.PUBLIC/'transcript.md').read_text();self.assertIn(q,t);self.assertIn(a,t)
    def test_unseal_only_closed_with_confirmation(self):
        with self.assertRaises(c.CourtError):self.add(event('unseal','engine',['player'],confirmed=True))
        self.verdict(False);self.go('closed')
        with self.assertRaises(c.CourtError):self.add(event('unseal','engine',['player'],confirmed=False))
        self.add(event('unseal','engine',['player'],confirmed=True))
        self.assertTrue((self.world/c.PUBLIC/'unsealed-case.json').exists())
    def test_record_only_decision_snapshot(self):
        self.verdict(False);s=(self.world/c.AREA/'decision-record.json').read_text()
        self.assertNotIn('AUTHOR_TRUTH_NEVER_EXPORT_563',s);self.assertNotIn('PRIVATE_CLIENT_MARKER_819',s)
    def test_style_change_does_not_change_substantive_case(self):
        source=fixture()
        alt=builder.configure(source,style='nsw-drama',forum='jury',side='defence',size=3)
        for key in ('truth','documents','issues','counts'):
            self.assertEqual(source[key],alt[key])
        self.assertEqual(source['rules'],alt['rules'])
    def test_custom_jurisdiction_is_independent_of_presentation(self):
        x=fixture(style='us-drama');x['config']['jurisdiction']='Fictional orbital tribunal with supplied law'
        c.validate(x);self.assertEqual(x['config']['style'],'us-drama')
    def test_partial_hung_and_resolved_counts(self):
        x=fixture();x['counts']={'C1':dict(label='First',elements=['I1'],bars=[]),'C2':dict(label='Second',elements=['I2'],bars=[])}
        self.case=c.validate(x);self.world=c.initialise(self.root,'partial-hung',x);self.publish();self.go('decision')
        self.add(event('deliberation','J01',sorted(c.jurors(x)),refs=[]))
        for j in sorted(c.jurors(x)):
            f=self.findings(True)
            if j=='J01':f['I2']=self.findings(False)['I2']
            self.add(event('ballot',j,[j],findings=f))
        self.add(event('deadlock','foreperson',self.audience(),counts=['C2']))
        self.add(event('verdict','foreperson',self.audience(),outcomes={'C1':'guilty','C2':'hung'}))
    def test_starter_role_switch_swaps_confidential_allocation(self):
        source=c.load(ROOT/'modules/courtroom-v2/.sealed/last-light.json')
        changed=builder.configure(source,side='prosecution')
        self.assertEqual(source['roles']['opponent']['knowledge'],changed['roles']['player']['knowledge'])
        self.assertEqual(source['roles']['player']['knowledge'],changed['roles']['opponent']['knowledge'])
    def test_cli_smoke_validate_init_verify_resume(self):
        source=self.root/'fixture.json';source.write_bytes(c.encode(self.case))
        commands=[['validate','--case',str(source)],['init','--case',str(source)],['verify'],['resume']]
        for args in commands:
            r=subprocess.run([sys.executable,str(ROOT/'tools/courtroom_v2.py'),*args,'--root',str(self.root),'--world','cli-case'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
    def test_cli_packet_needs_private_output(self):
        args=[sys.executable,str(ROOT/'tools/courtroom_v2.py'),'packet','--root',str(self.root),'--world','test-court','--role','J01']
        r=subprocess.run(args,capture_output=True,text=True);self.assertNotEqual(r.returncode,0)
        target=self.world/'.world/packets/J01.json'
        r=subprocess.run(args+['--out',str(target)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
        self.assertNotIn('ADMITTED_CONTENT_761',r.stdout)
    def test_cli_new_case_scaffold_then_validation_rejects_draft(self):
        dest=self.root/'new.json'
        r=subprocess.run([sys.executable,str(ROOT/'tools/courtroom_cases.py'),'--scenario','new','--case-type','civil','--factfinder','jury','--out',str(dest)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        with self.assertRaises(c.CourtError):c.validate(c.load(dest))


if __name__=='__main__': unittest.main()
