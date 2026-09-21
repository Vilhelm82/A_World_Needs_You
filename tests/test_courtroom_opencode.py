"""Contract and routing tests against an in-memory OpenCode HTTP surface.

These exercise the real adapter/orchestrator but do not claim live provider validation.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_courtroom_v2 import fixture, event
import courtroom_v2 as c
import courtroom_sessions as s
from courtroom_backend import SessionUnavailable
from courtroom_runtime_config import RuntimeConfig, ModelConfig
import courtroom_opencode as o

DENY_RULE={'permission':'*','pattern':'*','action':'deny'}


class FakeTransport:
    def __init__(self):
        self.calls=[];self.sessions={};self.messages={};self.responses=[]
        self.next_id=1;self.duplicate=False;self.bad_response=None
        self.config={'permission':{'*':'deny'},'default_agent':'courtroom',
                     'plugin':[],'mcp':{},'instructions':[],
                     'compaction':{'auto':False,'prune':False},'share':'disabled'}
        self.agents=[{'name':'courtroom','description':'courtroom-guard-v1:test',
                     'permission':[DENY_RULE],'mode':'primary','options':{}}]
        self.mcp={}
        self.health={'healthy':True,'version':'1.18.31'}
        self.providers={'providers':[{'id':'arbitrary','models':{'arbitrary-model':{'id':'arbitrary-model'}}}]}
        self.docs={'openapi':'3.1.0','paths':{
            '/session':{'post':{}}, '/session/{sessionID}':{'get':{},'delete':{}},
            '/session/{sessionID}/message':{'post':{},'get':{}},
            '/session/{sessionID}/abort':{'post':{}},
            **{path:{'get':{}} for path in ['/config','/config/providers','/agent','/mcp']}}}

    def request(self,method,path,body=None,directory=None):
        self.calls.append({'method':method,'path':path,'body':deepcopy(body),'directory':str(directory) if directory is not None else None})
        if path=='/global/health':return deepcopy(self.health)
        if path=='/doc':return deepcopy(self.docs)
        if path=='/config':return deepcopy(self.config)
        if path=='/config/providers':return deepcopy(self.providers)
        if path=='/agent':return deepcopy(self.agents)
        if path=='/mcp':return deepcopy(self.mcp)
        if path=='/session' and method=='POST':
            sid='ses_duplicate' if self.duplicate else 'ses_test_'+str(self.next_id)
            self.next_id+=1
            value={'id':sid,'directory':str(directory),'title':body['title'],
                   'permission':deepcopy(body['permission'])}
            self.sessions.setdefault(sid,value);self.messages.setdefault(sid,[])
            return deepcopy(value)
        pieces=path.strip('/').split('/')
        if len(pieces)>=2 and pieces[0]=='session':
            sid=pieces[1]
            if len(pieces)==2:
                if method=='GET':return deepcopy(self.sessions.get(sid))
                if method=='DELETE':
                    self.sessions.pop(sid,None);self.messages.pop(sid,None);return True
            if len(pieces)==3 and pieces[2]=='abort':return True
            if len(pieces)==3 and pieces[2]=='message':
                if method=='GET':return deepcopy(self.messages.get(sid,[]))
                if method=='POST':
                    user={'info':{'id':'msg_'+str(len(self.messages[sid])),'role':'user'},'parts':deepcopy(body['parts'])}
                    if 'variant' in body:
                        user['info']['model'] = {**body['model'], 'variant': body['variant']}
                    self.messages[sid].append(user)
                    if body.get('noReply'):return deepcopy(user)
                    if self.bad_response is not None:
                        response=deepcopy(self.bad_response)
                    else:
                        content=self.responses.pop(0) if self.responses else {'text':'A contribution.','data':{}}
                        response={'info':{'id':'msg_'+str(len(self.messages[sid])),'role':'assistant','agent':'courtroom'},
                                  'parts':[{'type':'text','text':json.dumps(content)}]}
                    self.messages[sid].append(response)
                    return deepcopy(response)
        raise AssertionError('Unexpected HTTP operation: '+method+' '+path)


class OpenCodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        cfgpath=self.root/'config.json'
        cfgpath.write_text(json.dumps({'backend':'opencode','storage_root':str(self.root/'store'),
            'defaults':{kind:{'provider':'arbitrary','model':'arbitrary-model'}
                        for kind in ('witness','juror','counsel','bench','support')}}))
        self.cfg=RuntimeConfig.load(cfgpath);self.case=fixture()
        self.transport=FakeTransport()
        self.host={'nonce':'test','instance':'persistent-test','version':'1.18.31','base_url':self.cfg.base_url,'plugin_uri':'file:///test/bundled-guard.js'}
        self.hostpatch=patch.object(o,'verify_host',return_value=self.host);self.hostpatch.start()
        self.addCleanup(self.hostpatch.stop)
        self.configure_guard()
        self.backend=o.OpenCodeBackend(self.cfg,self.cfg.resolve(self.case),transport=self.transport)
    def tearDown(self):self.tmp.cleanup()
    def configure_guard(self):
        self.transport.config['plugin']=[self.host['plugin_uri']]
    def start(self):
        self.backend.preflight()
        self.world=c.initialise(self.root,'court',self.case)
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        return self.runtime
    def queue(self,text='Statement',data=None,private=''):
        self.transport.responses.append({'text':text,'data':data or {},'private_reasoning':private})
    def history(self,who):
        sid=self.runtime.state()['sessions'][who]['session_id']
        return json.dumps(self.transport.messages[sid])

    def test_catalog_accepts_arbitrary_provider_model_identifiers(self):
        self.assertEqual(self.backend.list_models(),{('arbitrary','arbitrary-model')})
        self.backend.preflight()
        self.assertEqual(self.transport.sessions,{})

    def test_reasoning_is_role_specific_and_persists_after_restart(self):
        self.transport.providers['providers'][0]['models']['arbitrary-model']['variants'] = {
            'medium': {'effort': 'medium'}, 'high': {'effort': 'high'}}
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'medium')
        self.backend.assignments['WitnessX'] = ModelConfig('arbitrary', 'arbitrary-model', 'high')
        self.backend.preflight()
        handles = [self.backend.create_session(who, 'Identity instructions', {'identity': who})
                   for who in ('W9', 'WitnessX')]
        resumed = o.OpenCodeBackend(self.cfg, self.backend.assignments, transport=self.transport)
        resumed.preflight()
        for handle, level in zip(handles, ('medium', 'high')):
            self.assertEqual(resumed.resume_session(handle.session_id), handle)
            resumed.send(handle.session_id, {'identity': handle.identity, 'action': 'dialogue'})
            calls = [call['body'] for call in self.transport.calls
                     if call['method'] == 'POST' and call['path'] == '/session/' + handle.session_id + '/message']
            self.assertEqual([body['variant'] for body in calls], [level, level])
            self.assertTrue(all('reasoning' not in json.loads(body['parts'][0]['text']) for body in calls))
        self.assertNotEqual(handles[0].session_id, handles[1].session_id)

    def test_unsupported_reasoning_fails_before_session_creation(self):
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'unsupported')
        with self.assertRaisesRegex(c.CourtError, 'reasoning'):
            self.backend.preflight()
        self.assertFalse(any(call['path'] == '/session' and call['method'] == 'POST'
                             for call in self.transport.calls))

    def test_server_cannot_silently_drop_requested_reasoning(self):
        self.transport.providers['providers'][0]['models']['arbitrary-model']['variants'] = {'high': {'effort': 'high'}}
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'high')
        self.backend.preflight()
        original = self.transport.request
        def drop_variant(method, path, body=None, directory=None):
            if body and 'variant' in body:
                body = {key: value for key, value in body.items() if key != 'variant'}
            return original(method, path, body, directory)
        self.transport.request = drop_variant
        with self.assertRaisesRegex(c.CourtError, 'reasoning'):
            self.backend.create_session('W9', 'Witness', {})

    def test_saved_reasoning_cannot_be_altered_behind_controller(self):
        self.transport.providers['providers'][0]['models']['arbitrary-model']['variants'] = {'high': {'effort': 'high'}}
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'high')
        self.backend.preflight()
        handle = self.backend.create_session('W9', 'Witness', {})
        self.transport.messages[handle.session_id][0]['info']['model']['variant'] = 'low'
        with self.assertRaises(SessionUnavailable):
            self.backend.resume_session(handle.session_id)

    def test_empty_and_disabled_variants_are_not_usable_levels(self):
        self.transport.providers['providers'][0]['models']['arbitrary-model']['variants'] = {
            'empty': {}, 'disabled': {'effort': 'high', 'disabled': True}, 'custom-depth': {'effort': 'medium'}}
        self.backend.list_models()
        self.assertEqual(self.backend.reasoning_levels[('arbitrary', 'arbitrary-model')], ('custom-depth',))
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'custom-depth')
        self.backend.preflight()

    def test_reasoning_change_refuses_existing_session(self):
        self.transport.providers['providers'][0]['models']['arbitrary-model']['variants'] = {
            'medium': {'effort': 'medium'}, 'high': {'effort': 'high'}}
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'medium')
        self.backend.preflight()
        handle = self.backend.create_session('W9', 'Witness', {})
        self.backend.assignments['W9'] = ModelConfig('arbitrary', 'arbitrary-model', 'high')
        with self.assertRaisesRegex(c.CourtError, 'assignment changed'):
            self.backend.resume_session(handle.session_id)

    def test_legacy_session_without_reasoning_remains_resumable(self):
        self.backend.preflight()
        handle = self.backend.create_session('W9', 'Witness', {})
        meta = self.backend._load(handle.session_id)
        meta['model'].pop('reasoning', None)
        self.backend._save(meta)
        self.assertEqual(self.backend.resume_session(handle.session_id), handle)
        self.backend.send(handle.session_id, {'identity': 'W9', 'action': 'dialogue'})
        calls = [call for call in self.transport.calls if call['method'] == 'POST'
                 and call['path'] == '/session/' + handle.session_id + '/message']
        self.assertTrue(all('variant' not in call['body'] for call in calls))

    def test_failed_preflight_cleanup_cannot_leave_backend_callable(self):
        original=self.transport.request
        def fail_delete(method,path,body=None,directory=None):
            if method=='DELETE':raise o.TransportError(503)
            return original(method,path,body,directory)
        self.transport.request=fail_delete
        with self.assertRaises(o.TransportError):self.backend.preflight()
        self.assertFalse(self.backend.capabilities.independent_contexts)
        with self.assertRaisesRegex(c.CourtError,'preflight'):
            self.backend.create_session('W9','One witness',{})

    def test_model_content_never_contains_repository_or_sealed_paths(self):
        self.start()
        repo=str(Path(o.__file__).resolve().parents[1])
        for history in self.transport.messages.values():
            payload=json.dumps(history)
            for forbidden in (repo,str(self.world),'.world/court-v2',str(self.cfg.storage_root)):
                self.assertNotIn(forbidden,payload)

    def test_missing_session_api_refuses_startup(self):
        del self.transport.docs['paths']['/session/{sessionID}/message']['get']
        with self.assertRaisesRegex(c.CourtError,'API capability'):self.backend.preflight()
        self.assertFalse(self.transport.sessions)

    def test_provider_failure_reports_status_without_echoing_secrets(self):
        r=self.start()
        self.transport.bad_response={'info':{'id':'msg_2','role':'assistant',
            'error':{'data':{'statusCode':403,'responseBody':'PRIVATE_AUTH_CANARY'}}},'parts':[]}
        with self.assertRaisesRegex(c.CourtError,'provider HTTP 403') as result:
            r.turn('W9','dialogue',['W9','player'])
        self.assertNotIn('PRIVATE_AUTH_CANARY',str(result.exception))

    def test_initial_packet_creates_user_message_without_a_model_turn(self):
        self.start()
        for history in self.transport.messages.values():
            self.assertEqual([m['info']['role'] for m in history],['user'])
        posts=[call for call in self.transport.calls if call['method']=='POST' and call['path'].endswith('/message')]
        self.assertTrue(posts)
        self.assertTrue(all(call['body'].get('noReply') is True for call in posts))

    def test_identity_contexts_and_role_canaries_are_separate(self):
        self.start();entries=self.runtime.state()['sessions']
        self.assertEqual(len(entries),len({e['session_id'] for e in entries.values()}))
        self.assertNotIn('player',entries)
        for who,own,other in [('W9','OWN_MEMORY_679','OTHER_MEMORY_211'),('WitnessX','OTHER_MEMORY_211','OWN_MEMORY_679'),
                              ('opponent','OPPONENT_ONLY_813','CLIENT_SUPPORT_632'),('S1','CLIENT_SUPPORT_632','OPPONENT_ONLY_813')]:
            self.assertIn(own,self.history(who));self.assertNotIn(other,self.history(who))
        for who in entries:
            self.assertNotIn('AUTHOR_TRUTH_NEVER_EXPORT_563',self.history(who))
            self.assertNotIn('PRIVATE_CLIENT_MARKER_819',self.history(who))
        for who in ['judge_merits',*c.jurors(self.case)]:
            self.assertNotIn('EXCLUDED_CONTENT_301',self.history(who))

    def test_private_response_stays_in_own_session_and_restart_preserves_ids(self):
        r=self.start();before=deepcopy(r.state()['sessions'])
        self.queue('Private plan',private='ONLY_OPPONENT_REASONING')
        r.turn('opponent','private',['opponent'])
        self.backend=o.OpenCodeBackend(self.cfg,self.cfg.resolve(self.case),transport=self.transport)
        self.backend.preflight()
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who in before:
            self.assertEqual(before[who]['session_id'],self.runtime.state()['sessions'][who]['session_id'])
            if who!='opponent':self.assertNotIn('ONLY_OPPONENT_REASONING',self.history(who))
        self.assertIn('ONLY_OPPONENT_REASONING',self.history('opponent'))

    def test_provider_receives_deltas_without_repeated_initial_knowledge(self):
        r=self.start();self.queue();r.turn('W9','dialogue',['W9','player'])
        sid=r.state()['sessions']['W9']['session_id']
        user_messages=[m for m in self.transport.messages[sid] if m['info']['role']=='user']
        initial=json.loads(user_messages[0]['parts'][0]['text'])
        first=json.loads(user_messages[1]['parts'][0]['text'])
        self.assertIn('OWN_MEMORY_679',json.dumps(initial))
        self.assertEqual(first['packet'],{})
        r.human(event('dialogue','player',['player','W9'],text='NEW_HEARD_EVENT'))
        self.queue();r.turn('W9','dialogue',['W9','player'])
        message=self.transport.messages[sid][-2]
        packet=json.loads(message['parts'][0]['text'])['packet']
        self.assertIn('NEW_HEARD_EVENT',json.dumps(packet))
        self.assertNotIn('OWN_MEMORY_679',json.dumps(packet))
        self.assertNotIn('documents',packet)

    def test_jury_round_and_ballots_use_individual_provider_sessions(self):
        self.world=c.initialise(self.root,'court',self.case)
        for e in [event('phase',to='opening'),event('phase',to='evidence'),
                  event('publish','bench',sorted(c.CORE|c.jurors(self.case)),document='E1'),
                  event('phase',to='closing'),event('directions','bench',sorted(c.CORE|c.jurors(self.case)),rule='R1'),
                  event('phase',to='decision')]:c.record(self.world,e,_fixture=True)
        self.backend.preflight()
        self.runtime=s.Orchestrator.start(self.world,self.backend)
        for who in sorted(c.jurors(self.case)):self.queue('DELIBERATION_'+who,private='PRIVATE_'+who)
        self.runtime.deliberate_round()
        self.assertIn('DELIBERATION_J01',self.history('J02'))
        self.assertNotIn('PRIVATE_J01',self.history('J02'))
        for who in sorted(c.jurors(self.case)):
            self.queue('Ballot',{'findings':{i:{'status':'not_proved','reason':'BALLOT_'+who,'refs':[]} for i in self.case['issues']}})
        self.runtime.collect_ballots()
        self.assertNotIn('BALLOT_J01',self.history('J02'))
        self.assertNotIn('BALLOT_J02',self.history('J01'))
        self.assertNotIn('BALLOT_',json.dumps(self.runtime.player_packet()))

    def test_role_requests_are_outside_repo_and_tools_are_disabled(self):
        r=self.start();self.queue();r.turn('W9','dialogue',['W9','player'])
        directories={call['directory'] for call in self.transport.calls if call['path'].startswith('/session')}
        self.assertNotIn(None,directories)
        repo=Path(o.__file__).resolve().parents[1]
        for directory in directories:
            self.assertNotIn(repo,Path(directory).parents)
        live_directories={info['directory'] for info in self.transport.sessions.values()}
        self.assertEqual(len(live_directories),len(r.state()['sessions']))
        for call in self.transport.calls:
            if call['method']=='POST' and call['path']=='/session':self.assertEqual(call['body']['permission'],[DENY_RULE])
            if call['method']=='POST' and call['path'].endswith('/message'):
                self.assertEqual(call['body']['agent'],'courtroom')
                self.assertFalse(any(call['body'].get('tools',{}).values()))

    def test_lockdown_changes_fail_before_creating_sessions(self):
        for field,value in [('permission',{'*':'allow'}),('instructions',['leak.md']),('mcp',{'remote':{}}),
                            ('compaction',{'auto':True,'prune':True}),('share','auto'),('plugin',[])]:
            with self.subTest(field=field):
                previous=deepcopy(self.transport.config)
                self.transport.config[field]=value
                try:
                    with self.assertRaises(c.CourtError):self.backend.preflight()
                    self.assertEqual(self.transport.sessions,{})
                finally:self.transport.config=previous

    def test_duplicate_provider_session_ids_are_refused(self):
        self.transport.duplicate=True
        with self.assertRaises(c.CourtError):self.start()

    def test_unavailable_model_fails_before_creating_sessions(self):
        self.transport.providers={'providers':[]}
        with self.assertRaises(c.CourtError):self.backend.preflight()
        self.assertEqual(self.transport.sessions,{})

    def test_mcp_or_unverified_agent_fails_preflight(self):
        self.transport.mcp={'unexpected':{'status':'connected'}}
        with self.assertRaises(c.CourtError):self.backend.preflight()
        self.transport.mcp={}
        self.transport.agents[0]['description']='ordinary assistant'
        with self.assertRaises(c.CourtError):self.backend.preflight()
        self.assertEqual(self.transport.sessions,{})

    def test_changed_provider_session_directory_is_not_resumed(self):
        self.start();sid=self.runtime.state()['sessions']['W9']['session_id']
        self.transport.sessions[sid]['directory']=str(self.root/'another-role')
        with self.assertRaises((SessionUnavailable,c.CourtError)):self.backend.resume_session(sid)

    def test_extra_provider_history_is_never_resumed(self):
        self.start();sid=self.runtime.state()['sessions']['W9']['session_id']
        self.transport.messages[sid].append({'info':{'id':'foreign','role':'user'},'parts':[{'type':'text','text':'UNEXPECTED_HISTORY'}]})
        with self.assertRaises((SessionUnavailable,c.CourtError)):self.backend.resume_session(sid)

    def test_malformed_model_response_cannot_commit(self):
        r=self.start()
        self.transport.bad_response={'info':{'id':'bad','role':'assistant','agent':'courtroom'},'parts':[{'type':'text','text':'not JSON'}]}
        with self.assertRaises(c.CourtError):r.turn('W9','dialogue',['W9','player'])
        self.assertEqual(c.read_events(self.world),[])

    def test_tool_response_parts_cannot_commit(self):
        r=self.start()
        self.transport.bad_response={'info':{'id':'bad','role':'assistant','agent':'courtroom'},
                                    'parts':[{'type':'tool','tool':'read','state':{'status':'completed'}}]}
        with self.assertRaises(c.CourtError):r.turn('W9','dialogue',['W9','player'])
        self.assertEqual(c.read_events(self.world),[])

    def test_auth_environment_is_not_persisted_in_adapter_storage(self):
        with patch.dict('os.environ',{'OPENCODE_SERVER_PASSWORD':'TEST_AUTH_NEVER_STORE'}):
            self.start()
        for path in self.cfg.storage_root.rglob('*'):
            if path.is_file():self.assertNotIn('TEST_AUTH_NEVER_STORE',path.read_text())
        self.assertNotIn('TEST_AUTH_NEVER_STORE',json.dumps(self.transport.calls))
