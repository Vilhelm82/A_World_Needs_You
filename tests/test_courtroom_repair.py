"""A paused case cannot resume on a bare controller command."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_courtroom_v2 import fixture, event
import courtroom_v2 as c
import courtroom_sessions as s
from courtroom_backend import DeterministicBackend


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.case = fixture()
        self.world = c.initialise(self.root,'repair',self.case,allow_mock_rehearsal=True)
        self.backend = DeterministicBackend(self.root/'sessions')
        self.runtime = s.Orchestrator.start(self.world,self.backend)
        self.backend.queue('W9', {'text':'','data':{},'authoring_gap':'Never authored detail.'})
        with self.assertRaises(c.CourtError):
            self.runtime.turn('W9','dialogue',['player','W9'])

    def tearDown(self):
        self.tmp.cleanup()

    def test_omitted_committed_source_can_be_delivered_without_backfilling(self):
        other = c.initialise(self.root,'omitted',self.case,allow_mock_rehearsal=True)
        real_packet = s.routed_packet
        def missing(case, events, who):
            packet = real_packet(case, events, who)
            if who == 'W9': packet['role']['knowledge'] = []
            return packet
        # Simulate an already-committed runtime with a packet-delivery defect.
        with patch.object(s, 'routed_packet', side_effect=missing), patch.object(c, 'validate_readiness', return_value=self.case):
            runtime = s.Orchestrator.start(other,self.backend)
            self.backend.queue('W9', {'text':'','data':{},'authoring_gap':'Missing own observation.'})
            with self.assertRaises(c.CourtError): runtime.turn('W9','dialogue',['player','W9'])
        runtime.control(event('repair',audience=['player'],resolution={
            'kind':'delivery_repair','fault':'T0001','witness':'W9','refs':['W9.knowledge.0']}))
        self.assertFalse(c.replay(self.case,c.read_events(other))['paused'])
        self.assertEqual(c.read_case(other), self.case)

    def test_bare_repair_rejected_and_case_stays_paused(self):
        with self.assertRaisesRegex(c.CourtError, 'resolution'):
            self.runtime.control(event('repair', audience=['player']))
        self.assertTrue(c.replay(self.case,c.read_events(self.world))['paused'])

    def test_another_witness_source_cannot_resolve_gap(self):
        with self.assertRaisesRegex(c.CourtError, 'permitted'):
            self.runtime.control(event('repair', audience=['player'], resolution={
                'kind':'supported_resolution','fault':'T0001','witness':'W9','refs':['WitnessX.knowledge.0']}))

    def test_already_delivered_source_is_not_a_delivery_repair(self):
        with self.assertRaisesRegex(c.CourtError, 'omitted'):
            self.runtime.control(event('repair', audience=['player'], resolution={
                'kind':'delivery_repair','fault':'T0001','witness':'W9','refs':['W9.knowledge.0']}))

    def test_supported_resolution_is_recorded_without_exposing_sources_to_other_roles(self):
        self.runtime.control(event('repair', audience=['player'], resolution={
            'kind':'supported_resolution','fault':'T0001','witness':'W9','refs':['W9.knowledge.0']}))
        events = c.read_events(self.world)
        self.assertFalse(c.replay(self.case,events)['paused'])
        self.assertEqual(events[-1]['data']['resolution']['kind'],'supported_resolution')
        for who in ('WitnessX','opponent','judge_merits','J01'):
            self.assertFalse(any(e['type']=='repair' for e in s.routed_packet(self.case,events,who)['events']))


if __name__=='__main__':unittest.main()
