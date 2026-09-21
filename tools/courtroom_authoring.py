"""Sealed shared-world authoring and deterministic identity projections.

Only project() output crosses into a character session. The substrate is not a
prompt. Facet references never confer access to sibling fields or raw entries.
"""
from copy import deepcopy
import json
from pathlib import Path
import courtroom_v2 as c

TEMPLATES=json.loads((Path(__file__).resolve().parents[1]/'modules/courtroom-v2/witness-templates.json').read_text())
LAYERS={'space','time','records','flows'}
REASONS={'lie','honest_error','loyalty','embarrassment','fear','unrelated_concealment'}
KINDS={'never_knew','cannot_recall','approximate','withholds'}
LEGACY={'knowledge','knowledge_basis','background','relevant_activities','memory','motives','uncertainty','coverage_template'}


def enabled(case):return case.get('authoring_version')==2


def fields(value, required, message):
    c.require(isinstance(value,dict) and set(value)==set(required.split()),message)


def text_map(value, label):
    c.require(isinstance(value,dict) and all(c.identifier(k) and c.text(v) for k,v in value.items()),label)


def record_documents(case):
    return {key:{'title':row['title'],'text':row['text'],'provenance':row['display_provenance'],
                 'status':row['status'],'uses':deepcopy(row['uses'])}
            for key,row in case['substrate']['records'].items()}


def compile_case(case):
    """Create checked exhibit caches in a NEW uncommitted value, never mutate input."""
    result=deepcopy(case);result.pop('coverage_rehearsal',None)
    result['documents']=record_documents(result)
    for who,role in result['roles'].items():
        role['documents']=[key for key,row in result['substrate']['records'].items() if who in row['received_by']]
    return result


def scaffold(case):
    """Public empty authoring form; placeholders never establish play readiness."""
    result=deepcopy(case)
    result.pop('truth',None)
    result.update(authoring_version=2,time_scale='REPLACE: define integer timeline ticks',
                  substrate={layer:{} for layer in sorted(LAYERS)},coverage_probes={})
    for who,role in result['roles'].items():
        for key in LEGACY:role.pop(key,None)
        role.update(positions=[],affiliation='neutral',routine={},deltas={},perception_limits={},
                    account={},divergences={},fallibility=[],pressure_points={},manner='REPLACE: pressure expression')
        if role['kind']=='witness':role['template']='lay_eyewitness'
    return compile_case(result)


def envelope(case, who):
    role=case['roles'][who];world=case['substrate'];out={}
    if role['kind'] in {'bench','juror'}:return out
    positions=role['positions']
    for position in positions:
        key=position['location'];space=world['space'][key]
        out['space:'+key+':layout']=json.dumps({k:space[k] for k in ('name','adjacent','distances','sightlines','lighting')},sort_keys=True)
    for key,event in world['time'].items():
        placed=[p['location'] for p in positions if p['start']<=event['at']<=p['end']]
        for fact,value in event['facts'].items():
            channel=value['channel'];allowed=channel=='actor' and who in event['actors']
            for location in placed:
                source=world['space'][location];target=event['location']
                distance=0 if location==target else source['distances'].get(target,float('inf'))
                if channel=='visual':
                    allowed|=(location==target or target in source['sightlines']) and world['space'][target]['lighting']!='dark'
                if channel=='audible':allowed|=distance<=event['audible_range']
            if allowed:out['time:'+key+':'+fact]=value['text']
    for key,row in world['records'].items():
        if who in row['received_by']:
            out['records:'+key+':content']=row['text']
    for key,row in world['flows'].items():
        if who in {row['from'],row['to']}:
            out['flows:'+key+':transfer']=row['description']
    return out


def project(case, who):
    """Return this identity's permitted views. No hidden entry or recipient index."""
    role=case['roles'][who];base=envelope(case,who);visible=deepcopy(base)
    limits={};boundaries={}
    for key,value in role['perception_limits'].items():
        for ref in value['refs']:visible.pop(ref,None)
        limits[key]=deepcopy(value)
        boundaries[key]={'owner':who,'kind':value['kind'],'scope':', '.join(value['refs']),'account':value['account']}
    result={k:deepcopy(role[k]) for k in ('name','kind','routine','deltas','pressure_points','manner','fallibility')}
    result.update(authoring_version=2,envelope=sorted(base),knowledge_basis=sorted(visible),
                  account=deepcopy(role['account']),divergences=deepcopy(role['divergences']),
                  perception_limits=limits,uncertainty=boundaries,sources=visible)
    if role['kind'] in {'bench','juror'}:
        result['sources']={};return result
    # One default boundary describes only lack of personal basis, never hidden facts.
    ignorance='Outside the supplied observations and received information I have no personal basis. This cannot deny an event or invent a memory failure, qualification, or personal history.'
    result['uncertainty']['outside_envelope']={'owner':who,'kind':'never_knew','scope':'Outside my projected observations and receipts','account':ignorance}
    result['sources']['perception:'+who+':outside_envelope']=ignorance
    for key,value in limits.items():result['sources']['perception:'+who+':'+key]=json.dumps(value,sort_keys=True)
    for layer in ('routine','deltas'):
        for key,value in role[layer].items():
            result['sources'][('delta' if layer=='deltas' else layer)+':'+who+':'+key]=json.dumps(value,sort_keys=True)
    for ref,value in role['divergences'].items():
        result['sources']['divergence:'+who+':'+ref]=json.dumps(value,sort_keys=True)
    return result


def validate(case):
    c.require(type(case.get('authoring_version')) is int and enabled(case),'Expected authoring_version 2.')
    c.require(c.text(case.get('time_scale')),'Declare the timeline grain/time_scale.')
    c.require(not any(key in case for key in ('truth','coverage_templates','amendment_consistency')),
              'V2 uses sealed substrate and module-owned templates; remove legacy truth/templates/consistency maps.')
    world=case.get('substrate');fields(world,'space time records flows','Declare all four substrate stores, including empty ones.')
    for layer,store in world.items():
        c.require(isinstance(store,dict) and all(c.identifier(k) and isinstance(v,dict) for k,v in store.items()),'Invalid substrate '+layer+' store.')
    roles=case['roles'];entities=case.get('entities',{})
    text_map(entities,'Named entities need safe IDs and names.')
    c.require(not set(entities)&set(roles),'An entity ID cannot alias a courtroom identity.')
    people=set(roles)|set(entities)
    for key,value in world['space'].items():
        fields(value,'name adjacent distances sightlines lighting access','Invalid space fields.')
        c.require(c.text(value['name']) and value['lighting'] in {'clear','dim','dark'},'Invalid space name/lighting.')
        for field in ('adjacent','sightlines'):
            c.require(c.unique(value[field]) and set(value[field])<=world['space'].keys() and key not in value[field],'Invalid space topology.')
        c.require(c.unique(value['access']) and set(value['access'])<=roles.keys(),'Invalid space access allocation.')
        c.require(isinstance(value['distances'],dict) and set(value['distances'])<=world['space'].keys() and
                  all(type(v) in (int,float) and 0<=v<float('inf') for v in value['distances'].values()),'Invalid space distances.')
        c.require(set(value['adjacent']+value['sightlines'])<=value['distances'].keys(),'Declare distances for adjacency/sightlines.')
    for key,value in world['time'].items():
        fields(value,'at location actors audible_range facts','Invalid timeline entry.')
        c.require(type(value['at']) is int and value['location'] in world['space'],'Timeline needs a tick and location.')
        c.require(c.unique(value['actors']) and value['actors'] and set(value['actors'])<=people,'Timeline actors must be named.')
        c.require(type(value['audible_range']) in (int,float) and 0<=value['audible_range']<float('inf'),'Invalid audible range.')
        c.require(isinstance(value['facts'],dict) and value['facts'],'Timeline entry requires observable facts.')
        for ref,fact in value['facts'].items():
            fields(fact,'text channel','Invalid event facet.')
            c.require(c.identifier(ref) and c.text(fact['text']) and fact['channel'] in {'visual','audible','actor'},'Invalid event facet/channel.')
    for key,value in world['records'].items():
        fields(value,'title text author date recipients received_by provenance alterations display_provenance status uses','Invalid record metadata.')
        c.require(all(c.text(value[k]) for k in ('title','text','date','provenance','display_provenance')) and value['author'] in people,'Record needs author/date/provenance.')
        for field in ('recipients','received_by'):
            c.require(c.unique(value[field]) and set(value[field])<=people,'Invalid record recipient/receipt allocation.')
        c.require(c.strings(value['alterations']) and all(c.text(x) for x in value['alterations']),'Record alterations must be explicitly listed (or empty).')
    for key,value in world['flows'].items():
        fields(value,'kind from to at records description','Invalid flow fields.')
        c.require(value['kind'] in {'money','goods','data','custody'} and value['from'] in people and value['to'] in people and
                  value['from']!=value['to'] and value['at'] in world['time'],'Flow requires named parties and timeline entry.')
        c.require(c.unique(value['records']) and set(value['records'])<=world['records'].keys() and c.text(value['description']),'Invalid flow records/description.')
    for who,role in roles.items():
        c.require(not set(role)&LEGACY,who+': freehand knowledge and legacy witness layers are not allowed.')
        c.require(role.get('affiliation') in c.SIDES[case['config']['case_type']]|{'neutral'},who+': invalid affiliation.')
        positions=role.get('positions');c.require(isinstance(positions,list),who+': declare positions.')
        for index,p in enumerate(positions):
            fields(p,'location start end','Invalid position fields.')
            c.require(p['location'] in world['space'] and who in world['space'][p['location']]['access'],who+': position violates space access.')
            c.require(type(p['start']) is int and type(p['end']) is int and p['start']<=p['end'],'Invalid position interval.')
            c.require(not any(max(p['start'],q['start'])<=min(p['end'],q['end']) for q in positions[:index]),'Overlapping positions are invalid.')
        routine=role.get('routine');c.require(isinstance(routine,dict),who+': declare routine.')
        for key,value in routine.items():
            fields(value,'domain description tools sequence usual_choices','Invalid routine step.')
            c.require(c.identifier(key) and c.text(value['domain']) and c.text(value['description']) and
                      c.strings(value['tools']) and type(value['sequence']) is int and value['sequence']>=0 and
                      c.strings(value['usual_choices']) and value['usual_choices'] and all(c.text(x) for x in value['tools']+value['usual_choices']),
                      'Routine needs concrete procedure, tools, sequence and choices.')
        if role['kind']=='witness':
            c.require(role.get('template') in TEMPLATES,who+': choose a module-owned witness template.')
            c.require(set(TEMPLATES[role['template']]['routine_domains'])<={v['domain'] for v in routine.values()},who+': incomplete template routine domains.')
        for field in ('deltas','perception_limits','account','divergences','pressure_points'):
            c.require(isinstance(role.get(field),dict),who+': declare '+field+'.')
        base=envelope(case,who)
        limited=set()
        for key,value in role['perception_limits'].items():
            fields(value,'refs kind account','Invalid perception limit.')
            c.require(c.identifier(key) and key!='outside_envelope' and c.unique(value['refs']) and value['refs'] and
                      set(value['refs'])<=base.keys(),who+': perception limit must narrow its own envelope.')
            c.require(value['kind'] in KINDS and c.text(value['account']),'Invalid perception boundary kind/account.')
            c.require(not limited&set(value['refs']),'One explicit perception boundary per facet avoids ambiguous accounts.')
            limited.update(value['refs'])
        accounts=role['account'];divergences=role['divergences']
        c.require(set(accounts)<=base.keys() and all(c.text(v) for v in accounts.values()),who+': account source is outside envelope.')
        limit_accounts={ref:v['account'] for v in role['perception_limits'].values() for ref in v['refs']}
        expected={ref for ref,value in accounts.items() if value!=limit_accounts.get(ref,base[ref])}
        c.require(set(divergences)==expected,who+': every account difference needs exactly one divergence.')
        for ref,value in divergences.items():
            fields(value,'reason account','Invalid divergence fields.')
            c.require(value['reason'] in REASONS and value['account']==accounts[ref],who+': divergence needs a declared reason and matching account.')
        for key,value in role['deltas'].items():
            fields(value,'step event description','Invalid routine delta.')
            c.require(c.identifier(key) and value['step'] in routine and value['event'] in base and
                      value['event'].startswith('time:') and c.text(value['description']),'Delta must cite own routine and perceived event.')
        for key,value in role['pressure_points'].items():
            fields(value,'description case_linked','Invalid pressure point.')
            c.require(c.identifier(key) and c.text(value['description']) and type(value['case_linked']) is bool,'Invalid pressure point.')
        c.require(any(not v['case_linked'] for v in role['pressure_points'].values()),who+': at least one innocent pressure point is required.')
        c.require(c.text(role.get('manner')),who+': author manner under pressure.')
        fallibility=role.get('fallibility');c.require(isinstance(fallibility,list),'Declare fallibility.')
        for value in fallibility:
            fields(value,'kind scope','Invalid fallibility.')
            c.require(value['kind'] in {'error','bias'} and c.text(value['scope']),'Invalid error/bias scope.')
        if role['kind'] in {'bench','juror'}:
            c.require(not positions and not base and not accounts and not role['deltas'] and not role['perception_limits'],
                      'Factfinders must have empty historical envelopes.')
        c.require(role.get('documents')==[key for key,row in world['records'].items() if who in row['received_by']],
                  'Role document cache differs from actual record receipts.')
    for side in c.SIDES[case['config']['case_type']]:
        c.require(any(r['kind']=='witness' and r['affiliation']==side and r['fallibility'] for r in roles.values()),
                  'Each side requires a witness with authored fallibility (error or bias).')
    envelopes={who:envelope(case,who) for who in c.members(case,'witness')}
    known={ref for base in (envelope(case,who) for who in roles) for ref in base}
    for issue in case['issues'].values():
        refs=issue.get('substrate_refs')
        c.require(c.unique(refs) and refs and set(refs)<=known,'Issue requires existing substrate anchors.')
        if len(refs)==1 and sum(refs[0] in base for base in envelopes.values())<2:
            c.require(c.text(issue.get('single_source')),'A sole unshared issue anchor requires a deliberate single_source explanation.')
    c.require(case.get('documents')==record_documents(case),'Exhibit cache differs from committed record contents.')
    return case


def amendment_sources(case, scope):
    """Precommitted excerpts only. The live question never determines this scope."""
    layer,entry=scope['target_layer'],scope['entry']
    if layer=='witness':
        c.require(entry in c.members(case,'witness'),'Unknown witness amendment entry.')
        return project(case,entry)['sources']
    c.require(layer in LAYERS and entry in case['substrate'][layer],'Unknown substrate amendment entry.')
    prefix=layer+':'+entry+':'
    return {ref:text for who in case['roles'] for ref,text in project(case,who)['sources'].items() if ref.startswith(prefix)}


def consistency_context(case, scope):
    layer,entry=scope['target_layer'],scope['entry']
    if layer=='witness':
        refs=set(scope['refs']);target={k:deepcopy(case['roles'][entry][k]) for k in ('routine','pressure_points','manner')}
    else:
        target=deepcopy(case['substrate'][layer][entry])
        refs={ref for who in case['roles'] for ref in envelope(case,who) if ref.startswith(layer+':'+entry+':')}
    # Include linked time/record/flow/space entries, not unrelated case truth.
    linked={ref.split(':')[1] for ref in refs if ref.startswith('time:')}
    if layer=='space':linked.update(k for k,v in case['substrate']['time'].items() if v['location']==entry)
    if layer=='flows':linked.add(target['at'])
    if layer=='records':linked.update(v['at'] for v in case['substrate']['flows'].values() if entry in v['records'])
    linked_refs={ref for who in case['roles'] for ref in envelope(case,who) if ref.startswith('time:') and ref.split(':')[1] in linked}
    refs|=linked_refs
    accounts={}
    for who in case['roles']:
        projected=project(case,who);owned=set(envelope(case,who))&refs
        if not owned:continue
        accounts[who]={'knowledge':{ref:text for ref,text in projected['sources'].items() if ref in refs},
                       'limits':{k:v for k,v in projected['perception_limits'].items() if set(v['refs'])&refs},
                       'account':{k:v for k,v in projected['account'].items() if k in refs},
                       'divergences':{k:v for k,v in projected['divergences'].items() if k in refs}}
    return {'target_layer':layer,'entry':entry,'committed_entry':target,'committed_accounts':accounts,
            'linked_events':{k:deepcopy(case['substrate']['time'][k]) for k in linked},'rules':deepcopy(case['rules'])}


def _add(existing, addition):
    if isinstance(existing,dict) and isinstance(addition,dict):
        result=deepcopy(existing)
        for key,value in addition.items():result[key]=_add(result[key],value) if key in result else deepcopy(value)
        return result
    if isinstance(existing,list) and isinstance(addition,list):
        return deepcopy(existing)+[deepcopy(v) for v in addition if v not in existing]
    c.require(existing==addition,'Amendment cannot overwrite committed historical fields.')
    return deepcopy(existing)


def amend_entry(case, layer, entry, patch):
    c.require(isinstance(patch,dict) and set(patch)=={'addition'} and isinstance(patch['addition'],dict),'V2 amendment requires a structured addition.')
    addition=patch['addition']
    c.require(set(addition)<={'fields','accounts'} and isinstance(addition.get('fields'),dict) and addition['fields'],'V2 amendment needs entry fields.')
    result=deepcopy(case);result.pop('coverage_rehearsal',None)
    if layer=='witness':
        c.require(entry in c.members(case,'witness') and set(addition['fields'])<={'routine','pressure_points','manner'} and not addition.get('accounts'),
                  'Witness amendments may change only routine, pressure_points and manner.')
        for key,value in addition['fields'].items():
            result['roles'][entry][key]=deepcopy(value) if key=='manner' else _add(result['roles'][entry][key],value)
    else:
        c.require(layer in LAYERS and entry in result['substrate'][layer],'Unknown substrate amendment layer/entry.')
        result['substrate'][layer][entry]=_add(result['substrate'][layer][entry],addition['fields'])
        accounts=addition.get('accounts',{});c.require(isinstance(accounts,dict),'Invalid bound account amendments.')
        for who,value in accounts.items():
            c.require(who in result['roles'] and isinstance(value,dict) and set(value)<={'account','divergences'},'Invalid account amendment identity/fields.')
            for kind,updates in value.items():
                c.require(isinstance(updates,dict) and all(ref.startswith(layer+':'+entry+':') for ref in updates),
                          'Account changes must reference the amended substrate entry.')
                result['roles'][who][kind].update(deepcopy(updates))
    c.require(result!={k:v for k,v in case.items() if k!='coverage_rehearsal'},'An amendment must add a detail.')
    result=compile_case(result)
    c.validate_foundation(result)
    return result
