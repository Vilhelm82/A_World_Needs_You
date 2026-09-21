"""The commitment gate must require a real, case-bound coverage exercise."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from test_courtroom_v2 import fixture
import courtroom_v2 as c
import courtroom_rehearsal as r


class CoverageGateTests(unittest.TestCase):
    def test_unrehearsed_case_cannot_be_committed(self):
        case = fixture()
        case.pop('coverage_rehearsal', None)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(c.CourtError, 'rehearsal'):
                c.initialise(Path(directory), 'unrehearsed', case, allow_mock_rehearsal=True)
            self.assertFalse((Path(directory) / 'worlds').exists())

    def test_case_change_invalidates_rehearsal(self):
        case = fixture()
        case['roles']['W9']['background']['occupation'] = 'Newly changed profession.'
        with self.assertRaisesRegex(c.CourtError, 'rehearsal'):
            c.validate_readiness(case)


    def test_any_ordinary_gap_or_invention_blocks_commitment(self):
        for grade in ('gap', 'unsupported_invention'):
            case = fixture()
            row = case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
            row['answer']='' if grade=='gap' else 'An invented licence.'
            for assessment in row['assessments'].values():assessment.update(bin=grade,refs=[])
            r.seal_report(case['coverage_rehearsal'])
            with self.subTest(grade=grade), self.assertRaisesRegex(c.CourtError, 'blocks commitment'):
                c.validate_readiness(case)

    def test_probe_invention_is_not_hidden_in_the_ordinary_denominator(self):
        case = fixture()
        rows = case['coverage_rehearsal']['witnesses']['W9']['answers']
        row=next(row for row in rows if row['probe_class']=='author')
        row['answer']='Invented probe answer.'
        for assessment in row['assessments'].values():assessment.update(bin='unsupported_invention',refs=[])
        r.seal_report(case['coverage_rehearsal'])
        with self.assertRaisesRegex(c.CourtError, 'invention'):
            c.validate_readiness(case)

    def test_missing_followup_and_foreign_source_rejected(self):
        case = fixture()
        rows = case['coverage_rehearsal']['witnesses']['W9']['answers']
        del rows[1]
        r.seal_report(case['coverage_rehearsal'])
        with self.assertRaisesRegex(c.CourtError, 'follow-ups'):
            c.validate_readiness(case)
        case = fixture()
        row=case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
        for assessment in row['assessments'].values():assessment['refs']=['WitnessX.knowledge.0']
        r.seal_report(case['coverage_rehearsal'])
        with self.assertRaisesRegex(c.CourtError, 'outside witness packet'):
            c.validate_readiness(case)

    def test_mock_report_cannot_commit_for_live_play(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(c.CourtError, 'Mock rehearsal'):
                c.initialise(Path(directory), 'live', fixture())
            self.assertFalse((Path(directory) / 'worlds').exists())

    def test_runner_uses_independent_sessions_and_keeps_practice_out_of_play(self):
        import json
        from courtroom_backend import DeterministicBackend
        case=fixture()
        case['coverage_probes']={who:['Unwritten exact minute?','Unwritten childhood street?'] for who in c.members(case,'witness')}
        with tempfile.TemporaryDirectory() as directory:
            backend=DeterministicBackend(Path(directory))
            for who in sorted(c.members(case,'witness')):
                def replies(ids):
                    return {'text':'','data':{'answers':[{'id':key,'answer':'I count stock.','gap':False} for key in ids]}}
                backend.queue(who,replies(r.FAMILIES))
                backend.queue(r.technical_id('examiner',who),{'text':'','data':{'questions':[
                    {'area':area,'question':f'Natural {area} follow-up {i}?'} for area in r.FAMILIES for i in range(2)]}})
                backend.queue(who,replies([f'followup_{i}' for i in range(30)]))
                backend.queue(who,{'text':'','data':{'answers':[
                    {'id':f'author_probe_{i}','answer':'','gap':True} for i in range(2)]}})
                backend.queue(r.technical_id('blind_examiner',who),{'text':'','data':{'questions':[
                    {'area':('perception','episode_sequence','documents')[i%3],'question':f'Blind question {i}?'} for i in range(6)]}})
                backend.queue(who,replies([f'examiner_probe_{i}' for i in range(6)]))
                grades=[{'id':key,'bin':'grounded','refs':[who+'.background.occupation'],'hearing_plausible':True}
                        for key in [*r.FAMILIES,*[f'followup_{i}' for i in range(30)],*[f'examiner_probe_{i}' for i in range(6)]]]
                grades += [{'id':f'author_probe_{i}','bin':'gap','refs':[],'hearing_plausible':False} for i in range(2)]
                for grader in ('a','b'):
                    backend.queue(r.technical_id('grader_'+grader,who),{'text':'','data':{'assessments':grades}})
            report=r.rehearse(case,backend)
            case['coverage_rehearsal']=report;r.validate_report(case)
            counts=r.summary(report)
            self.assertEqual(counts['ordinary'],{'grounded':84})
            self.assertEqual(counts['author_probes'],{'gap':4})
            self.assertEqual(counts['examiner_probes'],{'grounded':12})
            self.assertEqual(counts['off_topic'],{'grounded':6})
            self.assertEqual(counts['grader_agreement'],{'agreed':106,'total':106,'rate':1.0})
            from courtroom_sessions import routed_packet
            self.assertNotIn('Natural occupation',json.dumps(routed_packet(case,[],'W9')))
            for who,exercise in report['witnesses'].items():
                graders=[backend.inspect(exercise['sessions']['grader_'+name]['session_id']) for name in ('a','b')]
                self.assertEqual(graders[0][0]['packet'],graders[1][0]['packet'])
                self.assertEqual(graders[0][1]['request']['task'],graders[1][1]['request']['task'])
                self.assertNotIn('assessments',json.dumps(graders[0][1]['request']))
                self.assertNotEqual(exercise['sessions']['grader_a']['session_id'],exercise['sessions']['grader_b']['session_id'])
                for kind,handle in exercise['sessions'].items():
                    history=json.dumps(backend.inspect(handle['session_id']))
                    self.assertNotIn('AUTHOR_TRUTH_NEVER_EXPORT_563',history)
                    self.assertNotIn('OTHER_MEMORY_211' if who=='W9' else 'OWN_MEMORY_679',history)
                    if kind=='blind_examiner':self.assertNotIn('Archive attendant',history)
                    self.assertTrue(c.load(backend._path(handle['session_id']))['closed'])


if __name__ == '__main__':
    unittest.main()
