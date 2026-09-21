# Courtroom with OpenCode

`tools/courtroom.py` runs each witness, juror, opposing counsel, support role and
judicial function in a separate persistent OpenCode session. The human player has
no model session. `judge_admissibility` and `judge_merits` remain separate even when
they use the same model. Runtime model choices never become immutable case facts.

The controller still owns permissions, evidence, the event journal and state
changes. An identity receives its initial permitted packet once, then changes and
newly heard events. Its recurring calls and ordinary resumes reuse its own session.
Lost or contaminated contexts are retired and rebuilt from permitted history;
there is no fallback to the coordinating agent generating character speech.

## Configure models

Use Python 3.10 or newer and OpenCode **1.18.31**, installed externally, for example
`npm install -g opencode-ai@1.18.31`. Other OpenCode versions are
rejected because the launcher and adapter depend on this version's isolation
hooks. Configure provider authentication manually through OpenCode's normal
authentication flow (`opencode auth login`) before launching the court. Provider and model IDs have no
hardcoded policy; local and remote providers are selected through the same mapping.

Save runtime JSON outside the repository, for example
`~/.config/courtroom/runtime.json`. Replace the placeholder provider/model IDs with
IDs returned by `list-models` after launching the server:

```json
{
  "backend": "opencode",
  "base_url": "http://127.0.0.1:4096",
  "defaults": {
    "witness": {"provider": "PROVIDER_ID", "model": "MODEL_ID"},
    "juror": {"provider": "PROVIDER_ID", "model": "MODEL_ID"},
    "counsel": {"provider": "PROVIDER_ID", "model": "MODEL_ID"},
    "bench": {"provider": "PROVIDER_ID", "model": "MODEL_ID"},
    "support": {"provider": "PROVIDER_ID", "model": "MODEL_ID"}
  },
  "roles": {
    "judge_merits": {"provider": "PROVIDER_ID", "model": "MODEL_ID"}
  }
}
```

`roles` overrides a single actual session identity. Use the case's own witness or
juror IDs, or either judicial identity. `player`, `bench`, and unknown identities
are rejected as overrides. Unused kind defaults are permitted; every actual
identity needs a resolved model. Every resolved provider/model pair is checked
against the current server catalog before any new world or role session is created.

An optional absolute `storage_root` selects private storage outside the repository.
Its default is `~/.local/state/courtroom/opencode`. Credentials, authentication
objects, API keys, passwords and tokens are forbidden in runtime JSON. Do not put
credentials in the URL or case file. Optional server authentication uses
`OPENCODE_SERVER_PASSWORD` from the environment, with the same environment value
available to the launcher and client commands. `OPENCODE_SERVER_USERNAME` is also
read from the environment if set; its default is `opencode`.

## Optional Claude subscription login

The external [Anthropic authentication plugin](https://github.com/ex-machina-co/opencode-anthropic-auth)
adds the `Claude Pro/Max` login method. The audited installation is pinned:

```sh
npm install --global --ignore-scripts --legacy-peer-deps @ex-machina/opencode-anthropic-auth@1.8.4
npm root --global
```

Under the printed directory, the entry file is
`@ex-machina/opencode-anthropic-auth/dist/index.js`. Add its absolute `file:///...`
URI to the `plugin` array in your normal `~/.config/opencode/opencode.jsonc`,
preserving any existing settings. Add the same absolute filesystem path (without
`file://`) as `auth_plugin` in the external courtroom runtime JSON. Then run:

```sh
opencode auth login --provider anthropic --method "Claude Pro/Max"
```

Complete the browser login yourself, then start or restart `backend-serve`.
Use `list-models` to select an exposed `anthropic` model in the role assignments.
No token belongs in the courtroom config or repository.

`auth_plugin` is provider-neutral and optional. The guard accepts a module only
when its single exported factory returns an authentication hook alone; extra
tool, prompt or agent hooks fail startup. The selected module's adjacent source
files are fingerprinted, so changing them requires a managed-host restart.
This plugin is trusted host code, not sandboxed code: review replacements and
upgrades, including their request transformations, before selecting them.

## Launch and check

Run these commands from the repository. The first stays in the foreground; run the
remaining commands in another terminal with the same required environment:

```sh
python3 tools/courtroom.py backend-serve --config "$HOME/.config/courtroom/runtime.json"
```

```sh
python3 tools/courtroom.py list-models --config "$HOME/.config/courtroom/runtime.json"
python3 tools/courtroom.py backend-check --config "$HOME/.config/courtroom/runtime.json" \
  --case /absolute/path/to/authored-case.json
python3 tools/courtroom.py start --config "$HOME/.config/courtroom/runtime.json" \
  --world practice --case /absolute/path/to/authored-case.json
python3 tools/courtroom.py resume --config "$HOME/.config/courtroom/runtime.json" \
  --world practice
```

`--executable /absolute/path/to/opencode` can select the launcher executable.
`--root /absolute/path/to/repository` changes the world-storage root; it defaults to
this repository. `--backend opencode` is the default. `backend-check` can instead
inspect an existing `--world` without a `--case`; it does not initialise a world or
open role sessions. `list-models` needs only runtime JSON and the running server.

Starting an existing world verifies its committed case. Supplying a different
`--case` cannot replace it. Changing model assignments may require the backend to
refuse an existing session binding; resolve that explicitly rather than reusing
another model's conversation accidentally.

## Launcher isolation

Use `backend-serve`; an ordinary `opencode serve` process is not an approved court
host. The dedicated launcher uses private `host/config`, `host/data`, `host/cache`,
`host/state`, `host/home` and `host/cwd` directories under `storage_root`. OpenCode's
instruction/skill home is redirected with `OPENCODE_TEST_HOME`; the process's
ordinary `HOME` variable is not rewritten. The host does not
inherit the repository's instructions, tools, MCP servers or plugins. Its only
registered plugin is the supplied fixed prompt guard, which can load the explicitly
selected external authentication hook described above. All tool permissions are denied, and
auxiliary agents are blocked. The adapter verifies the launcher's instance marker
before treating the server as an isolated backend. The supplied launcher accepts
a loopback HTTP endpoint with no URL path prefix.

The existing external OpenCode authentication store at
`$XDG_DATA_HOME/opencode/auth.json` (normally `~/.local/share/opencode/auth.json`)
is linked into the private host data directory; credentials are not copied into
the repository. Remote
well-known authentication that can inject server configuration is rejected.
Custom provider definitions can be supplied in a separate external JSON file
named by `COURTROOM_OPENCODE_PROVIDER_CONFIG`; this file is read in place, not
copied. Only `$schema`, `provider`, `enabled_providers`, and `disabled_providers`
are accepted at its top level.
Keep provider secrets in the existing authentication store or provider environment,
never in courtroom runtime JSON.

This is application-level model isolation. The trusted launcher and server still
run with their normal operating-system filesystem authority; this is not an OS
sandbox or a claim about a provider's internal infrastructure. Each role model has
no ambient filesystem tools or repository prompt. No claim of live-model reasoning
quality follows from passing the deterministic adapter/controller tests.

## Controller operations

All operations accept `--config`, `--root`, and `--world`. They print status, not
sealed model speech or private reasoning:

- `turn --identity ID --kind TYPE --audience ROLE ...` calls one identity.
- `human --event /path/event.json` records the human player's exact contribution.
- `control --event /path/event.json` records permitted deterministic controller events.
- `examine --identity player --witness ID --question "Exact question"` records the
  human question and calls the witness separately in flow mode. For an AI
  examiner, omit `--question`; its own session supplies the question.
  `--purpose admissibility` selects that explicitly restricted examination.
- `deliberate` runs the next jury round; `ballots` collects separate private votes.
- `verdict` deterministically aggregates jury votes. In a bench case, the merits
  judge's `turn` supplies the permitted verdict contribution.
- `close` closes the current sessions. A subsequent start rebuilds them from the
  permitted record.

The existing [session documentation](courtroom-sessions.md) describes routing,
judicial separation, evidence revocation and the event boundary. A command is a
host integration operation, not a requirement for a human player to manage IDs or
procedural bookkeeping during play.

## Offline tests

The mock path needs neither OpenCode nor credentials and must be selected
explicitly. The original `tools/courtroom_sessions.py` mock CLI remains available:

```sh
python3 tools/courtroom.py start --backend mock --allow-mock \
  --world practice-test --case /absolute/path/to/artificial-fixture.json
python3 -m unittest discover -s tests -v
```

`--script /path/responses.json` supplies per-identity response queues for mock
operations. It is rejected for live OpenCode operations. Automated tests use
artificial fixtures, mock sessions and fake transports; they do not require
OpenCode, credentials or provider calls.

## Optional live smoke

With the hardened server running, this explicitly makes real provider calls using
synthetic canaries and checks independent session resume. It may consume usage:

```sh
python3 tools/courtroom_opencode_smoke.py --config "$HOME/.config/courtroom/runtime.json" \
  --provider PROVIDER_ID --model MODEL_ID
```

Failure or an unavailable server is reported as failure, never a passing test.
The deterministic suite does not run this command. No live OpenCode integration
result is claimed when OpenCode is absent.

## Audited host contract

The adapter targets the V1 API in the pinned release, not the incompatible V2 API.
Version upgrades require rechecking the session, permission and prompt hooks.
The guard strips automatically assembled environment, AGENTS, skills and MCP
instructions before the provider request and prevents auxiliary-agent model calls.
All tool permissions are denied at both agent and session level, including
OpenCode's usual external tool-output directory exception. Tool execution also
fails at the guard hook. Remote servers are unsupported by this managed-host adapter.

Primary references: [headless server API](https://opencode.ai/docs/server/),
[pinned request assembly and permission filtering](https://github.com/anomalyco/opencode/blob/v1.18.31/packages/opencode/src/session/llm/request.ts),
[pinned agent permissions](https://github.com/anomalyco/opencode/blob/v1.18.31/packages/opencode/src/agent/agent.ts),
and [pinned session prompt lifecycle](https://github.com/anomalyco/opencode/blob/v1.18.31/packages/opencode/src/session/prompt.ts).
