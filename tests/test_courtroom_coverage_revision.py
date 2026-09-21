"""Independent assessment agreement, scoped families and human-only dispute resolution."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import io
import tempfile
from pathlib import Path
import unittest
from test_courtroom_v2 import fixture
import courtroom_v2 as c
import courtroom_rehearsal as r
import courtroom


class CoverageRevisionTests(unittest.TestCase):
    def test_single_grader_report_cannot_pass_revised_gate(self):
        case=fixture()
        case['coverage_rehearsal']['contract']='coverage-v1'
        with self.assertRaisesRegex(c.CourtError,'rehearsal'):c.validate_readiness(case)

    def test_broader_families_have_visible_counts(self):
        report=fixture()['coverage_rehearsal']
        counts=r.summary(report)
        self.assertIn('by_family',counts)
        for family in ('perception','episode_sequence','fact_basis','bias_motive','relationships','prior_statements','documents','off_topic'):
            self.assertGreater(counts['by_family'][family]['total'],0)

    def test_disagreement_blocks_until_digest_bound_human_ruling(self):
        case=fixture();report=case['coverage_rehearsal']
        self.assertIn('report_digest',report)
        row=report['witnesses']['W9']['answers'][0]
        row['assessments']['b']={'bin':'unsupported_invention','refs':[], 'hearing_plausible':True}
        r.seal_report(report)
        with self.assertRaisesRegex(c.CourtError,'human ruling'):c.validate_readiness(case)
        ruling={'witness':'W9','answer_id':row['id'],'bin':'grounded','refs':['W9.knowledge.0'],
                'hearing_plausible':True,'reviewer':'Unit-test human','reason':'Synthetic human review of the disputed fixture.'}
        before=report['report_digest']
        with self.assertRaisesRegex(c.CourtError,'human'):r.apply_rulings(case,[ruling],human_confirmed=False)
        r.apply_rulings(case,[ruling],human_confirmed=True,reviewer_will_not_play=True)
        c.validate_readiness(case)
        self.assertNotEqual(case['coverage_rehearsal']['report_digest'],before)
        case['coverage_rehearsal']['rulings'][0]['reason']='Changed after sealing.'
        with self.assertRaisesRegex(c.CourtError,'digest'):c.validate_readiness(case)

    def test_plausible_blind_probe_gap_is_a_defect_not_a_success(self):
        case=fixture();report=case['coverage_rehearsal']
        probes=[row for row in report['witnesses']['W9']['answers'] if row.get('probe_class')=='examiner']
        self.assertEqual(len(probes),6)
        row=probes[0];row['answer']=''
        for grade in row['assessments'].values():grade.update(bin='gap',refs=[],hearing_plausible=True)
        r.refresh_envelopes(case,report)
        r.seal_report(report)
        with self.assertRaisesRegex(c.CourtError,'plausible'):c.validate_readiness(case)

    def test_blind_examiner_input_excludes_authored_witness_fields(self):
        case=fixture();packet=r.blind_packet(case,'W9')
        text=c.encode(packet).decode()
        for secret in ('OWN_MEMORY_679','OTHER_MEMORY_211','Archive attendant','AUTHOR_TRUTH_NEVER_EXPORT_563','player_side'):
            self.assertNotIn(secret,text)
        self.assertEqual(packet['setting'],'An allegation, not evidence.')

    def test_weighted_template_requires_depth_in_each_family(self):
        from coverage_fixture import certify
        case=fixture();template=deepcopy(r.DEFAULT_TEMPLATE)
        template['perception']['weight']=3
        case['coverage_templates']={'observer':template}
        case['roles']['W9']['coverage_template']='observer'
        certify(case);c.validate_readiness(case)
        rows=case['coverage_rehearsal']['witnesses']['W9']['answers']
        self.assertEqual(sum(row['parent']=='perception' for row in rows),6)
        rows.remove(next(row for row in rows if row['parent']=='perception'))
        r.seal_report(case['coverage_rehearsal'])
        with self.assertRaisesRegex(c.CourtError,'follow-ups'):c.validate_readiness(case)

    def test_partial_rehearsal_survives_failure_but_never_passes(self):
        from courtroom_backend import DeterministicBackend
        case=fixture();snapshots=[]
        with tempfile.TemporaryDirectory() as directory:
            backend=DeterministicBackend(Path(directory))
            backend.queue('W9',{'text':'','data':{'answers':[
                {'id':key,'answer':'Synthetic foundation answer.','gap':False} for key in r.FAMILIES]}})
            with self.assertRaisesRegex(c.CourtError,'no scripted response'):
                r.rehearse(case,backend,checkpoint=snapshots.append)
            case['coverage_rehearsal']=snapshots[-1]
            self.assertEqual(len(snapshots[-1]['witnesses']['W9']['answers']),len(r.FAMILIES))
            with self.assertRaisesRegex(c.CourtError,'incomplete'):c.validate_readiness(case)
            for handle in snapshots[-1]['witnesses']['W9']['sessions'].values():
                self.assertTrue(c.load(backend._path(handle['session_id']))['closed'])

    def test_human_appeal_command_needs_confirmation_and_no_backend(self):
        case=fixture();row=case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
        row['assessments']['b'].update(bin='unsupported_invention',refs=[])
        r.seal_report(case['coverage_rehearsal'])
        ruling={'witness':'W9','answer_id':row['id'],'bin':'grounded','refs':['W9.knowledge.0'],
                'hearing_plausible':True,'reviewer':'Synthetic test reviewer','reason':'Test-only human ruling.'}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'case.json';out=root/'ruled.json';appeal=root/'rulings.json'
            source.write_bytes(c.encode(case));original=source.read_bytes();appeal.write_bytes(c.encode([ruling]))
            args=['coverage-rule','--case',str(source),'--out',str(out),'--rulings',str(appeal),
                  '--root',str(root),'--backend','mock','--allow-mock']
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                self.assertEqual(courtroom.main(args),2)
                self.assertFalse(out.exists())
                self.assertEqual(courtroom.main(args+['--confirm-human-review']),2)
                self.assertFalse(out.exists())
                self.assertEqual(courtroom.main(args+['--confirm-human-review','--reviewer-will-not-play']),0)
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual(out.stat().st_mode&0o777,0o600)
            self.assertFalse((root/'worlds').exists())
            revised=c.load(out);c.validate_readiness(revised)
            counts=r.summary(revised['coverage_rehearsal'])
            self.assertEqual(counts['disputes'],{'unresolved':0,'resolved':1})
            self.assertLess(counts['grader_agreement']['rate'],1)

    def test_ruling_cannot_import_another_witness_source(self):
        case=fixture();row=case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
        row['assessments']['b'].update(bin='unsupported_invention',refs=[])
        r.seal_report(case['coverage_rehearsal']);before=deepcopy(case)
        ruling={'witness':'W9','answer_id':row['id'],'bin':'grounded','refs':['WitnessX.knowledge.0'],
                'hearing_plausible':True,'reviewer':'Synthetic test reviewer','reason':'Invalid reference test.'}
        with self.assertRaisesRegex(c.CourtError,'outside witness packet'):
            r.apply_rulings(case,[ruling],human_confirmed=True,reviewer_will_not_play=True)
        self.assertEqual(case,before)

    def test_cli_keeps_sealed_partial_report_on_backend_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'case.json';out=root/'partial.json';script=root/'script.json'
            source.write_bytes(c.encode(fixture()))
            script.write_bytes(c.encode({'W9':[{'text':'','data':{'answers':[
                {'id':key,'answer':'Synthetic foundation answer.','gap':False} for key in r.FAMILIES]}}]}))
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                code=courtroom.main(['rehearse','--case',str(source),'--out',str(out),'--root',str(root),
                                     '--backend','mock','--allow-mock','--script',str(script)])
            self.assertEqual(code,2)
            self.assertFalse((root/'worlds').exists())
            self.assertEqual(out.stat().st_mode&0o777,0o600)
            partial=c.load(out);r.integrity(partial)
            self.assertFalse(partial['coverage_rehearsal']['complete'])
            self.assertEqual(len(partial['coverage_rehearsal']['witnesses']['W9']['answers']),15)

    def test_persisted_human_ruling_cannot_be_reused_for_a_changed_answer(self):
        case=fixture();row=case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
        row['assessments']['b'].update(bin='unsupported_invention',refs=[])
        r.seal_report(case['coverage_rehearsal'])
        ruling={'witness':'W9','answer_id':row['id'],'bin':'grounded','refs':['W9.knowledge.0'],
                'hearing_plausible':True,'reviewer':'Synthetic test reviewer','reason':'Test-only review.'}
        r.apply_rulings(case,[ruling],human_confirmed=True,reviewer_will_not_play=True)
        case['coverage_rehearsal']['witnesses']['W9']['answers'][0]['answer']='Changed answer.'
        r.seal_report(case['coverage_rehearsal'])
        with self.assertRaisesRegex(c.CourtError,'unchanged grader dispute'):c.validate_readiness(case)


if __name__=='__main__':unittest.main()
