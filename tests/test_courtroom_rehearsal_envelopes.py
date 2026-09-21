"""Blind probe gaps produce bound envelopes without weakening the readiness gate."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_courtroom_v2 import fixture
import courtroom_v2 as c
import courtroom_rehearsal as r
import courtroom_amendments as a
import courtroom


class RehearsalEnvelopeTests(unittest.TestCase):
    def gap(self, plausible):
        case=fixture();report=case['coverage_rehearsal']
        row=next(x for x in report['witnesses']['W9']['answers'] if x['probe_class']=='examiner')
        row['answer']=''
        for grade in row['assessments'].values():grade.update(bin='gap',refs=[],hearing_plausible=plausible)
        r.refresh_envelopes(case,report);r.seal_report(report)
        return case,report,row

    def test_every_examiner_gap_generates_a_probe_bound_envelope(self):
        case,report,row=self.gap(True)
        self.assertEqual(r.summary(report)['amendment_envelopes'],{'author':0,'rehearsal':1})
        topic,scope=next(iter(report['amendment_envelopes'].items()))
        self.assertEqual(scope['entry'],'W9');self.assertEqual(scope['target_layer'],'witness')
        self.assertEqual(scope['topic'],row['question'])
        self.assertTrue(scope['refs']);self.assertTrue(scope['constraints'])
        self.assertEqual(a.envelope(case,topic)[0],scope)
        with self.assertRaisesRegex(c.CourtError,'plausible'):c.validate_readiness(case)

    def test_envelope_is_not_a_commitment_bypass_and_needs_scoped_consistency(self):
        case,report,row=self.gap(False)
        topic,scope=next(iter(report['amendment_envelopes'].items()))
        with self.assertRaisesRegex(c.CourtError,'consistency scope'):c.validate_readiness(case)
        case['amendment_consistency']={topic:{'W9':scope['refs'],'WitnessX':[]}}
        report['case_hash']=r.case_hash(case);r.seal_report(report)  # Synthetic fixture only.
        c.validate_readiness(case)
        extended=a.extend(case,topic,'Synthetic new detail.')
        self.assertEqual(a.envelope(extended,topic)[0],scope)

    def test_patched_probe_no_longer_produces_a_generated_envelope(self):
        case,report,row=self.gap(False)
        row['answer']='Grounded fixture detail.'
        for grade in row['assessments'].values():grade.update(bin='grounded',refs=['W9.knowledge.0'],hearing_plausible=True)
        r.refresh_envelopes(case,report);r.seal_report(report)
        self.assertEqual(report['amendment_envelopes'],{})
        c.validate_readiness(case)

    def test_altered_generated_constraints_cannot_pass_even_with_resealed_digest(self):
        case,report,row=self.gap(False)
        scope=next(iter(report['amendment_envelopes'].values()))
        scope['constraints']=['Choose an outcome that favours a party.']
        r.seal_report(report)
        with self.assertRaisesRegex(c.CourtError,'probe-derived'):r.validate_report(case)

    def test_author_and_rehearsal_envelopes_are_counted_separately(self):
        case,report,row=self.gap(False)
        case['amendment_envelopes']={'authored_topic':{'target_layer':'witness','entry':'W9',
            'topic':'An authored neutral scope.','constraints':['Preserve fixed history.'],'refs':['W9.knowledge.0']}}
        report['case_hash']=r.case_hash(case);r.refresh_envelopes(case,report);r.seal_report(report)
        self.assertEqual(r.summary(report)['amendment_envelopes'],{'author':1,'rehearsal':1})
        self.assertEqual(len(a.all_envelopes(case)),2)

    def test_human_resolution_of_a_disputed_probe_gap_generates_its_envelope(self):
        case=fixture();report=case['coverage_rehearsal']
        row=next(x for x in report['witnesses']['W9']['answers'] if x['probe_class']=='examiner')
        row['answer']=''
        row['assessments']={'a':{'bin':'gap','refs':[],'hearing_plausible':False},
                            'b':{'bin':'unsupported_invention','refs':[],'hearing_plausible':False}}
        r.refresh_envelopes(case,report);r.seal_report(report)
        self.assertEqual(report['amendment_envelopes'],{})
        r.apply_rulings(case,[{'witness':'W9','answer_id':row['id'],'bin':'gap','refs':[],
            'hearing_plausible':False,'reviewer':'Synthetic human','reason':'Test-only dispute resolution.'}],human_confirmed=True,reviewer_will_not_play=True)
        self.assertEqual(len(case['coverage_rehearsal']['amendment_envelopes']),1)

    def test_rehearsal_cli_cannot_claim_pass_with_missing_consistency_scope(self):
        case,report,_=self.gap(False)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'case.json';out=root/'rehearsed.json'
            source.write_bytes(c.encode(case));stdout=io.StringIO();stderr=io.StringIO()
            with patch.object(r,'rehearse',return_value=report),redirect_stdout(stdout),redirect_stderr(stderr):
                code=courtroom.main(['rehearse','--case',str(source),'--out',str(out),'--root',str(root),
                                     '--backend','mock','--allow-mock'])
            self.assertEqual(code,2);self.assertIn('consistency scope',stderr.getvalue())
            self.assertNotIn('"coverage_pass": true',stdout.getvalue())
            self.assertIn('"amendment_envelopes": {"author": 0, "rehearsal": 1}',stdout.getvalue())
            self.assertTrue(out.exists())


if __name__=='__main__':unittest.main()
