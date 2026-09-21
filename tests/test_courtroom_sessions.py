"""Exercise real isolated mock conversations, not just filtered packet values."""
from coverage_fixture import certify
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy

from test_courtroom_v2 import fixture, event
import courtroom_v2 as c
import courtroom_sessions as s
from courtroom_backend import DeterministicBackend, Capabilities, Session


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.case = fixture()
        self.world = c.initialise(self.root, 'isolated', self.case, allow_mock_rehearsal=True)
        self.backend = DeterministicBackend(self.root / 'backend')
    def tearDown(self):
        self.tmp.cleanup()
    def start(self):
        self.runtime = s.Orchestrator.start(self.world, self.backend)
        return self.runtime
    def history(self, identity):
        entry = self.runtime.state()['sessions'][identity]
        return json.dumps(self.backend.inspect(entry['session_id']))
    def queue(self, who, text='Spoken contribution.', data=None, private=''):
        self.backend.queue(who, {'text': text, 'data': data or {}, 'private_reasoning': private})
    def add(self, e):
        return c.record(self.world, e, _fixture=True)
    def hearing(self):
        self.add(event('phase', to='opening')); self.add(event('phase', to='evidence'))
    def decision(self):
        self.hearing()
        self.add(event('publish','bench',sorted(c.CORE | c.jurors(self.case)),document='E1'))
        self.add(event('phase',to='closing'))
        self.add(event('directions','bench',sorted(c.CORE | c.jurors(self.case)),rule='R1'))
        self.add(event('phase',to='decision'))
    def findings(self, mark='PRIVATE_BALLOT_A'):
        return {i: {'status':'not_proved','reason':mark,'refs':[]} for i in self.case['issues']}

    def test_all_identities_get_distinct_persistent_physical_contexts(self):
        r=self.start(); entries=r.state()['sessions']
        self.assertEqual(set(entries), {'opponent','W9','WitnessX','S1','judge_admissibility','judge_merits'} | c.jurors(self.case))
        self.assertNotIn('player',entries)
        self.assertEqual(len(entries),len({v['session_id'] for v in entries.values()}))
    def test_witness_canaries_and_author_truth_absent_from_actual_histories(self):
        self.start()
        self.assertIn('OWN_MEMORY_679',self.history('W9'))
        self.assertNotIn('OTHER_MEMORY_211',self.history('W9'))
        self.assertNotIn('OWN_MEMORY_679',self.history('WitnessX'))
        for role in self.runtime.state()['sessions']:
            self.assertNotIn('AUTHOR_TRUTH_NEVER_EXPORT_563',self.history(role))
            self.assertNotIn('PRIVATE_CLIENT_MARKER_819',self.history(role))
    def test_private_planning_stays_in_its_session(self):
        self.add(event('private','player',['player'],text='PLAYER_STRATEGY_CANARY'))
        r=self.start(); self.queue('opponent', 'OPPONENT_STRATEGY_CANARY', private='OPPONENT_REASONING_CANARY')
        r.turn('opponent','private',['opponent'])
        self.assertNotIn('PLAYER_STRATEGY_CANARY',self.history('opponent'))
        self.assertNotIn('OPPONENT_STRATEGY_CANARY',json.dumps(r.player_packet()))
        for role in r.state()['sessions']:
            if role!='opponent': self.assertNotIn('OPPONENT_REASONING_CANARY',self.history(role))
    def test_judge_and_jurors_never_receive_contested_material(self):
        self.hearing()
        self.add(event('disclose','player',sorted(c.CORE),document='E2',to='bench'))
        self.add(event('ruling','bench',effect='document',document='E2',status='excluded',uses=[],rule='R5',text='EXCLUDED_CONTENT_301 quoted in inadmissibility reasons'))
        self.start()
        self.assertIn('EXCLUDED_CONTENT_301',self.history('judge_admissibility'))
        for who in ['judge_merits',*c.jurors(self.case)]:
            self.assertNotIn('EXCLUDED_CONTENT_301',self.history(who))
    def test_jurors_do_not_receive_outside_conferences_or_counsel_plans(self):
        self.hearing(); self.add(event('jury_presence','bench',present=False))
        self.add(event('exchange','player',sorted(c.CORE | {'W9'}),witness='W9',question='Private sidebar?',answer='BENCH_ONLY_CANARY'))
        self.add(event('accept','opponent'))
        self.add(event('private','opponent',['opponent'],text='OPPONENT_PLAN_CANARY'))
        self.start()
        for who in c.jurors(self.case):
            self.assertNotIn('BENCH_ONLY_CANARY',self.history(who))
            self.assertNotIn('OPPONENT_PLAN_CANARY',self.history(who))
    def test_deliberation_round_robin_and_private_ballots(self):
        self.decision(); r=self.start()
        for who in sorted(c.jurors(self.case)):
            self.queue(who, 'PUBLIC_JURY_ROOM_'+who, private='PRIVATE_REASON_'+who)
        r.deliberate_round()
        self.assertIn('PUBLIC_JURY_ROOM_J01',self.history('J02'))
        self.assertNotIn('PRIVATE_REASON_J01',self.history('J02'))
        for who in sorted(c.jurors(self.case)):
            self.queue(who, 'Ballot', {'findings':self.findings('BALLOT_SECRET_'+who)})
        r.collect_ballots()
        self.assertNotIn('BALLOT_SECRET_J02',self.history('J01'))
        self.assertNotIn('BALLOT_SECRET_J01',json.dumps(r.player_packet()))
        r.return_verdict()
        self.assertEqual(c.replay(self.case,c.read_events(self.world))['verdict']['outcomes'],{'C1':'not_guilty'})
    def test_same_witness_session_after_multiple_calls_and_restart(self):
        r=self.start(); sid=r.state()['sessions']['W9']['session_id']
        for line in ['FIRST_MEMORY','SECOND_MEMORY']:
            self.queue('W9',line); r.turn('W9','dialogue',['W9','player'])
        r=s.Orchestrator.start(self.world,DeterministicBackend(self.root/'backend'));self.runtime=r
        self.assertEqual(sid,r.state()['sessions']['W9']['session_id'])
        self.assertIn('FIRST_MEMORY',self.history('W9'));self.assertIn('SECOND_MEMORY',self.history('W9'))
    def test_lost_session_rebuilds_only_that_identity(self):
        r=self.start(); before=deepcopy(r.state()['sessions'])
        self.backend.lose(before['W9']['session_id'])
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        after=self.runtime.state()['sessions']
        self.assertNotEqual(before['W9']['session_id'],after['W9']['session_id'])
        self.assertEqual(before['WitnessX']['session_id'],after['WitnessX']['session_id'])
        self.assertNotIn('OTHER_MEMORY_211',self.history('W9'))
    def test_backend_without_guarantees_fails_before_any_session(self):
        self.backend.capabilities=Capabilities(independent_contexts=False)
        with self.assertRaisesRegex(c.CourtError,'independent'):self.start()
        self.assertFalse((self.world/s.RUNTIME).exists())
    def test_reused_backend_conversation_fails(self):
        original=self.backend.create_session
        def duplicate(*args):
            v=original(*args)
            return Session(v.session_id,'shared-context',v.identity)
        self.backend.create_session=duplicate
        with self.assertRaisesRegex(c.CourtError,'context'):self.start()
    def test_raw_record_cannot_impersonate_role_in_live_world(self):
        self.start()
        with self.assertRaisesRegex(c.CourtError,'orchestrator'):
            self.add(event('dialogue','W9',['W9','player'],text='fabricated'))
    def test_human_cannot_supply_ai_speech(self):
        r=self.start()
        with self.assertRaises(c.CourtError):r.human(event('dialogue','opponent',['player','opponent']))
        with self.assertRaises(c.CourtError):r.control(event('ruling','bench',rule='R1',effect='procedure'))
    def test_model_cannot_choose_another_actor_or_audience(self):
        r=self.start();self.backend.queue('W9',{'text':'x','data':{},'actor':'WitnessX'})
        with self.assertRaises(c.CourtError):r.turn('W9','dialogue',['W9','player'])
        self.assertEqual(c.read_events(self.world),[])
    def test_no_arbitrary_prompt_injection_api(self):
        r=self.start()
        with self.assertRaises((TypeError,c.CourtError)):
            r.turn('W9','dialogue',['W9','player'],prompt='AUTHOR_TRUTH_NEVER_EXPORT_563')
    def test_flow_question_and_answer_use_different_sessions(self):
        self.hearing();r=self.start()
        self.queue('opponent','Exact question?',{'witness':'W9','question':'Exact question?','answer':None})
        self.queue('W9','Exact witness answer.')
        r.examine('opponent','W9')
        p=c.replay(self.case,c.read_events(self.world))['pending']
        self.assertEqual(p['answer'],'Exact witness answer.')
        self.assertIn('Exact question?',self.history('W9'))
        self.assertNotIn('OWN_MEMORY_679',self.history('opponent'))
    def test_cli_no_backend_fails_clearly(self):
        run=subprocess.run([sys.executable,str(Path(c.__file__)),'init','--root',str(self.root),'--world','no-backend','--case',str(self.world/c.AREA/'case.json')],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('backend',run.stderr.lower())
        self.assertFalse((self.root/'worlds/no-backend').exists())

    def test_same_witness_context_across_examinations_and_restart(self):
        self.hearing();r=self.start();sid=r.state()['sessions']['W9']['session_id']
        for n in range(2):
            self.queue('opponent',f'Question {n}',{'witness':'W9','question':f'Question {n}','answer':None})
            self.queue('W9',f'Answer {n}');r.examine('opponent','W9')
            r.human(event('accept','player'))
            r=s.Orchestrator.start(self.world,self.backend);self.runtime=r
            self.assertEqual(sid,r.state()['sessions']['W9']['session_id'])
        self.assertIn('Answer 0',self.history('W9'));self.assertIn('Answer 1',self.history('W9'))

    def test_resume_wrong_identity_fails(self):
        self.start();original=self.backend.resume_session
        def bad(sid):
            handle=original(sid);return Session(handle.session_id,handle.context_id,'someone-else')
        self.backend.resume_session=bad
        with self.assertRaisesRegex(c.CourtError,'mismatch'):s.Orchestrator.start(self.world,self.backend)

    def test_backend_tools_or_nonpersistent_contexts_refused(self):
        for caps in [Capabilities(no_ambient_access=False),Capabilities(persistent_contexts=False)]:
            self.backend.capabilities=caps
            with self.assertRaises(c.CourtError):self.start()

    def test_interrupted_model_call_rebuilds_only_affected_character(self):
        r=self.start();old=deepcopy(r.state()['sessions'])
        self.queue('W9','UNCOMMITTED_CANARY');original=self.backend.send
        def crash(sid,request):
            original(sid,request);raise OSError('connection lost after delivery')
        self.backend.send=crash
        with self.assertRaises(OSError):r.turn('W9','dialogue',['player','W9'])
        self.backend.send=original;self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertNotEqual(old['W9']['session_id'],self.runtime.state()['sessions']['W9']['session_id'])
        self.assertEqual(old['WitnessX']['session_id'],self.runtime.state()['sessions']['WitnessX']['session_id'])
        self.assertNotIn('UNCOMMITTED_CANARY',self.history('W9'))
        self.assertEqual(c.read_events(self.world),[])

    def test_revoked_evidence_rebuilds_merits_context_without_old_reasoning(self):
        self.hearing()
        self.add(event('disclose','player',sorted(c.CORE),document='E2',to='bench'))
        self.add(event('ruling','bench',effect='document',document='E2',status='admitted',uses=['truth'],rule='R5'))
        self.add(event('publish','bench',sorted(c.CORE|c.jurors(self.case)),document='E2'))
        r=self.start();before=deepcopy(r.state()['sessions'])
        self.assertIn('EXCLUDED_CONTENT_301',self.history('judge_merits'))
        self.queue('judge_admissibility','Excluded: EXCLUDED_CONTENT_301',{'effect':'document','document':'E2','status':'excluded','uses':[],'rule':'R5'})
        r.turn('judge_admissibility','ruling',sorted(c.CORE))
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who in ['judge_merits',*c.jurors(self.case)]:
            self.assertNotEqual(before[who]['session_id'],self.runtime.state()['sessions'][who]['session_id'])
            self.assertNotIn('EXCLUDED_CONTENT_301',self.history(who))
        self.assertEqual(before['W9']['session_id'],self.runtime.state()['sessions']['W9']['session_id'])
        # A later provider loss must not reintroduce the retired conversation.
        self.backend.lose(self.runtime.state()['sessions']['judge_merits']['session_id'])
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertNotIn('EXCLUDED_CONTENT_301',self.history('judge_merits'))

    def test_personality_and_support_roles_have_separate_contexts(self):
        self.start()
        self.assertIn('CLIENT_SUPPORT_632',self.history('S1'))
        self.assertNotIn('CLIENT_SUPPORT_632',self.history('W9'))
        self.assertIn('Temperament is not evidence',self.history('W9'))

    def test_jury_mixed_and_hung_outcomes_use_individual_ballots(self):
        case=fixture();case['counts']={'C1':{'label':'One','elements':['I1'],'bars':[]},'C2':{'label':'Two','elements':['I2'],'bars':[]}}
        self.case=c.validate(case);self.world=c.initialise(self.root,'mixed',certify(case), allow_mock_rehearsal=True)
        self.decision();r=self.start()
        for who in sorted(c.jurors(case)):self.queue(who,'Different views '+who,{'refs':[]})
        r.deliberate_round()
        for who in sorted(c.jurors(case)):
            f=self.findings()
            f['I1']={'status':'proved','reason':'Supported','refs':[{'id':'E1','use':'truth'}]}
            if who!='J01': f['I2']=deepcopy(f['I1'])
            self.queue(who,'Private vote',{'findings':f})
        r.collect_ballots();r.return_verdict()
        self.assertEqual(c.replay(case,c.read_events(self.world))['verdict']['outcomes'],{'C1':'guilty','C2':'hung'})

    def test_runtime_lock_prevents_concurrent_calls(self):
        r=self.start()
        with s.runtime_lock(self.world):
            with self.assertRaisesRegex(c.CourtError,'in progress'):r.turn('W9','dialogue',['W9','player'])

    def test_model_response_cannot_modify_world(self):
        r=self.start();before=(self.world/c.AREA/'case.json').read_bytes()
        self.backend.queue('opponent',{'text':'x','data':{},'tool_calls':[{'write':'case.json'}]})
        with self.assertRaises(c.CourtError):r.turn('opponent','private',['opponent'])
        self.assertEqual(before,(self.world/c.AREA/'case.json').read_bytes())

    def test_merits_and_admissibility_judges_cannot_swap_jobs(self):
        r=self.start()
        with self.assertRaises(c.CourtError):r.turn('judge_admissibility','verdict',sorted(c.CORE))
        with self.assertRaises(c.CourtError):r.turn('judge_merits','ruling',sorted(c.CORE))

    def test_every_role_has_private_canary_in_only_its_context(self):
        case=fixture()
        for who,role in case['roles'].items():
            # Appearance/manner is a permitted identity attribute, not historical truth.
            role['manner']='VOICE_CANARY_'+who
            role['author_note']='HIDDEN_AUTHOR_METADATA_'+who
        self.case=case;self.world=c.initialise(self.root,'canaries',certify(case), allow_mock_rehearsal=True);r=self.start()
        for who in r.state()['sessions']:
            history=self.history(who);own=s.role_for(who)
            self.assertIn('VOICE_CANARY_'+own,history)
            self.assertNotIn('HIDDEN_AUTHOR_METADATA_',history)
            for other in case['roles']:
                if other!=own:self.assertNotIn('VOICE_CANARY_'+other,history)

    def test_admissibility_testimony_is_not_judicial_merits_evidence(self):
        self.hearing()
        self.add(event('jury_presence','bench',present=False))
        e=event('exchange','player',sorted(c.CORE|{'W9'}),question='Foundation only?',witness='W9',answer='ADMISSIBILITY_TESTIMONY_CANARY')
        e['purpose']='admissibility'
        self.add(e);self.add(event('accept','opponent'))
        self.start()
        self.assertIn('ADMISSIBILITY_TESTIMONY_CANARY',self.history('judge_admissibility'))
        self.assertNotIn('ADMISSIBILITY_TESTIMONY_CANARY',self.history('judge_merits'))
        for who in c.jurors(self.case):self.assertNotIn('ADMISSIBILITY_TESTIMONY_CANARY',self.history(who))

    def test_repeated_safe_rebuild_preserves_only_own_committed_reasoning(self):
        r=self.start();self.queue('W9','Own statement',private='WITNESS_PRIVATE_THOUGHT')
        r.turn('W9','dialogue',['W9','player'])
        for _ in range(2):
            self.backend.lose(r.state()['sessions']['W9']['session_id'])
            r=s.Orchestrator.start(self.world,self.backend);self.runtime=r
            self.assertIn('WITNESS_PRIVATE_THOUGHT',self.history('W9'))
            self.assertNotIn('OTHER_MEMORY_211',self.history('W9'))

    def test_controller_rejects_merits_reference_not_in_routed_packet(self):
        # A valid global reference is not enough: it must be visible to this session.
        self.hearing()
        self.add(event('jury_presence','bench',present=False))
        self.add(event('exchange','player',sorted(c.CORE|{'W9'}),witness='W9',question='Sidebar?',answer='PRIVATE_SIDE_TESTIMONY'))
        self.add(event('accept','opponent'))
        q=next(e['id'] for e in c.read_events(self.world) if e['type']=='exchange')
        self.add(event('jury_presence','bench',present=True))
        self.add(event('phase',to='closing'))
        self.add(event('directions','bench',sorted(c.CORE|c.jurors(self.case)),rule='R1'))
        self.add(event('phase',to='decision'))
        r=self.start();self.queue('J01','Guess unseen evidence',{'refs':[{'id':q,'use':'truth'}]})
        with self.assertRaises(c.CourtError):r.turn('J01','deliberation',sorted(c.jurors(self.case)))

    def test_jury_round_can_resume_after_crash_without_repeating_speaker(self):
        self.decision();r=self.start()
        self.queue('J01','ONCE_ONLY_J01')
        with self.assertRaises(c.CourtError):r.deliberate_round()
        self.runtime=r=s.Orchestrator.start(self.world,self.backend)
        self.queue('J02','NEXT_J02');self.queue('J03','NEXT_J03')
        r.deliberate_round()
        spoken=[e['actor'] for e in c.read_events(self.world) if e['type']=='deliberation']
        self.assertEqual(spoken,['J01','J02','J03'])

    def test_duplicate_session_ids_are_rejected(self):
        original=self.backend.create_session
        def same_session(*args):
            h=original(*args);return Session('same-session',h.context_id,h.identity)
        self.backend.create_session=same_session
        with self.assertRaises(c.CourtError):self.start()

    def test_context_ids_are_distinct_and_restored(self):
        r=self.start();before=r.state()['sessions']
        self.assertEqual(len(before),len({e['context_id'] for e in before.values()}))
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who,e in before.items():self.assertEqual(e['context_id'],self.runtime.state()['sessions'][who]['context_id'])

    def test_committed_response_recovery_does_not_duplicate_speech(self):
        r=self.start();self.queue('W9','EXACT_ONCE')
        original=c.render
        def crash(*args):raise OSError('crash after journal commit')
        c.render=crash
        try:
            with self.assertRaises(OSError):r.turn('W9','dialogue',['W9','player'])
        finally:c.render=original
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertEqual([e['text'] for e in c.read_events(self.world)],['EXACT_ONCE'])
        self.assertEqual(len(self.runtime.state()['sessions']['W9']['history']),1)
        self.assertEqual(c.verify(self.world)['status'],'PASS')

    def test_bench_decision_is_generated_only_by_merits_session(self):
        self.case=fixture('civil','bench');self.world=c.initialise(self.root,'bench-runtime',self.case, allow_mock_rehearsal=True)
        self.hearing();self.add(event('phase',to='closing'));self.add(event('phase',to='decision'))
        r=self.start();self.queue('judge_merits','Record-based judgment',{'findings':self.findings(),'outcomes':{'C1':'not_liable'}})
        r.turn('judge_merits','verdict',sorted(c.CORE))
        self.assertEqual(c.replay(self.case,c.read_events(self.world))['verdict']['outcomes'],{'C1':'not_liable'})
        self.assertNotIn('Record-based judgment',self.history('judge_admissibility'))

    def test_strict_examination_uses_witness_after_objection_opportunity(self):
        self.hearing();self.add(event('cadence',mode='strict'));r=self.start()
        self.queue('opponent','Strict question?',{'witness':'W9','question':'Strict question?','answer':None})
        r.examine('opponent','W9');r.human(event('accept','player'))
        self.queue('W9','STRICT_WITNESS_ANSWER')
        r.turn('W9','answer',sorted(c.CORE|{'W9'}|c.jurors(self.case)))
        self.assertIn('STRICT_WITNESS_ANSWER',json.dumps(c.read_events(self.world)))
        self.assertIn('Strict question?',self.history('W9'))

    def test_closed_sessions_rebuild_without_cross_role_history(self):
        r=self.start();self.queue('opponent','Private plan',private='PRIVATE_AFTER_CLOSE')
        r.turn('opponent','private',['opponent']);r.close()
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertIn('PRIVATE_AFTER_CLOSE',self.history('opponent'))
        self.assertNotIn('PRIVATE_AFTER_CLOSE',self.history('W9'))

    def test_startup_wrong_backend_is_refused(self):
        self.start()
        with self.assertRaisesRegex(c.CourtError,'backend'):
            s.Orchestrator.start(self.world,DeterministicBackend(self.root/'different'))

    def test_flow_witness_receives_only_journalled_question(self):
        self.hearing();r=self.start()
        self.queue('opponent','Recorded question?',{'witness':'W9','question':'Recorded question?','answer':None})
        self.queue('W9','Recorded answer.')
        original=self.backend.send
        def check(sid,request):
            if request['identity']=='W9':
                self.assertTrue(any(e['type']=='exchange' and e['data']['question']=='Recorded question?' for e in c.read_events(self.world)))
            return original(sid,request)
        self.backend.send=check;r.examine('opponent','W9')

    def test_cli_turn_uses_same_authority_registry_as_controller(self):
        self.start()
        script=self.root/'script.json';script.write_text(json.dumps({'W9':[{'text':'CLI_EXACT','data':{}}]}))
        # CLI mock storage uses this conventional per-world backend directory.
        other=c.initialise(self.root,'cli-turn',self.case, allow_mock_rehearsal=True)
        for args in [['start'],['turn','--identity','W9','--kind','dialogue','--audience','W9','player','--script',str(script)]]:
            run=subprocess.run([sys.executable,str(Path(s.__file__)),*args,'--root',str(self.root),'--world','cli-turn','--backend','mock','--allow-mock'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(c.read_events(other)[0]['text'],'CLI_EXACT')

    def test_admissibility_judge_cannot_emit_merits_stipulations(self):
        r=self.start()
        with self.assertRaises(c.CourtError):r.turn('judge_admissibility','stipulation',sorted(c.CORE))

    def test_provisional_answer_never_reaches_jurors_before_acceptance(self):
        self.hearing();r=self.start()
        self.queue('opponent','Question?',{'witness':'W9','question':'Question?','answer':None})
        self.queue('W9','PROVISIONAL_CANARY');r.examine('opponent','W9')
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who in ['judge_merits',*c.jurors(self.case)]:self.assertNotIn('PROVISIONAL_CANARY',self.history(who))
        r.human(event('objection','player',rule='R4'))
        self.queue('judge_admissibility','Sustained',{'rule':'R4','effect':'objection','result':'sustained'})
        r.turn('judge_admissibility','ruling',sorted(c.CORE))
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who in ['judge_merits',*c.jurors(self.case)]:self.assertNotIn('PROVISIONAL_CANARY',self.history(who))

    def test_session_map_and_backend_files_are_private(self):
        r=self.start()
        self.assertEqual((self.world/s.RUNTIME).stat().st_mode & 0o777,0o600)
        for entry in r.state()['sessions'].values():
            p=self.backend.directory/(entry['session_id']+'.json')
            self.assertEqual(p.stat().st_mode & 0o777,0o600)

    def test_quarantined_derived_testimony_cannot_be_cited_after_rebuild(self):
        self.hearing()
        self.add(event('disclose','player',sorted(c.CORE),document='E2',to='bench'))
        self.add(event('ruling','bench',effect='document',document='E2',status='admitted',uses=['truth'],rule='R5'))
        q=self.add(event('exchange','player',sorted(c.CORE|c.jurors(self.case)|{'W9'}),witness='W9',question='Based on this?',answer='DERIVED_CANARY'))[0]
        self.add(event('accept','opponent'))
        self.add(event('ruling','bench',effect='document',document='E2',status='excluded',uses=[],rule='R5'))
        self.add(event('phase',to='closing'))
        self.add(event('directions','bench',sorted(c.CORE|c.jurors(self.case)),rule='R1'))
        self.add(event('phase',to='decision'))
        r=self.start();self.assertNotIn('DERIVED_CANARY',self.history('J01'))
        self.queue('J01','Cite quarantined evidence',{'refs':[{'id':q,'use':'truth'}]})
        with self.assertRaises(c.CourtError):r.turn('J01','deliberation',sorted(c.jurors(self.case)))

    def test_prepared_world_cannot_record_live_roles_without_backend(self):
        with self.assertRaisesRegex(c.CourtError,'backend'):
            c.record(self.world,event('dialogue','W9',['W9','player']))

    def test_sustained_objection_quarantines_intervening_echo_of_answer(self):
        self.hearing();r=self.start()
        self.queue('opponent','Q?',{'witness':'W9','question':'Q?','answer':None})
        self.queue('W9','PROVISIONAL_ECHO_CANARY');r.examine('opponent','W9')
        r.human(event('submission','player',sorted(c.CORE|c.jurors(self.case)),text='The witness said PROVISIONAL_ECHO_CANARY',refs=[]))
        self.backend.lose(r.state()['sessions']['judge_merits']['session_id'])
        self.runtime=r=s.Orchestrator.start(self.world,self.backend)
        self.assertIn('PROVISIONAL_ECHO_CANARY',self.history('judge_merits'))
        r.human(event('objection','player',rule='R4'))
        self.queue('judge_admissibility','Sustained',{'rule':'R4','effect':'objection','result':'sustained'})
        r.turn('judge_admissibility','ruling',sorted(c.CORE))
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who in ['judge_merits',*c.jurors(self.case)]:self.assertNotIn('PROVISIONAL_ECHO_CANARY',self.history(who))

    def test_corrected_private_ballot_retires_contaminated_own_context(self):
        self.decision();r=self.start()
        self.queue('J01','WRONG_BALLOT_CANARY',{'findings':self.findings('WRONG_BALLOT_CANARY')})
        target=r.turn('J01','ballot',['J01'])[0]
        previous=r.state()['sessions']['J01']['session_id']
        r.control(event('erratum','engine',sorted(c.jurors(self.case)),text='A private ballot contained an engine error.',target=target,replacement='Reconsider from the record.'))
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertNotEqual(previous,self.runtime.state()['sessions']['J01']['session_id'])
        self.assertNotIn('WRONG_BALLOT_CANARY',self.history('J01'))
