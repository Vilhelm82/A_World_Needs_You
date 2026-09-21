"""Credential-free model routing, separate from immutable courtroom case facts.

JSON uses ``defaults`` keyed by role kind and ``roles`` keyed by session identity.
Provider/model IDs are opaque strings; availability is checked against the live
catalog before the backend opens any role session. Authentication belongs to the
server environment, never this file or a case packet.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import ipaddress
import json
from pathlib import Path
from types import MappingProxyType
from urllib.parse import urlsplit

import courtroom_v2 as c


KINDS = frozenset({'witness', 'juror', 'counsel', 'bench', 'support'})
REPOSITORY = Path(__file__).resolve().parents[1]
_SECRET_FIELDS = frozenset({'credential', 'credentials', 'auth', 'authentication',
    'authorization', 'password', 'passwd', 'apikey', 'token', 'accesstoken',
    'refreshtoken', 'secret', 'clientsecret'})


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    reasoning: str | None = None


def _object(pairs):
    result = {}
    for key, value in pairs:
        c.require(key not in result, 'Duplicate fields are not allowed in runtime config.')
        result[key] = value
    return result


def _reject_credentials(value):
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = ''.join(ch for ch in key.lower() if ch.isalnum())
            c.require(normalized not in _SECRET_FIELDS,
                      'Runtime config cannot contain credential fields; use environment authentication.')
            _reject_credentials(child)
    elif isinstance(value, list):
        for child in value:
            _reject_credentials(child)


def _model(value):
    c.require(isinstance(value, dict) and {'provider', 'model'} <= set(value) <= {'provider', 'model', 'reasoning'},
              'Each model assignment requires provider and model, with optional reasoning.')
    c.require(all(isinstance(value[key], str) and value[key].strip() for key in ('provider', 'model')),
              'Provider and model IDs must be nonempty strings.')
    if 'reasoning' in value:
        c.require(isinstance(value['reasoning'], str) and bool(value['reasoning'].strip())
                  and value['reasoning'] == value['reasoning'].strip(),
                  'reasoning must be a nonempty OpenCode variant name.')
    return ModelConfig(value['provider'], value['model'], value.get('reasoning'))


def _base_url(value, allow_remote):
    c.require(isinstance(value, str) and value and not any(ch.isspace() or ord(ch) < 32 for ch in value),
              'Runtime base_url must be an HTTP URL without whitespace.')
    try:
        parsed = urlsplit(value)
        hostname, port = parsed.hostname, parsed.port
    except ValueError:
        raise c.CourtError('Invalid runtime base_url.') from None
    c.require(parsed.scheme in {'http', 'https'} and hostname and parsed.netloc,
              'Runtime base_url must use HTTP or HTTPS with a hostname.')
    c.require(parsed.username is None and parsed.password is None and not parsed.query and not parsed.fragment,
              'Runtime base_url cannot contain authentication, query parameters, or fragments.')
    c.require(port is None or 1 <= port <= 65535, 'Invalid runtime base_url port.')
    try:
        loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        loopback = hostname.lower() == 'localhost'
    c.require(loopback or allow_remote,
              'Runtime base_url must use loopback unless allow_remote is explicitly true.')
    return value.rstrip('/')


@dataclass(frozen=True)
class RuntimeConfig:
    backend: str
    base_url: str
    defaults: Mapping[str, ModelConfig]
    roles: Mapping[str, ModelConfig]
    storage_root: Path
    allow_remote: bool = False
    auth_plugin: Path | None = None

    @classmethod
    def load(cls, path):
        """Read and validate JSON without opening sessions or creating directories."""
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_object)
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise c.CourtError('Cannot read runtime config as valid UTF-8 JSON.') from None
        c.require(isinstance(data, dict), 'Runtime config must be a JSON object.')
        _reject_credentials(data)
        c.require(set(data) <= {'backend', 'base_url', 'defaults', 'roles', 'storage_root', 'allow_remote', 'auth_plugin'},
                  'Unknown runtime config fields.')
        backend = data.get('backend', 'opencode')
        c.require(backend == 'opencode', 'Runtime config backend must be opencode.')
        allow_remote = data.get('allow_remote', False)
        c.require(type(allow_remote) is bool, 'allow_remote must be a boolean.')
        base_url = _base_url(data.get('base_url', 'http://127.0.0.1:4096'), allow_remote)
        defaults, roles = data.get('defaults', {}), data.get('roles', {})
        c.require(isinstance(defaults, dict) and set(defaults) <= KINDS,
                  'Runtime defaults must be an object keyed by known role kinds.')
        c.require(isinstance(roles, dict) and all(isinstance(key, str) and key.strip() for key in roles),
                  'Runtime roles must be an object keyed by nonempty session identities.')
        storage = data.get('storage_root', str(Path.home() / '.local/state/courtroom/opencode'))
        c.require(isinstance(storage, str) and storage and '\x00' not in storage,
                  'Runtime storage_root must be an absolute path outside the repository.')
        storage_root = Path(storage).expanduser()
        c.require(storage_root.is_absolute(), 'Runtime storage_root must be an absolute path outside the repository.')
        storage_root = storage_root.resolve()
        c.require(storage_root != REPOSITORY and REPOSITORY not in storage_root.parents,
                  'Runtime storage_root must be outside the repository.')
        auth_plugin = data.get('auth_plugin')
        if auth_plugin is not None:
            c.require(isinstance(auth_plugin, str) and Path(auth_plugin).expanduser().is_absolute(),
                      'auth_plugin must be an absolute external JavaScript entry file.')
            auth_plugin = Path(auth_plugin).expanduser().resolve()
            c.require(auth_plugin.suffix in {'.js', '.mjs'} and auth_plugin.is_file() and
                      REPOSITORY not in auth_plugin.parents,
                      'auth_plugin must be an existing external JavaScript entry file.')
        return cls(backend=backend, base_url=base_url,
                   defaults=MappingProxyType({kind: _model(value) for kind, value in defaults.items()}),
                   roles=MappingProxyType({identity: _model(value) for identity, value in roles.items()}),
                   storage_root=storage_root, allow_remote=allow_remote, auth_plugin=auth_plugin)

    def resolve(self, case) -> dict[str, ModelConfig]:
        """Resolve every nonhuman identity, including separate judicial contexts."""
        # Import lazily: the orchestrator may itself import this module for its CLI.
        from courtroom_sessions import identities, role_for

        c.require(isinstance(case, dict) and isinstance(case.get('roles'), dict),
                  'Case roles are required for runtime model assignment.')
        roles = case['roles']
        c.require(all(isinstance(who, str) and isinstance(role, dict) and role.get('kind') in KINDS
                      for who, role in roles.items()) and 'bench' in roles,
                  'Case has invalid runtime role kinds or no bench.')
        wanted = identities(case)
        unknown = set(self.roles) - set(wanted)
        c.require(not unknown, 'Unknown runtime identity overrides: ' + ', '.join(sorted(unknown)))
        assignments = {}
        missing = []
        for identity in wanted:
            kind = roles[role_for(identity)]['kind']
            model = self.roles.get(identity, self.defaults.get(kind))
            if model is None:
                missing.append(identity + ' (' + kind + ')')
            else:
                assignments[identity] = model
        c.require(not missing, 'Missing model assignment for: ' + ', '.join(missing))
        return assignments

    @staticmethod
    def validate_models(assignments, catalog):
        """Fail before session creation unless every resolved provider/model exists."""
        c.require(isinstance(catalog, (set, frozenset)) and
                  all(isinstance(pair, tuple) and len(pair) == 2 and
                      all(isinstance(value, str) and value.strip() for value in pair) for pair in catalog),
                  'Provider catalog must be a set of (provider, model) string pairs.')
        c.require(isinstance(assignments, Mapping) and
                  all(isinstance(identity, str) and isinstance(model, ModelConfig) and
                      all(isinstance(value, str) and value.strip() for value in (model.provider, model.model))
                      for identity, model in assignments.items()),
                  'Invalid resolved runtime model assignments.')
        missing = [identity + ' (' + model.provider + '/' + model.model + ')'
                   for identity, model in sorted(assignments.items())
                   if (model.provider, model.model) not in catalog]
        c.require(not missing, 'Unavailable model assignments: ' + ', '.join(missing))
