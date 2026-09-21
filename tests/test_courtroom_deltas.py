"""Exercise delivery deltas through persisted isolated conversations."""
import json
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from test_courtroom_v2 import fixture, event
import courtroom_v2 as c
import courtroom_sessions as s
from courtroom_backend import DeterministicBackend


class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.case=fixture();self.world=c.initialise(self.root,'delta',self.case)
        self.backend=DeterministicBackend(self.root/'backend')
        self.runtime=s.Orchestrator.start(self.world,self.backend)
    def tearDown(self):self.tmp.cleanup()
    def turn(self,who='W9',kind='dialogue',audience=None,text='Reply',data=None):
        self.backend.queue(who,{'text':text,'data':data or {}})
        return self.runtime.turn(who,kind,audience or [who,'player'])
    def history(self,who='W9'):
        return self.backend.inspect(self.runtime.state()['sessions'][who]['session_id'])

    def test_initial_packet_is_not_repeated_on_first_send(self):
        initial=self.history()[0]['packet']
        self.assertIn('role',initial);self.assertIn('documents',initial)
        self.turn()
        self.assertEqual(self.history()[-1]['request']['packet'],{})

    def test_only_new_heard_events_arrive_and_restart_keeps_cursor(self):
        self.runtime.human(event('dialogue','player',['player','W9'],text='FIRST_HEARD'))
        self.turn()
        first=self.history()[-1]['request']['packet']
        self.assertEqual([e['text'] for e in first['events']],['FIRST_HEARD'])
        self.assertNotIn('role',first);self.assertNotIn('documents',first)
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.runtime.human(event('dialogue','player',['player','W9'],text='SECOND_HEARD'))
        self.turn()
        latest=self.history()[-1]['request']['packet']
        self.assertNotIn('FIRST_HEARD',json.dumps(latest))
        self.assertIn('SECOND_HEARD',json.dumps(latest))
        self.assertNotIn('role',latest)

    def test_new_document_is_delivered_once_and_state_changes_are_included(self):
        self.runtime.human(event('disclose','player',['player','W9'],document='E2',to='W9'))
        self.runtime.control(event('phase',to='opening'))
        self.turn()
        delta=self.history()[-1]['request']['packet']
        self.assertEqual(set(delta['documents']),{'E2'})
        self.assertEqual(delta['phase'],'opening')
        self.turn()
        delta=self.history()[-1]['request']['packet']
        self.assertNotIn('documents',delta);self.assertNotIn('phase',delta)

    def test_recovered_commit_advances_delivery_without_resending_input(self):
        self.runtime.human(event('dialogue','player',['player','W9'],text='RECOVERED_INPUT'))
        original=c.render
        def crash(*args):raise OSError('after journal commit')
        c.render=crash
        try:
            with self.assertRaises(OSError):self.turn()
        finally:c.render=original
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.turn()
        self.assertNotIn('RECOVERED_INPUT',json.dumps(self.history()[-1]['request']))

    def test_uncommitted_send_does_not_advance_delivery_and_rebuilds_safely(self):
        before=deepcopy(self.runtime.state()['sessions']['W9'])
        self.runtime.human(event('dialogue','player',['player','W9'],text='PENDING_INPUT'))
        original=self.backend.send
        def crash(sid,request):
            original(sid,request)
            raise OSError('response lost')
        self.backend.send=crash
        try:
            with self.assertRaises(OSError):self.turn(text='UNCOMMITTED_RESPONSE')
        finally:self.backend.send=original
        self.assertEqual(before['delivery'],self.runtime.state()['sessions']['W9']['delivery'])
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertNotEqual(before['session_id'],self.runtime.state()['sessions']['W9']['session_id'])
        self.assertIn('PENDING_INPUT',json.dumps(self.history()[0]))
        self.assertNotIn('UNCOMMITTED_RESPONSE',json.dumps(self.history()))
        self.turn()
        self.assertEqual(self.history()[-1]['request']['packet'],{})

    def test_restriction_rebuild_starts_full_clean_packet_then_sends_delta(self):
        self.runtime.control(event('phase',to='opening'))
        self.runtime.human(event('disclose','player',sorted(c.CORE),document='E1',to='bench'))
        before=self.runtime.state()['sessions']['judge_merits']['session_id']
        self.turn('judge_admissibility','ruling',sorted(c.CORE),data={'effect':'document','document':'E1','status':'excluded','uses':[],'rule':'R5'})
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        self.assertNotEqual(before,self.runtime.state()['sessions']['judge_merits']['session_id'])
        initial=self.history('judge_merits')[0]['packet']
        self.assertIn('role',initial);self.assertNotIn('E1',initial['documents'])
        self.turn('judge_merits','stipulation',sorted(c.CORE|c.jurors(self.case)),data={'agreed_by':['player','opponent']})
        self.assertEqual(self.history('judge_merits')[-1]['request']['packet'],{})

    def test_delta_tracks_updates_and_removals_without_mutating_inputs(self):
        before={'events':[{'id':'T1','text':'old'}], 'documents':{'D':{'text':'old'}},'public_orders':[{'id':'T2','status':'old'}],'pending':{'id':'T1'}}
        after={'events':[{'id':'T1','text':'new'}], 'documents':{},'public_orders':[{'id':'T2','status':'new'}]}
        saved=deepcopy(before)
        delta=s.packet_delta(before,after)
        self.assertEqual(delta['events'],after['events'])
        self.assertEqual(delta['public_orders'],after['public_orders'])
        self.assertEqual(delta['removed'],{'documents':['D'],'fields':['pending']})
        self.assertEqual(before,saved)
