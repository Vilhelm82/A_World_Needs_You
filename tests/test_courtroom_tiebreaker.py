"""Disputes use a peer-blind third grader; players never need sealed human review."""
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest
from test_courtroom_v2 import fixture
import courtroom_v2 as c
import courtroom_rehearsal as r
from courtroom_backend import DeterministicBackend


class TiebreakerTests(unittest.TestCase):
    def run_rehearsal(self, directory, third_bin='grounded', plausible_only=False):
        case=fixture();case['roles'].pop('WitnessX');case.pop('coverage_rehearsal')
        case['coverage_probes']={'W9':['Unwritten detail one?','Unwritten detail two?']}
        backend=DeterministicBackend(Path(directory))
        def answers(ids):return {'text':'','data':{'answers':[{'id':key,'answer':'Fixture answer.','gap':False} for key in ids]}}
        backend.queue('W9',answers(r.FAMILIES))
        backend.queue(r.technical_id('examiner','W9'),{'text':'','data':{'questions':[
            {'area':area,'question':f'Follow-up {area} {i}?'} for area in r.FAMILIES for i in range(2)]}})
        backend.queue('W9',answers([f'followup_{i}' for i in range(30)]))
        backend.queue('W9',{'text':'','data':{'answers':[{'id':f'author_probe_{i}','answer':'','gap':True} for i in range(2)]}})
        backend.queue(r.technical_id('blind_examiner','W9'),{'text':'','data':{'questions':[
            {'area':('perception','documents','limits')[i%3],'question':f'Blind probe {i}?'} for i in range(6)]}})
        backend.queue('W9',answers([f'examiner_probe_{i}' for i in range(6)]))
        grades=[{'id':key,'bin':'grounded','refs':['W9.knowledge.0'],'hearing_plausible':True}
                for key in [*r.FAMILIES,*[f'followup_{i}' for i in range(30)],*[f'examiner_probe_{i}' for i in range(6)]]]
        grades += [{'id':f'author_probe_{i}','bin':'gap','refs':[],'hearing_plausible':False} for i in range(2)]
        for grader in ('a','b','c'):
            values=deepcopy(grades)
            if grader=='b' and not plausible_only:values[0].update(bin='authored_uncertainty',refs=['boundary:W9:sounds'])
            if grader=='a' and plausible_only:values[0]['hearing_plausible']=False
            if grader=='c':values[0].update(bin=third_bin,refs=[] if third_bin=='unsupported_invention' else ['W9.knowledge.0'])
            backend.queue(r.technical_id('grader_'+grader,'W9'),{'text':'','data':{'assessments':values}})
        report=r.rehearse(case,backend);case['coverage_rehearsal']=report
        return case,backend

    def test_majority_resolves_dispute_with_same_frozen_input_and_separate_session(self):
        with tempfile.TemporaryDirectory() as directory:
            case,backend=self.run_rehearsal(directory);r.validate_report(case)
            report=case['coverage_rehearsal'];exercise=report['witnesses']['W9']
            histories=[backend.inspect(exercise['sessions']['grader_'+x]['session_id']) for x in ('a','b','c')]
            for history in histories[1:]:
                self.assertEqual(history[0]['packet'],histories[0][0]['packet'])
                self.assertEqual(history[1]['request']['task'],histories[0][1]['request']['task'])
            self.assertNotIn('assessments',histories[2][1]['request']['task']['answers'][0])
            self.assertEqual(report['rulings'],[])
            counts=r.summary(report)['by_witness']['W9']
            self.assertEqual(counts['tiebreakers'],1)
            self.assertEqual(counts['three_way_splits'],0)
            self.assertEqual(counts['grader_agreement'],{'agreed':52,'total':53,'rate':52/53})
            self.assertTrue(c.load(backend._path(exercise['sessions']['grader_c']['session_id']))['closed'])

    def test_three_way_split_returns_sealed_author_patch_target_and_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            case,backend=self.run_rehearsal(directory,'unsupported_invention')
            report=case['coverage_rehearsal']
            with self.assertRaisesRegex(c.CourtError,'three-way'):c.validate_readiness(case)
            self.assertEqual(r.summary(report)['by_witness']['W9']['three_way_splits'],1)
            target=report['patch_targets'][0]
            self.assertEqual(target['entry'],'W9')
            self.assertEqual(target['answer_id'],'occupation')
            self.assertEqual(target['reason'],'three_way_split')
            handoff=r.author_patch_packet(case,'W9')
            self.assertEqual(handoff['patch_targets'],report['patch_targets'])
            self.assertNotIn('AUTHOR_TRUTH_NEVER_EXPORT_563',c.encode(handoff).decode())
            case['roles']['W9']['knowledge'].append('Author patch makes the source explicit.')
            with self.assertRaisesRegex(c.CourtError,'stale'):r.validate_report(case)

    def test_hearing_plausibility_is_also_decided_by_majority(self):
        with tempfile.TemporaryDirectory() as directory:
            case,_=self.run_rehearsal(directory,plausible_only=True)
            report=case['coverage_rehearsal'];row=report['witnesses']['W9']['answers'][0]
            self.assertFalse(r.agreed(row));self.assertTrue(r.decision(report,'W9',row)['hearing_plausible'])
            r.validate_report(case)

    def test_human_review_is_rejected_without_nonplaying_reviewer_flag(self):
        case=fixture();row=case['coverage_rehearsal']['witnesses']['W9']['answers'][0]
        row['assessments']['b'].update(bin='unsupported_invention',refs=[]);r.seal_report(case['coverage_rehearsal'])
        ruling={'witness':'W9','answer_id':row['id'],'bin':'grounded','refs':['W9.knowledge.0'],
                'hearing_plausible':True,'reviewer':'Test reviewer','reason':'Synthetic ruling.'}
        with self.assertRaisesRegex(c.CourtError,'will not play'):
            r.apply_rulings(case,[ruling],human_confirmed=True)


if __name__=='__main__':unittest.main()
