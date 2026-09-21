"""Exercise launch isolation and the real JavaScript prompt guard without an LLM."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import courtroom_opencode_host as host
import courtroom_v2 as c


class HostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = SimpleNamespace(storage_root=self.root, base_url='http://127.0.0.1:4096')

    def tearDown(self):
        self.tmp.cleanup()

    def test_environment_replaces_ambient_settings_but_preserves_provider_auth(self):
        incoming = {'OPENCODE_CONFIG_CONTENT': 'unsafe', 'OPENCODE_PURE': '1',
                    'COURTROOM_OPENCODE_AUTH_PLUGIN': 'file:///unselected-plugin.mjs',
                    'OPENCODE_DB': '/user/database', 'OPENCODE_CONFIG': '/user/config',
                    'NODE_OPTIONS': '--require untrusted', 'OPENAI_API_KEY': 'not-a-real-secret',
                    'OPENCODE_SERVER_PASSWORD': 'test-password', 'HOME': '/original/home'}
        with patch.dict(os.environ, incoming, clear=True):
            env = host._environment(self.root, 'a' * 64, self.root / 'guard.mjs', None)
        self.assertNotIn('OPENCODE_CONFIG_CONTENT', env)
        self.assertNotIn('OPENCODE_CONFIG', env)
        self.assertNotIn('OPENCODE_DB', env)
        self.assertNotIn('OPENCODE_PURE', env)
        self.assertNotIn('NODE_OPTIONS', env)
        self.assertEqual(env['OPENAI_API_KEY'], incoming['OPENAI_API_KEY'])
        self.assertEqual(env['HOME'], '/original/home')
        self.assertEqual(env['OPENCODE_TEST_HOME'], str(self.root / 'home'))
        self.assertEqual(env['OPENCODE_DISABLE_PROJECT_CONFIG'], '1')
        self.assertEqual(env['OPENCODE_DISABLE_EXTERNAL_SKILLS'], '1')
        self.assertEqual(env['COURTROOM_OPENCODE_AUTH_PLUGIN'], '')

    def test_auth_plugin_fingerprint_covers_imported_sibling_source(self):
        plugin = self.root/'auth/index.mjs';plugin.parent.mkdir()
        plugin.write_text('export default () => {};')
        sibling = plugin.parent/'transport.mjs';sibling.write_text('export const x = 1;')
        self.config.auth_plugin = plugin
        before = host._auth_plugin(self.config)
        self.assertEqual(before['uri'], plugin.as_uri())
        sibling.write_text('export const x = 2;')
        self.assertNotEqual(before, host._auth_plugin(self.config))
        env = host._environment(self.root, 'a'*64, self.root/'guard.mjs', None, before)
        self.assertEqual(env['COURTROOM_OPENCODE_AUTH_PLUGIN'], plugin.as_uri())

    def test_provider_file_remains_external_and_cannot_load_plugins(self):
        path = self.root / 'provider.json'
        path.write_text(json.dumps({'provider': {'custom': {'options': {'apiKey': 'existing-external-value'}}}}))
        before = path.read_bytes()
        with patch.dict(os.environ, {'COURTROOM_OPENCODE_PROVIDER_CONFIG': str(path)}):
            self.assertEqual(host._provider_config(), path)
            self.assertEqual(path.read_bytes(), before)
            path.write_text(json.dumps({'provider': {}, 'plugin': ['untrusted']}))
            with self.assertRaises(c.CourtError):
                host._provider_config()

    def test_auth_is_referenced_without_copying_and_remote_config_auth_rejected(self):
        data = self.root / 'original'
        source = data / 'opencode/auth.json'
        source.parent.mkdir(parents=True)
        source.write_text(json.dumps({'custom': {'type': 'api', 'key': 'existing-external-value'}}))
        destination = self.root / 'private'
        with patch.dict(os.environ, {'XDG_DATA_HOME': str(data)}):
            host._auth_link(destination)
            target = destination / 'data/opencode/auth.json'
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), source)
            source.write_text(json.dumps({'provider': {'type': 'wellknown', 'token': 'unused'}}))
            with self.assertRaisesRegex(c.CourtError, 'remote configuration'):
                host._auth_link(destination)

    def test_manifest_validates_guard_config_process_and_instance(self):
        root = self.root / 'host'
        (root / 'config').mkdir(mode=0o700, parents=True)
        os.chmod(root, 0o700)
        plugin = root / 'config/courtroom-guard.mjs'
        plugin.write_bytes(host.GUARD.read_bytes())
        os.chmod(plugin, 0o600)
        settings = root / 'config/opencode.json'
        host._write(settings, host._settings(plugin.as_uri()))
        host._write(root / 'identity.json', {'instance': 'fixed-id'})
        manifest = {'protocol': host.PROTOCOL, 'version': host.VERSION,
                    'base_url': self.config.base_url, 'pid': 1234, 'nonce': 'a' * 64,
                    'host_root': str(root), 'instance': 'fixed-id', 'plugin_uri': plugin.as_uri(),
                    'plugin_sha256': host._digest(plugin), 'config_sha256': host._digest(settings)}
        host._write(root / 'manifest.json', manifest)
        with patch.object(host, '_running', return_value=True):
            self.assertEqual(host.verify_host(self.config)['instance'], 'fixed-id')
            plugin.write_text('tampered')
            with self.assertRaisesRegex(c.CourtError, 'guard has changed'):
                host.verify_host(self.config)
            plugin.write_bytes(host.GUARD.read_bytes())
            settings.write_text('{}')
            with self.assertRaisesRegex(c.CourtError, 'configuration has changed'):
                host.verify_host(self.config)
            host._write(settings, host._settings(plugin.as_uri()))
        with patch.object(host, '_running', return_value=False):
            with self.assertRaisesRegex(c.CourtError, 'not running'):
                host.verify_host(self.config)

    def test_host_rejects_remote_https_and_proxy_paths(self):
        for url in ('http://192.168.1.2:4096', 'https://localhost:4096', 'http://localhost:4096/proxy'):
            with self.subTest(url=url), self.assertRaises(c.CourtError):
                host._endpoint(SimpleNamespace(base_url=url))

    @unittest.skipUnless(shutil.which('node'), 'Node is required to test the actual guard module')
    def test_actual_guard_wipes_ambient_context_and_blocks_tools_and_auxiliary_calls(self):
        script = r'''
import assert from 'node:assert/strict';
const module = await import(process.env.TEST_GUARD_URI);
assert.deepEqual(Object.keys(module), ['CourtroomGuard']);
const hooks = await module.CourtroomGuard();
const config = JSON.parse(process.env.TEST_CONFIG);
const system = config.agent.courtroom.prompt;
await hooks.config(config);
assert.equal(config.agent.courtroom.description, 'courtroom-guard-v1:' + process.env.COURTROOM_OPENCODE_NONCE);
assert.deepEqual(Object.keys(config.agent.courtroom.permission), ['external_directory', '*']);
assert.equal(config.agent.courtroom.permission.external_directory[process.env.XDG_DATA_HOME + '/opencode/tool-output/*'], 'deny');
const output = {system: ['ambient workspace secret', 'AGENTS.md', 'MCP server instructions']};
await hooks['experimental.chat.system.transform']({}, output);
assert.deepEqual(output.system, [system]);
const message = {agent:'courtroom',system,tools:{'*':false}};
await hooks['chat.message']({}, {message,parts:[{type:'text',text:'allowed engine packet'}]});
await assert.rejects(hooks['chat.message']({}, {message,parts:[{type:'file',url:'file:///secret'}]}));
const params = {options:{instructions:'ambient provider system'}};
await hooks['chat.params']({agent:'courtroom',message}, params);
assert.equal(params.options.instructions, system);
await assert.rejects(hooks['chat.params']({agent:'title',message},params));
await assert.rejects(hooks['tool.execute.before']({},{}));
await assert.rejects(hooks['command.execute.before']({},{}));
await assert.rejects(hooks['experimental.session.compacting']({},{}));
const permission = {status:'allow'};
await hooks['permission.ask']({}, permission);
assert.equal(permission.status,'deny');
config.plugin.push('untrusted');
await assert.rejects(hooks.config(config));
'''
        env = dict(os.environ, COURTROOM_OPENCODE_NONCE='a' * 64,
                   XDG_DATA_HOME=str(self.root / 'data'),
                   COURTROOM_OPENCODE_GUARD_URI=host.GUARD.as_uri(),
                   TEST_GUARD_URI=host.GUARD.as_uri(),
                   TEST_CONFIG=json.dumps(host._settings(host.GUARD.as_uri())))
        result = subprocess.run(['node', '--input-type=module', '-e', script],
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Node is required to test the actual guard module')
    def test_guard_accepts_auth_only_and_rejects_added_agent_hooks(self):
        valid = self.root/'valid.mjs'
        valid.write_text("export default async () => ({auth:{provider:'custom',methods:[{type:'oauth',label:'Browser login'}]}});")
        unsafe = self.root/'unsafe.mjs'
        unsafe.write_text("export default async () => ({auth:{provider:'custom',methods:[]},tool:{}});")
        script = r'''
import assert from 'node:assert/strict';
const {CourtroomGuard} = await import(process.env.TEST_GUARD_URI);
process.env.COURTROOM_OPENCODE_AUTH_PLUGIN = process.env.TEST_VALID;
const hooks = await CourtroomGuard({client:{}});
assert.equal(hooks.auth.provider, 'custom');
const output = {system:['UNALLOCATED_SECRET']};
await hooks['experimental.chat.system.transform']({},output);
assert.ok(!output.system.join('').includes('UNALLOCATED_SECRET'));
await assert.rejects(hooks['tool.execute.before']({},{}));
process.env.COURTROOM_OPENCODE_AUTH_PLUGIN = process.env.TEST_UNSAFE;
await assert.rejects(CourtroomGuard({client:{}}));
'''
        env = dict(os.environ, COURTROOM_OPENCODE_NONCE='a'*64,
                   COURTROOM_OPENCODE_GUARD_URI=host.GUARD.as_uri(), TEST_GUARD_URI=host.GUARD.as_uri(),
                   TEST_VALID=valid.as_uri(), TEST_UNSAFE=unsafe.as_uri())
        result = subprocess.run(['node','--input-type=module','-e',script], env=env,
                                capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
