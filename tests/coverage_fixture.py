"""Explicit synthetic assessments for deterministic controller tests, never live coverage."""
from copy import deepcopy
import uuid
import courtroom_v2 as c
import courtroom_rehearsal as r


def certify(case):
    report={'contract':r.CONTRACT,'case_hash':r.case_hash(case),'policy':deepcopy(r.POLICY),
            'mock':True,'backend':'synthetic-test-record','witnesses':{},'rulings':[],'complete':True}
    for who in sorted(c.members(case,'witness')):
        packet=r.packet_for(case,who);_,template=r.template_for(case,who)
        rows=[]
        def add(key,family,question,parent,kind,grade='grounded',plausible=True):
            value={'bin':grade,'refs':[] if grade=='gap' else [who+'.knowledge.0'],'hearing_plausible':plausible}
            rows.append({'id':key,'area':family,'question':question,'parent':parent,'probe_class':kind,
                         'answer':'' if grade=='gap' else 'Artificial fixture answer.',
                         'assessments':{'a':deepcopy(value),'b':deepcopy(value)}})
        for family,question in r.FAMILIES.items():
            kind='off_topic' if family=='off_topic' else 'ordinary'
            add(family,family,question,None,kind,'gap' if kind=='off_topic' else 'grounded',kind!='off_topic')
            for n in range(2*template[family]['weight']):
                add(family+str(n),family,f'Fixture follow-up {family} {n}?',family,kind,
                    'gap' if kind=='off_topic' else 'grounded',kind!='off_topic')
        for n in range(2):add('author_probe_'+str(n),None,f'Unauthored fixture detail {n}?',None,'author','gap',False)
        for n in range(6):add('examiner_probe_'+str(n),('perception','episode_sequence','documents')[n%3],
                            f'Blind hearing probe {n}?',None,'examiner')
        report['witnesses'][who]={'packet_hash':c.digest(c.encode(packet)),'template':template,'answers':rows,
            'sessions':{kind:{'identity':who if kind=='witness' else r.technical_id(kind,who),
                              'session_id':uuid.uuid4().hex,'context_id':uuid.uuid4().hex} for kind in r.SESSION_KINDS}}
    r.refresh_envelopes(case,report)
    case['coverage_rehearsal']=r.seal_report(report)
    return case
