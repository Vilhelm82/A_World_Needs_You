"""Runtime assignments stay separate from case facts and contain no credentials."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import courtroom_v2 as c
from courtroom_runtime_config import ModelConfig, RuntimeConfig
from test_courtroom_v2 import fixture


class RuntimeConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / 'runtime.json'
        self.case = fixture()

    def tearDown(self):
        self.tmp.cleanup()

    def config(self, **changes):
        data = {'backend': 'opencode', 'defaults': {
            kind: {'provider': 'custom-provider', 'model': kind + '-model'}
            for kind in ('witness', 'juror', 'counsel', 'bench', 'support')}, 'roles': {}}
        data.update(changes)
        self.path.write_text(json.dumps(data), encoding='utf-8')
        return RuntimeConfig.load(self.path)

    def test_defaults_resolve_every_identity_without_mutating_case(self):
        before = deepcopy(self.case)
        cfg = self.config()
        assignments = cfg.resolve(self.case)
        self.assertEqual(set(assignments), {'opponent', 'W9', 'WitnessX', 'S1',
                         'J01', 'J02', 'J03', 'judge_admissibility', 'judge_merits'})
        for who, kind in [('W9', 'witness'), ('J01', 'juror'), ('opponent', 'counsel'),
                          ('S1', 'support'), ('judge_admissibility', 'bench'), ('judge_merits', 'bench')]:
            self.assertEqual(assignments[who], ModelConfig('custom-provider', kind + '-model'))
        self.assertEqual(self.case, before)
        self.assertEqual(cfg.backend, 'opencode')
        self.assertEqual(cfg.base_url, 'http://127.0.0.1:4096')
        self.assertEqual(cfg.storage_root, Path.home() / '.local/state/courtroom/opencode')

    def test_identity_and_judicial_overrides_are_independent(self):
        roles = {'W9': {'provider': 'local/experimental', 'model': 'weights v2:Q4'},
                 'judge_merits': {'provider': 'arbitrary-provider', 'model': 'different-model'}}
        assignments = self.config(roles=roles).resolve(self.case)
        self.assertEqual(assignments['W9'], ModelConfig('local/experimental', 'weights v2:Q4'))
        self.assertEqual(assignments['WitnessX'], ModelConfig('custom-provider', 'witness-model'))
        self.assertEqual(assignments['judge_merits'], ModelConfig('arbitrary-provider', 'different-model'))
        self.assertEqual(assignments['judge_admissibility'], ModelConfig('custom-provider', 'bench-model'))

    def test_all_identities_may_be_configured_without_kind_defaults(self):
        roles = {who: {'provider': 'p', 'model': 'm'} for who in
                 (set(self.case['roles']) - {'bench', 'player'}) | {'judge_admissibility', 'judge_merits'}}
        self.assertEqual(len(self.config(defaults={}, roles=roles).resolve(self.case)), len(roles))

    def test_missing_kind_fails_with_identity_and_no_partial_assignments(self):
        cfg = self.config(defaults={'bench': {'provider': 'p', 'model': 'm'}})
        with self.assertRaisesRegex(c.CourtError, 'Missing model assignment'):
            cfg.resolve(self.case)

    def test_unknown_human_and_unsplit_bench_overrides_fail(self):
        for identity in ('absent', 'player', 'bench'):
            with self.subTest(identity=identity):
                cfg = self.config(roles={identity: {'provider': 'p', 'model': 'm'}})
                with self.assertRaisesRegex(c.CourtError, 'Unknown runtime identity'):
                    cfg.resolve(self.case)

    def test_unknown_role_kinds_and_reserved_case_ids_fail(self):
        for mutation in ('kind', 'reserved'):
            with self.subTest(mutation=mutation):
                case = deepcopy(self.case)
                if mutation == 'kind':
                    case['roles']['W9']['kind'] = 'other'
                else:
                    case['roles']['judge_merits'] = {'kind': 'bench'}
                with self.assertRaises(c.CourtError):
                    self.config().resolve(case)

    def test_catalog_checks_provider_and_model_as_a_pair(self):
        cfg = self.config()
        assignments = cfg.resolve(self.case)
        catalog = {(m.provider, m.model) for m in assignments.values()}
        cfg.validate_models(assignments, catalog)
        catalog.remove(('custom-provider', 'witness-model'))
        catalog.add(('wrong-provider', 'witness-model'))
        with self.assertRaisesRegex(c.CourtError, 'Unavailable model assignments.*W9.*WitnessX'):
            cfg.validate_models(assignments, catalog)

    def test_loopback_addresses_supported(self):
        for url in ('http://localhost:4096', 'http://127.8.2.1:4096/', 'http://[::1]:4096'):
            with self.subTest(url=url):
                self.assertEqual(self.config(base_url=url).base_url, url.rstrip('/'))

    def test_remote_access_requires_explicit_boolean_option(self):
        for url in ('http://192.168.1.42:4096', 'https://models.example.test', 'http://0.0.0.0:4096'):
            with self.subTest(url=url):
                with self.assertRaisesRegex(c.CourtError, 'loopback'):
                    self.config(base_url=url)
                self.assertEqual(self.config(base_url=url, allow_remote=True).base_url, url)
        with self.assertRaises(c.CourtError):
            self.config(allow_remote='true')

    def test_urls_cannot_embed_credentials_or_unsupported_components(self):
        urls = ('http://name:secret@localhost:4096', 'http://localhost:4096/?token=secret',
                'http://localhost:4096/#secret', 'file:///tmp/server', 'localhost:4096',
                'http://localhost:bad', 'http://localhost:70000', 'http://localhost:4096\n')
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaises(c.CourtError) as raised:
                    self.config(base_url=url)
                self.assertNotIn('secret', str(raised.exception))

    def test_storage_is_absolute_and_outside_repository(self):
        storage = self.root / 'state'
        self.assertEqual(self.config(storage_root=str(storage)).storage_root, storage)
        for value in ('relative/state', str(ROOT), str(ROOT / '.runtime')):
            with self.subTest(value=value):
                with self.assertRaises(c.CourtError):
                    self.config(storage_root=value)
        link = self.root / 'alias'
        link.symlink_to(ROOT, target_is_directory=True)
        with self.assertRaises(c.CourtError):
            self.config(storage_root=str(link / 'runtime'))
        self.assertFalse(storage.exists(), 'Loading config must not create storage.')

    def test_credentials_rejected_at_every_level_without_echoing_values(self):
        for key in ('credential', 'credentials', 'auth', 'authorization', 'password',
                    'api-key', 'api_key', 'apiKey', 'token', 'access_token', 'secret'):
            for scope in ('top', 'model'):
                with self.subTest(key=key, scope=scope):
                    changes = {key: 'DO_NOT_ECHO'} if scope == 'top' else {
                        'roles': {'W9': {'provider': 'p', 'model': 'm', key: 'DO_NOT_ECHO'}}}
                    with self.assertRaises(c.CourtError) as raised:
                        self.config(**changes)
                    self.assertNotIn('DO_NOT_ECHO', str(raised.exception))

    def test_strict_schema_and_model_types(self):
        bad = ({'backend': 'other'}, {'unknown': True}, {'defaults': []}, {'roles': []},
               {'defaults': {'unknown-kind': {'provider': 'p', 'model': 'm'}}},
               {'roles': {'W9': {'provider': '', 'model': 'm'}}},
               {'roles': {'W9': {'provider': 'p', 'model': '  '}}},
               {'roles': {'W9': {'provider': 'p', 'model': 42}}},
               {'roles': {'W9': {'provider': 'p'}}},
               {'roles': {'W9': {'provider': 'p', 'model': 'm', 'extra': True}}})
        for changes in bad:
            with self.subTest(changes=changes):
                with self.assertRaises(c.CourtError):
                    self.config(**changes)

    def test_malformed_json_and_duplicate_fields_fail(self):
        for content in ('[]', 'null', '{broken', '{"backend":"opencode","backend":"opencode"}',
                        '{"roles":{"W9":{"provider":"p","model":"a","model":"b"}}}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding='utf-8')
                with self.assertRaises(c.CourtError):
                    RuntimeConfig.load(self.path)


if __name__ == '__main__':
    unittest.main()
