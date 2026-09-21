"""Private, version-pinned OpenCode host; no changes to the user's normal setup.

The guard removes ambient model context, not the OS authority of the trusted
OpenCode process or provider implementations. The manifest attests this locally
managed launch; it is not a claim about an arbitrary remote server.
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import stat
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
import uuid

import courtroom_v2 as c

VERSION = '1.18.31'
AGENT = 'courtroom'
DENY_RULE = {'permission': '*', 'pattern': '*', 'action': 'deny'}
SYSTEM = 'You are one isolated courtroom identity. Follow only the identity instructions and court packets supplied in this conversation. You have no tools or access to files, repositories, other sessions, or outside information. Return exactly one raw JSON object with text (string), data (object), and optional private_reasoning (brief fictional private notes, not hidden chain of thought). Do not use Markdown fences or surrounding prose.'
PROTOCOL = 'courtroom-opencode-v1'
GUARD = Path(__file__).with_name('courtroom_opencode_guard.mjs')
REPOSITORY = Path(__file__).resolve().parents[1]


def guard_description(nonce):
    return 'courtroom-guard-v1:' + nonce


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _auth_plugin(config):
    """Bind an explicitly selected external auth module and its local source files."""
    entry = getattr(config, 'auth_plugin', None)
    if entry is None:
        return None
    entry = Path(entry)
    c.require(entry.is_absolute() and entry.is_file() and entry.suffix in {'.js', '.mjs'} and
              REPOSITORY not in entry.resolve().parents, 'Invalid external authentication plugin.')
    fingerprint = hashlib.sha256()
    for file in sorted(entry.parent.rglob('*')):
        c.require(not file.is_symlink(), 'Authentication plugin source cannot contain symbolic links.')
        if file.is_file():
            fingerprint.update(str(file.relative_to(entry.parent)).encode() + b'\0')
            fingerprint.update(file.read_bytes())
    return {'uri': entry.as_uri(), 'sha256': fingerprint.hexdigest()}


def _private(path, directory=False):
    path = Path(path)
    c.require(not path.is_symlink(), 'Host paths cannot be symbolic links.')
    info = path.stat()
    c.require(info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o077,
              'Host state must be owned by this user and private.')
    c.require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode),
              'Invalid host state file type.')
    return path


def _root(config):
    root = Path(config.storage_root).absolute() / 'host'
    c.require(REPOSITORY not in root.resolve().parents and root.resolve() != REPOSITORY,
              'OpenCode host state must be outside the repository.')
    c.require(not any(p.is_symlink() for p in (root, *root.parents)),
              'OpenCode host state cannot traverse symbolic links.')
    return root


def _endpoint(config):
    parsed = urlsplit(config.base_url)
    c.require(parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'}
              and parsed.path in {'', '/'} and not parsed.query and not parsed.fragment
              and parsed.username is None and parsed.password is None,
              'The managed OpenCode host requires a loopback HTTP URL without a path.')
    return parsed.hostname, parsed.port or 80


def _write(path, value):
    path = Path(path)
    c.require(not path.is_symlink(), 'Host state cannot overwrite symbolic links.')
    temporary = path.with_name(path.name + '.' + secrets.token_hex(8))
    try:
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as out:
            out.write(json.dumps(value, sort_keys=True) + '\n')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _load(path):
    try:
        return json.loads(_private(path).read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError):
        raise c.CourtError('Cannot verify private OpenCode host state.') from None


def _running(pid, nonce):
    if type(pid) is not int or pid <= 0:
        return False
    try:
        info = Path('/proc') / str(pid)
        if info.stat().st_uid != os.getuid():
            return False
        environment = (info / 'environ').read_bytes().split(b'\0')
        return ('COURTROOM_OPENCODE_NONCE=' + nonce).encode() in environment
    except (OSError, ValueError):
        return False


def verify_host(config):
    """Verify launch provenance; the adapter additionally verifies each instance."""
    _endpoint(config)
    root = _root(config)
    try:
        _private(root, directory=True)
        manifest = _load(root / 'manifest.json')
        c.require(isinstance(manifest, dict) and manifest.get('protocol') == PROTOCOL
                  and manifest.get('version') == VERSION and manifest.get('base_url') == config.base_url
                  and manifest.get('host_root') == str(root), 'Unsupported OpenCode host manifest.')
        nonce = manifest.get('nonce')
        c.require(isinstance(nonce, str) and len(nonce) == 64 and all(x in '0123456789abcdef' for x in nonce),
                  'Invalid OpenCode host nonce.')
        plugin = _private(root / 'config' / 'courtroom-guard.mjs')
        c.require(manifest.get('plugin_uri') == plugin.as_uri()
                  and manifest.get('plugin_sha256') == _digest(plugin) == _digest(GUARD),
                  'OpenCode hardening guard has changed; restart the managed host.')
        settings = _private(root / 'config' / 'opencode.json')
        c.require(manifest.get('config_sha256') == _digest(settings),
                  'OpenCode host configuration has changed; restart the managed host.')
        c.require(manifest.get('auth_plugin') == _auth_plugin(config),
                  'Authentication plugin changed; restart the managed host.')
        provider_path = manifest.get('provider_config')
        if provider_path:
            c.require(manifest.get('provider_config_sha256') == _digest(provider_path),
                      'Provider configuration has changed; restart the managed host.')
        c.require(_running(manifest.get('pid'), nonce), 'The managed OpenCode host is not running.')
        identity = _load(root / 'identity.json')
        c.require(manifest.get('instance') == identity.get('instance'), 'OpenCode host identity mismatch.')
        return manifest
    except OSError:
        raise c.CourtError('The managed OpenCode host is unavailable; start backend-serve first.') from None


def _settings(plugin_uri):
    return {'$schema': 'https://opencode.ai/config.json', 'default_agent': AGENT,
            'permission': {'*': 'deny'}, 'plugin': [plugin_uri], 'mcp': {},
            'instructions': [], 'skills': {'paths': [], 'urls': []}, 'references': {},
            'share': 'disabled', 'snapshot': False, 'autoupdate': False,
            'compaction': {'auto': False, 'prune': False}, 'lsp': False, 'formatter': False,
            'agent': {AGENT: {'mode': 'primary', 'prompt': SYSTEM, 'permission': {'*': 'deny'}},
                      **{name: {'disable': True} for name in
                         ('build', 'plan', 'general', 'explore', 'title', 'summary', 'compaction')}}}


def _provider_config():
    value = os.environ.get('COURTROOM_OPENCODE_PROVIDER_CONFIG')
    if not value:
        return None
    try:
        path = Path(value).expanduser().resolve(strict=True)
        c.require(path.is_file() and path != REPOSITORY and REPOSITORY not in path.parents,
                  'Provider configuration must be an external JSON file.')
        data = json.loads(path.read_text(encoding='utf-8'))
        c.require(isinstance(data, dict) and set(data) <= {
            '$schema', 'provider', 'enabled_providers', 'disabled_providers'},
            'The external provider file may contain provider settings only.')
        c.require(isinstance(data.get('provider', {}), dict), 'Invalid external provider settings.')
        # Never write this file or copy its contents, which may include credentials.
        return path
    except c.CourtError:
        raise
    except (OSError, ValueError, UnicodeError):
        raise c.CourtError('Cannot read the external provider configuration as JSON.') from None


def _auth_link(root):
    """Reference original credentials without copying them or sharing databases."""
    source = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'opencode/auth.json'
    target = root / 'data' / 'opencode' / 'auth.json'
    if not source.exists():
        c.require(not target.exists() and not target.is_symlink(), 'Unexpected host authentication file.')
        return
    source = source.resolve()
    c.require(REPOSITORY not in source.parents, 'Provider credentials must remain outside the repository.')
    try:
        auth = json.loads(source.read_text(encoding='utf-8'))
        c.require(isinstance(auth, dict) and all(isinstance(item, dict) and
                  item.get('type') in {'api', 'oauth'} for item in auth.values()),
                  'Managed host cannot import credentials that load remote configuration.')
    except c.CourtError:
        raise
    except (OSError, ValueError, UnicodeError):
        raise c.CourtError('Cannot validate the external authentication store.') from None
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.is_symlink():
        c.require(target.resolve() == source, 'Host authentication source has changed.')
    else:
        c.require(not target.exists(), 'Unexpected host authentication file.')
        target.symlink_to(source)


def _environment(root, nonce, plugin, provider, auth_plugin=None):
    # Preserve provider credential/proxy env vars; remove ambient OpenCode settings.
    env = {key: value for key, value in os.environ.items() if not key.startswith('OPENCODE_')}
    for key in ('NODE_OPTIONS', 'BUN_OPTIONS', 'BUN_INSPECT'):
        env.pop(key, None)
    for key in ('OPENCODE_SERVER_PASSWORD', 'OPENCODE_SERVER_USERNAME'):
        if key in os.environ:
            env[key] = os.environ[key]
    env.update({'XDG_CONFIG_HOME': str(root / 'config-home'), 'XDG_DATA_HOME': str(root / 'data'),
                'XDG_CACHE_HOME': str(root / 'cache'), 'XDG_STATE_HOME': str(root / 'state'),
                'OPENCODE_TEST_HOME': str(root / 'home'), 'OPENCODE_CONFIG_DIR': str(root / 'config'),
                'OPENCODE_DISABLE_PROJECT_CONFIG': '1', 'OPENCODE_DISABLE_CLAUDE_CODE': '1',
                'OPENCODE_DISABLE_EXTERNAL_SKILLS': '1', 'OPENCODE_DISABLE_AUTOCOMPACT': '1',
                'OPENCODE_DISABLE_PRUNE': '1', 'OPENCODE_DISABLE_AUTOUPDATE': '1',
                'OPENCODE_DISABLE_LSP_DOWNLOAD': '1', 'OPENCODE_DISABLE_EMBEDDED_WEB_UI': '1',
                'OPENCODE_EXPERIMENTAL_DISABLE_FILEWATCHER': '1',
                'COURTROOM_OPENCODE_NONCE': nonce, 'COURTROOM_OPENCODE_GUARD_URI': plugin.as_uri(),
                'COURTROOM_OPENCODE_AUTH_PLUGIN': auth_plugin['uri'] if auth_plugin else ''})
    if provider:
        env['OPENCODE_CONFIG'] = str(provider)
    return env


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise c.CourtError('OpenCode host redirects are not allowed.')


def _get(base, route, directory=None):
    url = base + route + ('?' + urlencode({'directory': str(directory)}) if directory else '')
    headers = {}
    password = os.environ.get('OPENCODE_SERVER_PASSWORD')
    if password:
        username = os.environ.get('OPENCODE_SERVER_USERNAME', 'opencode')
        headers['Authorization'] = 'Basic ' + base64.b64encode((username + ':' + password).encode()).decode()
    with build_opener(ProxyHandler({}), _NoRedirect()).open(Request(url, headers=headers), timeout=3) as response:
        return json.loads(response.read(4 * 1024 * 1024))


def _preflight(base, directory, nonce, plugin_uri):
    health = _get(base, '/global/health')
    c.require(health == {'healthy': True, 'version': VERSION}, 'Unsupported OpenCode version.')
    cfg = _get(base, '/config', directory)
    c.require(cfg.get('permission') == {'*': 'deny'} and cfg.get('plugin') == [plugin_uri]
              and cfg.get('default_agent') == AGENT and not cfg.get('mcp')
              and not cfg.get('instructions') and cfg.get('share') == 'disabled'
              and cfg.get('compaction', {}).get('auto') is False
              and cfg.get('compaction', {}).get('prune') is False,
              'OpenCode effective configuration failed lockdown verification.')
    agents = _get(base, '/agent', directory)
    agent = next((item for item in agents if item.get('name') == AGENT), {})
    rules = agent.get('permission', [])
    c.require(agent.get('description') == guard_description(nonce) and agent.get('mode') == 'primary'
              and bool(rules) and rules[-1] == DENY_RULE and not agent.get('options'),
              'OpenCode hardening guard did not initialize safely.')
    c.require(_get(base, '/mcp', directory) == {}, 'OpenCode host must not load MCP servers.')


def _serve(config, executable):
    hostname, port = _endpoint(config)
    binary = shutil.which(executable)
    c.require(binary is not None, 'OpenCode is not installed. Install the pinned version 1.18.31 externally.')
    root = _root(config)
    for path in (root, *(root / name for name in ('config', 'config-home', 'data', 'cache', 'state', 'home', 'cwd'))):
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        _private(path, directory=True)
    previous = root / 'manifest.json'
    if previous.exists():
        old = _load(previous)
        c.require(not _running(old.get('pid'), old.get('nonce', '')), 'The managed OpenCode host is already running.')
    identity_path = root / 'identity.json'
    if not identity_path.exists():
        _write(identity_path, {'instance': uuid.uuid4().hex})
    instance = _load(identity_path)['instance']
    provider = _provider_config()
    _auth_link(root)
    nonce = secrets.token_hex(32)
    plugin = root / 'config' / 'courtroom-guard.mjs'
    c.require(not plugin.is_symlink(), 'The hardening plugin cannot be a symbolic link.')
    with os.fdopen(os.open(plugin, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'wb') as output:
        output.write(GUARD.read_bytes())
    os.chmod(plugin, 0o600)
    settings = root / 'config' / 'opencode.json'
    _write(settings, _settings(plugin.as_uri()))
    auth_plugin = _auth_plugin(config)
    env = _environment(root, nonce, plugin, provider, auth_plugin)
    # Check the selected executable before starting a network service.
    version = subprocess.run([binary, '--version'], env=env, cwd=root / 'cwd',
                             capture_output=True, text=True, timeout=20)
    c.require(version.returncode == 0 and version.stdout.strip() == VERSION,
              'Only audited OpenCode version 1.18.31 is supported.')
    previous.unlink(missing_ok=True)
    process = subprocess.Popen([binary, 'serve', '--hostname', hostname, '--port', str(port)],
                               env=env, cwd=root / 'cwd', start_new_session=True)
    try:
        deadline = time.monotonic() + 45
        while True:
            c.require(process.poll() is None, 'The managed OpenCode host exited before becoming ready.')
            try:
                _preflight(config.base_url, root / 'cwd', nonce, plugin.as_uri())
                break
            except (URLError, HTTPError, TimeoutError, OSError):
                c.require(time.monotonic() < deadline, 'The managed OpenCode host did not become ready.')
                time.sleep(.2)
        manifest = {'protocol': PROTOCOL, 'version': VERSION, 'base_url': config.base_url,
                    'pid': process.pid, 'nonce': nonce, 'instance': instance, 'host_root': str(root),
                    'plugin_uri': plugin.as_uri(), 'plugin_sha256': _digest(plugin),
                    'auth_plugin': auth_plugin,
                    'config_sha256': _digest(settings),
                    'provider_config': str(provider) if provider else None,
                    'provider_config_sha256': _digest(provider) if provider else None}
        _write(previous, manifest)
        print('Courtroom OpenCode host ready at ' + config.base_url, flush=True)
        return process.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        previous.unlink(missing_ok=True)


def serve(config, executable='opencode'):
    """Run the private server in the foreground. Does not install OpenCode."""
    _endpoint(config)
    c.require(shutil.which(executable) is not None,
              'OpenCode is not installed. Install the pinned version 1.18.31 externally.')
    root = _root(config)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    _private(root, directory=True)
    lock_path = root / 'launch.lock'
    c.require(not lock_path.is_symlink(), 'Host lock cannot be a symbolic link.')
    with os.fdopen(os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600), 'r+') as lock:
        _private(lock_path)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise c.CourtError('The managed OpenCode host is already starting or running.') from None
        previous_handler = signal.getsignal(signal.SIGTERM)
        def terminate(_signum, _frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, terminate)
        try:
            return _serve(config, executable)
        finally:
            signal.signal(signal.SIGTERM, previous_handler)
