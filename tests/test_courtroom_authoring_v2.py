"""Shared-world projection canaries; synthetic cases, never a live readiness claim."""
from copy import deepcopy
import json
import unittest
from test_courtroom_v2 import fixture
import courtroom_v2 as c
import courtroom_authoring as a
from courtroom_grounding import sources, check_grounding, validate_assessment
from courtroom_sessions import routed_packet


def substrate_fixture():
    case=fixture()
    case.pop('coverage_rehearsal');case.pop('truth')
    case.update(authoring_version=2,time_scale='Integer minutes from fixture morning')
    people=list(case['roles'])
    space={'Room':{'name':'Archive room','adjacent':['Office'],'distances':{'Office':5},
                    'sightlines':['Office'],'lighting':'clear','access':people},
           'Office':{'name':'Separate office','adjacent':['Room'],'distances':{'Room':5},
                     'sightlines':['Room'],'lighting':'clear','access':people}}
    time={'Count':{'at':10,'location':'Room','actors':['W9'],'audible_range':2,
                  'facts':{'packs':{'text':'SHARED_VISIBLE_731','channel':'visual'},
                           'mutter':{'text':'NEAR_SOUND_811','channel':'audible'},
                           'intent':{'text':'W9_PRIVATE_INTENT_521','channel':'actor'}}},
          'Private':{'at':20,'location':'Office','actors':['WitnessX'],'audible_range':0,
                     'facts':{'memory':{'text':'X_PRIVATE_MEMORY_612','channel':'actor'}}}}
    records={key:{**doc,'display_provenance':doc['provenance'],'provenance':'SEALED_ORIGIN_381',
                  'author':'W9','date':'fixture morning','recipients':['player','opponent','W9'],
                  'received_by':['player','opponent','W9'] if key=='E1' else ['player','opponent'],
                  'alterations':['SEALED_ALTERATION_491']} for key,doc in case['documents'].items()}
    case['substrate']={'space':space,'time':time,'records':records,
        'flows':{'F1':{'kind':'goods','from':'W9','to':'WitnessX','at':'Count','records':['E1'],
                       'description':'PARTICIPANTS_TRANSFER_811'}}}
    for who,old in list(case['roles'].items()):
        kind=old['kind'];witness=kind=='witness'
        role={'name':old['name'],'kind':kind,'positions':[],
              'affiliation':'defence' if who in {'W9','player','S1'} else 'prosecution' if who in {'WitnessX','opponent'} else 'neutral',
              'routine':{},'deltas':{},'perception_limits':{},'account':{},'divergences':{},
              'fallibility':[{'kind':'error','scope':'May misread a count.'}] if witness else [],
              'pressure_points':{'ordinary':{'description':'Dislikes speaking before a group.','case_linked':False}},
              'manner':'Pauses to organise words when under any pressure.'}
        if witness:
            role['template']='lay_eyewitness'
            role['positions']=[{'location':'Room' if who=='W9' else 'Office','start':10,'end':10}]
            for index,domain in enumerate(a.TEMPLATES['lay_eyewitness']['routine_domains']):
                role['routine'][domain]={'domain':domain,'description':'Fixture usual '+domain,
                    'tools':['pencil'],'sequence':index,'usual_choices':['Check before recording.']}
        case['roles'][who]=role
        if old.get('knowledge'):
            time['Bio_'+who]={'at':-10,'location':'Room','actors':[who],'audible_range':0,
                             'facts':{'past':{'text':' '.join(old['knowledge']),'channel':'actor'}}}
    for issue in case['issues'].values():issue['substrate_refs']=['time:Count:packs']
    case['coverage_probes']={who:['Exact unauthored first schoolbag colour?','Exact unauthored first holiday date?']
                             for who in c.members(case,'witness')}
    return a.compile_case(case)


def certified_fixture():
    from coverage_fixture import certify
    return certify(substrate_fixture())


class AuthoringV2Tests(unittest.TestCase):
    def setUp(self):self.case=substrate_fixture()
    def test_valid_substrate_replaces_freehand_knowledge(self):
        c.validate_foundation(self.case)
        self.assertNotIn('knowledge',self.case['roles']['W9'])
        self.assertIn('time:Count:packs',routed_packet(self.case,[],'W9')['role']['knowledge_basis'])
    def test_private_facts_records_and_raw_substrate_never_cross(self):
        w=json.dumps(routed_packet(self.case,[],'W9'))
        x=json.dumps(routed_packet(self.case,[],'WitnessX'))
        self.assertNotIn('X_PRIVATE_MEMORY_612',w)
        self.assertNotIn('W9_PRIVATE_INTENT_521',x)
        for who in self.case['roles']:
            p=json.dumps(routed_packet(self.case,[], 'judge_merits' if who=='bench' else who))
            for secret in ('SEALED_ORIGIN_381','SEALED_ALTERATION_491','"substrate"','"substrate_refs"'):
                self.assertNotIn(secret,p)
    def test_sightline_distance_light_and_access_drive_projection(self):
        self.assertIn('time:Count:packs',a.project(self.case,'WitnessX')['sources'])
        self.assertNotIn('time:Count:mutter',a.project(self.case,'WitnessX')['sources'])
        for change in ('dark','sightline'):
            x=deepcopy(self.case)
            if change=='dark':x['substrate']['space']['Room']['lighting']='dark'
            else:x['substrate']['space']['Office']['sightlines']=[]
            self.assertNotIn('time:Count:packs',a.project(x,'WitnessX')['sources'])
        self.case['substrate']['space']['Office']['access'].remove('WitnessX')
        with self.assertRaisesRegex(c.CourtError,'access'):c.validate_foundation(self.case)
    def test_records_require_actual_receipt_and_flows_are_personal(self):
        self.assertNotIn('records:E2:content',a.project(self.case,'W9')['sources'])
        self.assertIn('flows:F1:transfer',a.project(self.case,'W9')['sources'])
        self.assertNotIn('flows:F1:transfer',a.project(self.case,'player')['sources'])
        self.assertEqual(a.project(self.case,'bench')['knowledge_basis'],[])
        self.assertEqual(a.project(self.case,'J01')['knowledge_basis'],[])
    def test_limit_removes_raw_fact_and_is_owned(self):
        self.case['roles']['W9']['perception_limits']['count']={
            'refs':['time:Count:packs'],'kind':'approximate','account':'Saw approximately a dozen packs.'}
        p=routed_packet(self.case,[],'W9');s=sources(p)
        self.assertNotIn('SHARED_VISIBLE_731',json.dumps(p))
        self.assertIn('perception:W9:count',s)
        check_grounding(p,{'refs':['perception:W9:count'],'boundaries':['count']})
        with self.assertRaises(c.CourtError):check_grounding(p,{'refs':['perception:WitnessX:count'],'boundaries':[]})
        self.case['roles']['W9']['perception_limits']['count']['refs']=['time:Private:memory']
        with self.assertRaisesRegex(c.CourtError,'envelope'):c.validate_foundation(self.case)
    def test_ignorance_boundary_contains_no_hidden_catalogue(self):
        p=a.project(self.case,'W9')
        boundary=p['sources']['perception:W9:outside_envelope']
        self.assertNotIn('Private',boundary)
        self.assertNotIn('WitnessX',boundary)
        self.assertIn('no personal basis',boundary)
    def test_record_limit_cannot_reappear_through_document_alias(self):
        self.case['roles']['W9']['perception_limits']['record']={'refs':['records:E1:content'],
            'kind':'cannot_recall','account':'Cannot recall the exact wording.'}
        packet=routed_packet(self.case,[],'W9')
        self.assertNotIn('ADMITTED_CONTENT_761',json.dumps(packet))
        self.assertNotIn('E1',packet['documents'])
    def test_new_scaffold_uses_shared_stores_but_cannot_play(self):
        draft=a.scaffold(fixture())
        self.assertEqual(set(draft['substrate']),a.LAYERS)
        self.assertNotIn('knowledge',draft['roles']['W9'])
        with self.assertRaises(c.CourtError):c.validate_foundation(draft)
    def test_unknown_citations_and_empty_witness_citations_fail(self):
        p=routed_packet(self.case,[],'W9')
        for refs in ([],['time:Private:memory'],['W9.knowledge.0']):
            with self.assertRaises(c.CourtError):check_grounding(p,{'refs':refs,'boundaries':[]})
    def test_uncertainty_requires_limit_or_routine_not_document(self):
        p=routed_packet(self.case,[],'W9')
        response={'text':'','data':{'result':'supported_uncertainty','refs':['routine:W9:occupation']}}
        validate_assessment(p,response)
        response['data']['refs']=['records:E1:content']
        with self.assertRaises(c.CourtError):validate_assessment(p,response)
    def test_account_differences_require_reasoned_owned_divergence(self):
        role=self.case['roles']['WitnessX'];ref='time:Count:packs'
        role['account'][ref]='Saw three packs.'
        with self.assertRaisesRegex(c.CourtError,'divergence'):c.validate_foundation(self.case)
        role['divergences'][ref]={'reason':'honest_error','account':'Saw three packs.'}
        c.validate_foundation(self.case)
        role['divergences'][ref]['reason']=''
        with self.assertRaises(c.CourtError):c.validate_foundation(self.case)
    def test_fairness_and_unshared_decisive_issue(self):
        bad=deepcopy(self.case);bad['roles']['W9']['pressure_points']['ordinary']['case_linked']=True
        with self.assertRaisesRegex(c.CourtError,'innocent'):c.validate_foundation(bad)
        bad=deepcopy(self.case);bad['roles']['WitnessX']['fallibility']=[]
        with self.assertRaisesRegex(c.CourtError,'fallibility'):c.validate_foundation(bad)
        self.case['issues']['I1']['substrate_refs']=['time:Private:memory']
        with self.assertRaisesRegex(c.CourtError,'unshared'):c.validate_foundation(self.case)
        self.case['issues']['I1']['single_source']='Deliberately depends on the only observer.'
        c.validate_foundation(self.case)
    def test_derived_caches_and_freehand_fields_cannot_bypass_projector(self):
        for target in ('knowledge','documents','templates'):
            case=deepcopy(self.case)
            if target=='knowledge':case['roles']['W9']['knowledge']=['UNROUTED_SECRET']
            elif target=='documents':case['documents']['E1']['text']='TAMPERED'
            else:case['coverage_templates']={'lay_eyewitness':{}}
            with self.assertRaises(c.CourtError):c.validate_foundation(case)
    def test_routine_required_domains_and_episode_delta_ownership(self):
        role=self.case['roles']['W9'];role['routine'].pop('occupation')
        with self.assertRaisesRegex(c.CourtError,'routine'):c.validate_foundation(self.case)
        self.case=substrate_fixture()
        self.case['roles']['W9']['deltas']['change']={'step':'occupation','event':'time:Private:memory','description':'A change.'}
        with self.assertRaises(c.CourtError):c.validate_foundation(self.case)
    def test_all_stores_declared_and_positions_cannot_overlap(self):
        bad=deepcopy(self.case);bad['substrate'].pop('flows')
        with self.assertRaises(c.CourtError):c.validate_foundation(bad)
        self.case['roles']['W9']['positions'].append({'location':'Office','start':10,'end':12})
        with self.assertRaisesRegex(c.CourtError,'position'):c.validate_foundation(self.case)


class AuthoringRehearsalTests(unittest.TestCase):
    def test_fixed_templates_and_blind_probe_family_coverage(self):
        import courtroom_rehearsal as r
        case=certified_fixture();report=case['coverage_rehearsal']
        c.validate_readiness(case)
        self.assertEqual(r.template_for(case,'W9')[0],'lay_eyewitness')
        rows=report['witnesses']['W9']['answers']
        self.assertEqual({x['area'] for x in rows if x['probe_class']=='examiner'},set(r.FAMILIES))
        rows.remove(next(x for x in rows if x['probe_class']=='examiner' and x['area']=='tools'))
        r.seal_report(report)
        with self.assertRaisesRegex(c.CourtError,'every template family'):c.validate_readiness(case)
    def test_invalid_citation_cannot_pass_even_with_unanimous_lenient_graders(self):
        import courtroom_rehearsal as r
        case=certified_fixture();row=case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
        row['grounding']={'refs':['time:Private:memory'],'boundaries':[]}
        row['citation_error']=r.citation_error(r.packet_for(case,'W9'),row)
        r.seal_report(case['coverage_rehearsal'])
        self.assertEqual(r.summary(case['coverage_rehearsal'])['ordinary']['unsupported_invention'],1)
        with self.assertRaisesRegex(c.CourtError,'invention'):c.validate_readiness(case)
    def test_layer_depth_is_diagnostic_and_survives_digest(self):
        import courtroom_rehearsal as r
        case=certified_fixture();c.validate_readiness(case)
        counts=r.summary(case['coverage_rehearsal'])
        self.assertTrue(counts['by_witness']['W9']['author_review'])
        self.assertEqual(len(counts['by_witness']['W9']['ordinary_source_layers']),1)
    def test_v2_gap_envelopes_use_existing_substrate_entry_and_derived_scope(self):
        import courtroom_rehearsal as r
        import courtroom_amendments as amendments
        case=certified_fixture();report=case['coverage_rehearsal']
        row=next(x for x in report['witnesses']['W9']['answers'] if x['probe_class']=='examiner' and x['area']=='activity')
        row.update(answer='',grounding={'refs':[],'boundaries':[]})
        for grade in row['assessments'].values():grade.update(bin='gap',refs=[],hearing_plausible=False)
        r.refresh_envelopes(case,report);r.seal_report(report)
        topic,scope=next(iter(report['amendment_envelopes'].items()))
        self.assertEqual(scope['target_layer'],'time')
        self.assertIn(scope['entry'],case['substrate']['time'])
        amendments.context(case,scope,topic)
        c.validate_readiness(case)
    def test_legacy_live_commitment_refused_without_rewriting_saved_case(self):
        from coverage_fixture import certify
        import courtroom_rehearsal as r
        case=fixture();before=deepcopy(case)
        case['coverage_rehearsal']['mock']=False;r.seal_report(case['coverage_rehearsal'])
        with self.assertRaisesRegex(c.CourtError,'Authoring V2'):c.validate_readiness(case,allow_mock=False)
        self.assertEqual(before['roles'],case['roles'])


class AuthoringAmendmentTests(unittest.TestCase):
    def setUp(self):self.case=substrate_fixture()
    def test_time_amendment_reprojects_all_observers_without_changing_original(self):
        import courtroom_amendments as m
        original=deepcopy(self.case)
        patch={'addition':{'fields':{'facts':{'new':{'text':'NEW_SHARED_OBSERVATION','channel':'visual'}}}}}
        revised=m.apply_entry(self.case,'time','Count',patch)
        for who in ('W9','WitnessX'):self.assertIn('NEW_SHARED_OBSERVATION',json.dumps(a.project(revised,who)))
        self.assertNotIn('NEW_SHARED_OBSERVATION',json.dumps(a.project(revised,'opponent')))
        self.assertEqual(self.case,original)
    def test_checker_scope_derived_from_shared_entries_not_manual_map(self):
        import courtroom_amendments as m
        scope={'target_layer':'time','entry':'Count','refs':['time:Count:packs']}
        value=m.context(self.case,scope,'unused')
        self.assertEqual(set(value['committed_accounts']),{'W9','WitnessX'})
        self.assertNotIn('X_PRIVATE_MEMORY_612',json.dumps(value))
        self.assertIn('W9_PRIVATE_INTENT_521',json.dumps(value['committed_entry']))
        self.assertTrue(m.matches_fault(scope,{'data':{'witness':'WitnessX'}},self.case))
        self.assertFalse(m.matches_fault(scope,{'data':{'witness':'player'}},self.case))
    def test_other_substrate_layers_and_new_receipt(self):
        import courtroom_amendments as m
        for layer,entry,fields in [('space','Room',{'access':[]}),('records','E2',{'received_by':['W9']}),
                                  ('flows','F1',{'records':['E2']})]:
            if layer=='space':
                self.case['substrate']['space']['Room']['access'].remove('S1');fields={'access':['S1']}
            with self.subTest(layer=layer):
                revised=m.apply_entry(self.case,layer,entry,{'addition':{'fields':fields}})
                c.validate_foundation(revised)
                if layer=='records':self.assertIn('records:E2:content',a.project(revised,'W9')['sources'])
    def test_historical_overwrite_and_witness_knowledge_bypass_rejected(self):
        import courtroom_amendments as m
        for layer,entry,fields in [('time','Count',{'at':12}),('records','E1',{'text':'Replacement'}),
                                  ('witness','W9',{'knowledge':['Uncommitted history']}),
                                  ('witness','W9',{'account':{'time:Count:packs':'Different'}})]:
            with self.subTest(layer=layer),self.assertRaises(c.CourtError):
                m.apply_entry(self.case,layer,entry,{'addition':{'fields':fields}})
    def test_account_change_must_be_bound_to_amended_entry_and_reasoned(self):
        import courtroom_amendments as m
        patch={'addition':{'fields':{'facts':{'colour':{'text':'Blue pack.','channel':'visual'}}},
                           'accounts':{'W9':{'account':{'time:Private:memory':'Other event'}}}}}
        with self.assertRaisesRegex(c.CourtError,'amended substrate'):m.apply_entry(self.case,'time','Count',patch)
        patch['addition']['accounts']={'W9':{'account':{'time:Count:colour':'Red pack.'},
            'divergences':{'time:Count:colour':{'reason':'honest_error','account':'Red pack.'}}}}
        c.validate_foundation(m.apply_entry(self.case,'time','Count',patch))
    def test_independent_sessions_rebuild_after_new_projection_and_restart(self):
        import tempfile
        from pathlib import Path
        from courtroom_backend import DeterministicBackend
        from courtroom_sessions import Orchestrator
        from coverage_fixture import certify
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);case=certify(self.case)
            world=c.initialise(root,'projection',case,allow_mock_rehearsal=True)
            backend=DeterministicBackend(root/'backend');runtime=Orchestrator.start(world,backend)
            state=runtime.state();before=deepcopy(state['sessions'])
            import courtroom_amendments as m
            revised=m.apply_entry(case,'time','Count',{'addition':{'fields':{'facts':{'new':{'text':'NEW_SHARED','channel':'visual'}}}}})
            for who in ('W9','WitnessX','opponent'):runtime._ensure(state,revised,[],who,resume=True)
            for who in ('W9','WitnessX'):self.assertNotEqual(state['sessions'][who]['session_id'],before[who]['session_id'])
            self.assertEqual(state['sessions']['opponent']['session_id'],before['opponent']['session_id'])
            self.assertEqual(len(state['sessions']),len({x['session_id'] for x in state['sessions'].values()}))
    def test_missing_citation_pauses_before_speech_but_preserves_rejected_output(self):
        import tempfile
        from pathlib import Path
        from courtroom_backend import DeterministicBackend
        from courtroom_sessions import Orchestrator
        from coverage_fixture import certify
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);world=c.initialise(root,'citation',certify(self.case),allow_mock_rehearsal=True)
            backend=DeterministicBackend(root/'backend');runtime=Orchestrator.start(world,backend)
            backend.queue('W9',{'text':'UNSUPPORTED_CONFIDENT_ANSWER','data':{}})
            with self.assertRaises(c.CourtError):runtime.turn('W9','dialogue',['player','W9'])
            self.assertEqual([e['type'] for e in c.read_events(world)],['gap'])
            self.assertNotIn('UNSUPPORTED_CONFIDENT_ANSWER',json.dumps(runtime.player_packet()))
            self.assertIn('UNSUPPORTED_CONFIDENT_ANSWER',json.dumps(runtime.state()))
    def test_substrate_amendment_receipt_replays_and_rebuilds_independent_sessions(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from courtroom_backend import DeterministicBackend
        from courtroom_sessions import Orchestrator
        from coverage_fixture import certify
        from test_courtroom_v2 import event
        case=self.case
        case['amendment_envelopes']={'colour':{'target_layer':'time','entry':'Count',
            'topic':'Visible pack colour.','constraints':['Preserve the count.'],'refs':['time:Count:packs']}}
        certify(case)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);world=c.initialise(root,'amended',case,allow_mock_rehearsal=True)
            backend=DeterministicBackend(root/'backend');runtime=Orchestrator.start(world,backend)
            before=runtime.state()['sessions'];original=(world/c.AREA/'case.json').read_bytes()
            runtime.control(event('gap',audience=['player'],detail='Missing colour.',witness='W9'))
            for index,colour in enumerate(('blue','green','yellow'),1):
                backend.queue('amendment_author_'+str(index)+'_time_Count',{'text':'','data':{'candidate':{'addition':{
                    'fields':{'facts':{'colour':{'text':colour+' pack.','channel':'visual'}}}}}}})
            backend.queue('amendment_checker_time_Count',{'text':'','data':{'checks':[
                {'consistent':True,'reason':'Synthetic fixture consistency.'} for _ in range(3)]}})
            with patch('courtroom_rehearsal.rehearse',side_effect=lambda x,*args,**kw:certify(x)['coverage_rehearsal']),patch('secrets.randbelow',return_value=1):
                runtime.amend('colour',confirmed=True)
            self.assertEqual((world/c.AREA/'case.json').read_bytes(),original)
            effective=c.effective_case(case,c.read_events(world))
            self.assertEqual(effective['substrate']['time']['Count']['facts']['colour']['text'],'green pack.')
            self.assertFalse(c.replay(case,c.read_events(world))['paused'])
            after=runtime.state()['sessions']
            for who in ('W9','WitnessX'):self.assertNotEqual(before[who]['session_id'],after[who]['session_id'])
            restarted=Orchestrator.start(world,backend)
            self.assertEqual({k:v['session_id'] for k,v in after.items()},
                             {k:v['session_id'] for k,v in restarted.state()['sessions'].items()})


if __name__=='__main__':unittest.main()
