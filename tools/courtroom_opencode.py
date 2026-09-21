"""OpenCode HTTP sessions behind the provider-neutral courtroom backend contract.

The adapter accepts only the audited, application-launched host. A normal coding
server is deliberately insufficient: even with tools denied it adds ambient context.
No credentials enter session metadata, packets, errors or the case journal.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
import uuid

import courtroom_v2 as c
from courtroom_backend import Backend, Capabilities, Session, SessionUnavailable
from courtroom_runtime_config import RuntimeConfig, ModelConfig
from courtroom_opencode_host import VERSION, AGENT, SYSTEM, DENY_RULE, verify_host, guard_description


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class TransportError(c.CourtError):
    def __init__(self, status=None):
        self.status = status
        super().__init__('OpenCode HTTP request failed' + (f' (status {status})' if status else '') +
                         '; check the local server and environment authentication.')


class HTTPTransport:
    """No redirects/proxies; do not expose server errors that could echo credentials."""
    def __init__(self, base_url, timeout=180):
        self.base_url = base_url
        self.timeout = timeout
        self.opener = build_opener(_NoRedirect(), ProxyHandler({}))

    def request(self, method, path, body=None, directory=None):
        url = self.base_url + path
        if directory is not None:
            url += '?' + urlencode({'directory': str(directory)})
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        password = os.environ.get('OPENCODE_SERVER_PASSWORD')
        if password:
            user = os.environ.get('OPENCODE_SERVER_USERNAME', 'opencode')
            headers['Authorization'] = 'Basic ' + base64.b64encode((user + ':' + password).encode()).decode()
        request = Request(url, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                # Bound an unexpected server response instead of exhausting the controller.
                raw = response.read(32 * 1024 * 1024 + 1)
                c.require(len(raw) <= 32 * 1024 * 1024, 'OpenCode response exceeded the safety limit.')
                return json.loads(raw)
        except HTTPError as exc:
            raise TransportError(exc.code) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise TransportError() from None


def _private_directory(path):
    path = Path(path)
    c.require(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)),
              'OpenCode storage must be an absolute nonsymlink directory.')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    c.require(path.is_dir() and path.stat().st_uid == os.getuid(), 'OpenCode storage must be owned by this user.')
    path.chmod(0o700)
    return path


def _signature(message):
    """Compare model-visible history, not changing timestamps/token accounting."""
    c.require(isinstance(message, dict) and isinstance(message.get('info'), dict) and
              isinstance(message.get('parts'), list), 'Malformed OpenCode message history.')
    info = message['info']
    c.require(info.get('role') in {'user', 'assistant'} and isinstance(info.get('id'), str),
              'Unexpected OpenCode message identity.')
    parts = []
    for part in message['parts']:
        c.require(isinstance(part, dict) and part.get('type') in {'text', 'reasoning', 'step-start', 'step-finish'},
                  'OpenCode history contains a tool, file, task or compacted context.')
        if part['type'] in {'text', 'reasoning'}:
            c.require(isinstance(part.get('text'), str), 'Malformed OpenCode text part.')
            c.require(not part.get('synthetic') and not part.get('ignored'), 'Unexpected injected OpenCode message.')
            parts.append({'type': part['type'], 'text': part['text']})
    return {'id': info['id'], 'role': info['role'], 'digest': c.digest(c.encode(parts))}


def _texts(message):
    return ''.join(part['text'] for part in message['parts'] if part['type'] == 'text')


class OpenCodeBackend(Backend):
    """One durable OpenCode conversation and empty working directory per identity."""
    capabilities = Capabilities(False, False, False, False)

    def __init__(self, config: RuntimeConfig, assignments: dict[str, ModelConfig], *, transport=None):
        self.config = config
        self.assignments = dict(assignments)
        self.transport = transport or HTTPTransport(config.base_url)
        self.manifest = verify_host(config)
        self.backend_id = 'opencode-v1:' + str(self.manifest['instance']) + ':' + config.base_url
        self.directory = _private_directory(config.storage_root / 'sessions')
        self.workspaces = _private_directory(config.storage_root / 'roles')
        self._ready = False

    def _request(self, method, path, body=None, directory=None):
        return self.transport.request(method, path, body, directory)

    def healthcheck(self):
        health = self._request('GET', '/global/health')
        c.require(isinstance(health, dict) and health.get('healthy') is True and health.get('version') == VERSION,
                  'OpenCode version/capability is not audited; use the pinned courtroom backend-serve host.')
        return health

    def _host(self):
        current = verify_host(self.config)
        c.require(current['instance'] == self.manifest['instance'] and current['nonce'] == self.manifest['nonce'],
                  'OpenCode host changed; run preflight again before resuming.')

    def _lockdown(self, directory):
        self._host()
        self._empty(directory)
        config = self._request('GET', '/config', directory=directory)
        c.require(isinstance(config, dict) and config.get('permission') == {'*': 'deny'} and
                  config.get('default_agent') == AGENT and config.get('share') == 'disabled' and
                  config.get('compaction', {}).get('auto') is False and
                  config.get('compaction', {}).get('prune') is False and
                  not config.get('mcp') and not config.get('instructions') and
                  config.get('plugin') == [self.manifest['plugin_uri']],
                  'OpenCode tool lockdown/configuration cannot be confirmed.')
        agents = self._request('GET', '/agent', directory=directory)
        c.require(isinstance(agents, list), 'OpenCode agent capability unavailable.')
        agents = [a for a in agents if a.get('name') == AGENT]
        c.require(len(agents) == 1 and agents[0].get('description') == guard_description(self.manifest['nonce']) and
                  agents[0].get('mode') == 'primary' and agents[0].get('permission', [])[-1:] == [DENY_RULE] and
                  not agents[0].get('options') and not agents[0].get('model'),
                  'OpenCode loaded guard/tool lockdown cannot be confirmed.')
        c.require(self._request('GET', '/mcp', directory=directory) == {}, 'OpenCode MCP must be disabled.')

    def _empty(self, directory):
        directory = Path(directory)
        c.require(directory.parent == self.workspaces and directory.is_dir() and
                  not directory.is_symlink() and not any(directory.iterdir()),
                  'Every OpenCode identity requires its own empty external working directory.')

    def _workspace(self):
        return _private_directory(self.workspaces / uuid.uuid4().hex)

    def list_models(self):
        # Provider availability is supplied by OpenCode. No provider policy here.
        directory = self._workspace()
        try:
            self._lockdown(directory)
            result = self._request('GET', '/config/providers', directory=directory)
            c.require(isinstance(result, dict) and isinstance(result.get('providers'), list),
                      'OpenCode configured-provider catalog unavailable.')
            catalog = set()
            for provider in result['providers']:
                c.require(isinstance(provider.get('id'), str) and isinstance(provider.get('models'), dict),
                          'Malformed OpenCode provider catalog.')
                for model in provider['models']:
                    catalog.add((provider['id'], model))
            return catalog
        finally:
            directory.rmdir()

    def preflight(self):
        self._ready = False
        self.capabilities = Capabilities(False, False, False, False)
        self._host()
        self.healthcheck()
        spec = self._request('GET', '/doc')
        paths = spec.get('paths', {}) if isinstance(spec, dict) else {}
        required = {'/session': ['post'], '/session/{sessionID}': ['get', 'delete'],
                    '/session/{sessionID}/message': ['post', 'get'], '/session/{sessionID}/abort': ['post'],
                    '/config': ['get'], '/agent': ['get'], '/mcp': ['get'], '/config/providers': ['get']}
        c.require(all(all(verb in paths.get(path, {}) for verb in verbs) for path, verbs in required.items()),
                  'OpenCode persistent session API capability is missing.')
        catalog = self.list_models()
        self.config.validate_models(self.assignments, catalog)
        with tempfile.TemporaryFile(dir=self.directory) as probe:
            probe.write(b'courtroom runtime write probe'); probe.flush(); os.fsync(probe.fileno())
        # Exercise actual separate persisted histories without calling a model.
        self._ready = True
        probes = []
        try:
            model = next(iter(self.assignments.values()), None)
            c.require(model is not None or bool(catalog), 'No OpenCode models configured.')
            if model is None:
                model = ModelConfig(*sorted(catalog)[0])
            for i in range(2):
                probes.append(self._create('__preflight_' + str(i), 'Isolated preflight.',
                                           {'canary': uuid.uuid4().hex}, model))
            c.require(probes[0].session_id != probes[1].session_id, 'OpenCode reused an independent session ID.')
            for handle in probes:
                self.resume_session(handle.session_id)
        except Exception:
            self._ready = False
            raise
        finally:
            # Cleanup is part of preflight; failure must leave this backend disabled.
            self._ready = False
            for handle in probes:
                meta = self._load(handle.session_id)
                try:
                    self._request('DELETE', '/session/' + quote(handle.session_id), directory=meta['directory'])
                finally:
                    meta['closed'] = True; self._save(meta)
        self._ready = True
        self.capabilities = Capabilities()
        return {'backend': 'opencode', 'version': VERSION, 'models': len(catalog),
                'assigned_identities': len(self.assignments), 'independent_sessions': True,
                'tool_lockdown': True, 'ambient_context_blocked': True,
                'runtime_writable': True, 'credentials_persisted': False}

    def _path(self, session_id):
        c.require(isinstance(session_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{8,128}', session_id),
                  'Invalid OpenCode session ID.')
        return c.safe_path(self.directory, Path(session_id + '.json'))

    def _load(self, session_id):
        try:
            meta = c.load(self._path(session_id))
        except FileNotFoundError:
            raise SessionUnavailable(session_id) from None
        c.require(meta['backend'] == self.backend_id and meta['handle']['session_id'] == session_id,
                  'OpenCode session ownership metadata mismatch.')
        return meta

    def _save(self, meta):
        c.atomic(self._path(meta['handle']['session_id']), c.encode(meta))

    def _info(self, meta):
        sid = meta['handle']['session_id']
        try:
            info = self._request('GET', '/session/' + quote(sid), directory=meta['directory'])
        except TransportError as exc:
            if exc.status == 404:
                raise SessionUnavailable(sid) from None
            raise
        c.require(isinstance(info, dict) and info.get('id') == sid and not info.get('parentID') and
                  info.get('directory') == meta['directory'] and info.get('permission') == [DENY_RULE],
                  'OpenCode session independence, directory or permissions changed.')

    def _messages(self, meta):
        messages = self._request('GET', '/session/' + quote(meta['handle']['session_id']) + '/message',
                                 directory=meta['directory'])
        c.require(isinstance(messages, list), 'OpenCode message history capability unavailable.')
        return messages

    def create_session(self, identity, system_prompt, initial_packet, model_config=None):
        model = model_config or self.assignments.get(identity)
        c.require(isinstance(model, ModelConfig), 'No runtime model assignment for this identity.')
        c.require(self.assignments.get(identity) == model, 'Model assignment must match preflight.')
        return self._create(identity, system_prompt, initial_packet, model)

    def _create(self, identity, system_prompt, initial_packet, model):
        c.require(self._ready, 'OpenCode backend preflight must succeed before session creation.')
        directory = self._workspace()
        self._lockdown(directory)
        info = self._request('POST', '/session', {'title': 'Courtroom isolated identity',
                                                'permission': [DENY_RULE]}, directory)
        c.require(isinstance(info, dict) and isinstance(info.get('id'), str), 'OpenCode did not create a session.')
        sid = info['id']
        c.require(not self._path(sid).exists(), 'OpenCode reused an identity session ID.')
        handle = Session(sid, sid, identity)
        meta = {'handle': asdict(handle), 'backend': self.backend_id, 'directory': str(directory),
                'model': asdict(model), 'messages': [], 'closed': False, 'initialised': False}
        self._save(meta)
        self._info(meta)
        c.require(not self._messages(meta), 'New OpenCode session already has a context.')
        payload = {'identity': identity, 'system_prompt': system_prompt, 'initial_packet': deepcopy(initial_packet),
                   'delivery': 'Initial permitted context. Subsequent packets contain changes only. '
                   'Merge documents by key and events/public_orders by id; apply explicit removed entries. '
                   'Return only JSON with text, data, optional private_reasoning for the requested action.'}
        self._post(meta, payload, initial=True)
        meta['initialised'] = True
        self._save(meta)
        return handle

    def resume_session(self, session_id):
        c.require(self._ready, 'OpenCode backend preflight must succeed before resume.')
        meta = self._load(session_id)
        if meta['closed'] or not meta['initialised']:
            raise SessionUnavailable(session_id)
        identity = meta['handle']['identity']
        if not identity.startswith('__preflight_'):
            c.require(self.assignments.get(identity) == ModelConfig(**meta['model']),
                      'An identity model assignment changed; close the runtime before changing models.')
        self._lockdown(meta['directory'])
        self._info(meta)
        messages = self._messages(meta)
        if [_signature(message) for message in messages] != meta['messages']:
            raise SessionUnavailable(session_id)
        return Session(**meta['handle'])

    def _post(self, meta, payload, initial=False):
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        body = {'agent': AGENT, 'model': {'providerID': meta['model']['provider'], 'modelID': meta['model']['model']},
                'system': SYSTEM, 'tools': {'*': False}, 'parts': [{'type': 'text', 'text': text}]}
        if initial:
            body['noReply'] = True
        result = self._request('POST', '/session/' + quote(meta['handle']['session_id']) + '/message', body, meta['directory'])
        messages = self._messages(meta)
        signatures = [_signature(message) for message in messages]
        before = len(meta['messages'])
        c.require(signatures[:before] == meta['messages'] and len(messages) == before + (1 if initial else 2),
                  'OpenCode context changed outside the orchestrator.')
        c.require(messages[before]['info']['role'] == 'user' and _texts(messages[before]) == text,
                  'OpenCode changed the supplied role packet.')
        c.require(_signature(result) == signatures[-1], 'OpenCode response/history mismatch.')
        if not initial:
            c.require(result['info']['role'] == 'assistant', 'OpenCode did not return an identity response.')
            error = result['info'].get('error')
            if error:
                status = error.get('data', {}).get('statusCode') if isinstance(error, dict) else None
                detail = f' (provider HTTP {status})' if type(status) is int else ''
                # Provider errors may contain request headers; never echo their body.
                raise c.CourtError('OpenCode model call failed' + detail + '; check the external provider setup.')
        meta['messages'] = signatures
        self._save(meta)
        return result

    def send(self, session_id, request):
        handle = self.resume_session(session_id)
        c.require(request.get('identity') == handle.identity, 'Request identity does not own this OpenCode session.')
        meta = self._load(session_id)
        result = self._post(meta, request)
        try:
            response = json.loads(_texts(result))
        except (ValueError, TypeError):
            raise c.CourtError('OpenCode identity must return one JSON response; repair/restart this identity.') from None
        c.require(isinstance(response, dict) and set(response) <= {'text', 'data', 'private_reasoning'} and
                  isinstance(response.get('text'), str) and isinstance(response.get('data'), dict) and
                  isinstance(response.get('private_reasoning', ''), str), 'Invalid OpenCode identity response.')
        return response

    def close_session(self, session_id):
        try:
            meta = self._load(session_id)
        except SessionUnavailable:
            return
        try:
            self._request('POST', '/session/' + quote(session_id) + '/abort', {}, meta['directory'])
        except TransportError as exc:
            if exc.status != 404:
                raise
        meta['closed'] = True
        self._save(meta)
