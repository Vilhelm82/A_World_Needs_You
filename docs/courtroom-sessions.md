# Courtroom v2: required isolated conversations

Courtroom v2 requires a separate persistent model conversation for every independent
identity. Packet filtering alone is insufficient. The host that authored/read sealed
case truth is a coordinator, never a character. It must not generate testimony,
strategy, substantive speech, rulings, findings, or juror reasoning.

## Execution boundary

`tools/courtroom_sessions.py` is deterministic orchestration; `courtroom_v2.py` owns
the committed case, append-only event journal, evidence state, objection gates,
jury presence, reference checks, projections and verdict thresholds. Neither calls
a model to impersonate a room. An adapter in `courtroom_backend.py` supplies isolated
conversations. Model responses contain only one identity's text, event data and
optional brief fictional private notes. Models have no filesystem, controller tools,
other conversation memory, shared agent scratchpad or retrieval access.

The session mapping contains opponent, each witness, each juror, each support
identity, `judge_admissibility` and `judge_merits`. A recurring clerk, solicitor or
expert is a committed support/witness role with a session, not prose invented by the
coordinator. The human `player` has no AI session. Automated co-counsel is not enabled.
The `foreperson` event alias forwards a juror's question or a deterministic count
result; it is not a model generating a collective jury mind.

Each model call reconstructs a packet from the committed case and validated journal.
Only allocated knowledge, disclosed documents, personally heard events, permitted
orders and that identity's previous conversation are eligible. The initial packet
is delivered once; subsequent calls carry only changes, merging documents by key
and events/orders by ID. Delivery cursors advance only with committed contributions.
The packet explicitly
whitelists identity fields; author metadata is excluded. Authoring must keep secrets
out of shared summaries, procedure, rule text and personality descriptions. Nervous
or confident manners are not proxies for truth, guilt, or evidence strength.

## Backend contract

Implement `Backend` with a stable `backend_id` identifying the provider/account/store:

- `create_session(identity, system_prompt, initial_packet, model_config=None) -> Session`
- `send(session_id, request) -> {text, data, private_reasoning?, grounding?, authoring_gap?}`
- `resume_session(session_id) -> Session`
- `close_session(session_id)`
- `healthcheck()` and `list_models()` for live backend discovery

`Session` has stable `session_id`, underlying `context_id`, and owning `identity`.
The context handle must represent the actual isolated conversation, not an invented
alias for a shared conversation. Duplicate current or retired handles fail startup.

New live play requires Authoring V2 shared substrate projections. Each identity
receives only owned observations, actual record receipts, routine, deltas and
bounded accounts. Perception limits remove the raw facet from delivered knowledge.
Every witness answer requires checked grounding citations. The substrate itself,
sealed provenance and other identities' accounts never enter a character session.
See `modules/courtroom-v2/authoring.md` for the exact contract.

A witness may report missing authored knowledge with empty `text`, empty `data`,
and a nonempty `authoring_gap` string, without private reasoning. It is not speech.
The orchestrator records only a fixed player-facing engine gap notice, keeps the
explanation in sealed identity history/audit, and pauses the case. It records no
answer and will make no more role calls while paused, including after restart.
Reported gaps cannot be mixed with testimony or used by a different role type.
Readiness requires filled foundations plus the independent coverage rehearsal.
Every witness gets five separate practice contexts: witness, informed examiner,
blind examiner, grader A and grader B. Graders receive identical frozen answers and
permitted sources, without peer assessments. The blind examiner sees only public
setting and neutral role-template weights. Disputes use an optional sixth fresh
session, grader C, with the identical frozen input and no peer assessments. Majority
classification and hearing-plausibility stand. A three-way split returns a sealed
patch target to a fresh pre-play author and requires a new rehearsal. No player ruling
is requested. Human review is exceptional and requires `--reviewer-will-not-play`.
The report preserves raw agreement rate, per-witness tiebreaker/split counts and
per-family/probe-class counts.
Its finite, fallible semantic checks do not cover every possible omission.
Resume must return the same handle and identity. Report `SessionUnavailable` if safe
resumption is impossible. Never attach a guessed, shared or different conversation.
Adapters must declare independent persistent contexts and no ambient access. A backend
without these guarantees is refused; unsafe resume triggers a per-identity rebuild.
The abstract default declares no capabilities. Provider-specific adapters can use
OpenAI, Anthropic, local models, or isolated Codex/Cline-compatible sessions, provided
they satisfy the same contract and disable access to the host's sealed case/files.
A different role prompt in the same conversation does not satisfy it.

The durable `DeterministicBackend` stores independent session
histories and consumes per-identity scripted responses for repeatable tests. It has
no model, network or generated legal reasoning. Unscripted calls fail clearly.
`OpenCodeBackend` supplies real persistent sessions through the headless HTTP API.
Its preflight requires the version-pinned hardened host, wildcard tool denial,
verified prompt guard, unique sessions, empty per-role working directories, and
configured model availability. Follow [OpenCode setup](courtroom-opencode.md).
Provider authentication stays external. There is no fallback to the authoring agent.

A direct Claude Code adapter is intentionally not bundled: safely handling its
ambient instructions, tools and persistence is a separate integration. It can
implement this same interface without duplicating the court controller or routing.

## Startup and use

Validate/author the case before substantive player theory. The low-level Python
`initialise` function prepares immutable storage; it does not start live roleplay.
The old controller `init` command now fails with instructions to select a backend.
Production integration calls `Orchestrator.start(world, backend)` and must not begin
a scene until it succeeds. For an explicit offline mock exercise only:

```sh
python3 tools/courtroom_sessions.py start --world practice \
  --case /path/to/authored-case.json --backend mock --allow-mock
python3 tools/courtroom_sessions.py resume --world practice --backend mock --allow-mock
```

The mock CLI accepts `--script` JSON mapping individual identities to response lists.
It prints operation status only; private responses never go to stdout. Scripts are
artificial test inputs, not a substitute for isolated live reasoning. Ordinary users
need not manage IDs or perform procedural bookkeeping.

Host applications use these operations:

- `human(event)`: records the human's contribution; cannot submit another actor's speech.
- `turn(identity, kind, audience)`: calls only that identity's session and validates its
  response against its permitted action and the controller. No arbitrary global prompt
  argument, actor/audience override, or model tool calls are accepted.
- `examine(examiner, witness, question=None, purpose='merits')`: human question or
  separately generated examiner question, then a separate witness call in flow mode. The question is committed before that
  call; its answer is recorded as a separate `provisional_answer` event.
  An interrupted flow exchange resumes with the witness's `provisional_answer` turn.
  Strict mode leaves the question pending until objections clear and the witness's
  own `answer` turn occurs. Caller-supplied AI answers are rejected.
- `control(event)`: deterministic phase/checkpoint/cadence/error-repair/unseal events;
  never rulings, strategy or character dialogue.
- `deliberate_round()`: mediated round robin. Each juror speaks in its own session;
  commit its jury-room statement before calling the next juror. Round progress persists.
- `collect_ballots()`: independent private votes. No ballot/reason enters another
  juror's context. `return_verdict()` applies configured thresholds per count, including
  mixed and genuinely deliberated hung outcomes, without generating juror reasoning.
- `player_packet()`: only the human's permitted record. `close()` closes sessions;
  a subsequent start safely reconstructs identities from their permitted history.

All live writes require a single-use contribution capability minted by deterministic
orchestration. The raw `record` command cannot impersonate roles in an active runtime.
Prepared storage also refuses live contributions until a backend starts. The private
`_fixture=True` switch is reserved for constructing offline state-machine test records;
it cannot bypass the session guard once a runtime exists and is not exposed in the CLI. Python
module internals and the host filesystem are trusted application code, not a sandbox
against an operator deliberately rewriting them.

## Judicial and jury isolation

`judge_admissibility` may inspect offered material. `judge_merits` receives only
admitted/limited exhibits and merits events. Admissibility reasons can quote excluded
material, so only structured public orders (rule, status, use, effect) cross that
boundary. Admissibility testimony is explicitly marked `purpose:admissibility`, is
withheld from the merits judge and jury, and cannot support merits findings.

Jurors see only published permitted exhibits, heard merits testimony, public
directions and statements actually spoken in the jury room. Publication and jury
presence are independently enforced. Pending/provisional answers never enter their
contexts. Public deliberation enters later jurors' packets before their next calls;
private ballots and private notes do not. Courtroom transcripts retain exact speech;
the deliberation log stays sealed in the authoritative journal.

A persistent model cannot unsee withdrawn evidence. Exclusion, reduced permitted
uses, struck testimony and corrections therefore cause affected merits contexts to
be retired and rebuilt from permitted history before another call. Retired handles
are never reused. Potentially derived speech during the exposure interval is
conservatively quarantined too; contaminated private notes/ballots are not replayed.
This can withhold otherwise valid intervening testimony, so re-present necessary
material prospectively rather than pretending a model forgot a contaminating fact.
The exact original transcript stays intact for audit. Session IDs ordinarily remain
stable; unsafe resume and information withdrawal are explicit recorded exceptions.

## Persistence and failure

`.world/court-v2/runtime.json` holds sealed identity/session mappings, per-identity
committed conversation history, retired handles, provenance and pending operations.
The mock backend holds separate restricted files per conversation. The OpenCode
adapter records session ownership, model assignment, working directory and message
fingerprints in private external storage, and checks the provider's history before
resumption. Altered or missing history causes an identity-only rebuild. Atomic writes and
exclusive runtime/controller locks prevent conflicting turns. A crashed model send
is not retried blindly in a possibly changed context: rebuild that identity only.
A pending event commit is reconciled against the journal to avoid duplicate speech;
ambiguous divergence fails. Projection recovery uses the authoritative journal.

## Honest security boundary

Filtered packets plus genuinely separate model contexts give strong application-level
isolation. The trusted adapter must actually provide it: flags and opaque handles
cannot prove what an external provider does internally. Provider infrastructure,
model weights and transport may be shared outside this program's control. A malicious
adapter or host operator can defeat application protections; neither is untrusted
model output. Tests exercise persisted mock conversations, the real OpenCode adapter
against a deterministic fake HTTP server, and the guard's hooks. Live provider
integration is a separate opt-in smoke test, never inferred from those test results.

Models can still make semantic mistakes or quote information they legitimately heard
into an explicit event. The program validates routing/provenance, not all legal
inferences or the truthfulness of speech. Corrections remain explicit. Fixed history,
entertainment pacing, either side, civil/criminal, bench/jury and US/NSW/custom styles
remain intact. No filing queues, calendar simulation or jury-selection bureaucracy
are introduced.

## Grounding checks after speech

The player may use `// ground` (latest heard witness answer) or `// ground T0123`.
The corresponding CLI is `python3 tools/courtroom.py ground --target T0123 ...`.
Private answers not heard by the player cannot be queried through this control.
Sampling is independently drawn by the controller and persisted before recording
the answer; an unfinished sampled check blocks further model answers and resumes
after restart. Runtime `grounding.sample_rate` ranges from 0 to 1 (default 0.1).
`grounding.model` optionally overrides the checker provider/model/reasoning;
otherwise the bench default is used. Zero disables sampling, not the player control.

Every check gets a fresh isolated technical context with only the witness's permitted
sources at answer time, public rules, and the target question/answer. No global truth,
other witness packet, later discovery or private player strategy is supplied. The
checker returns supported, supported_uncertainty or missing_coverage plus source
references. It cannot write replacement testimony. Authored uncertainty must cite
an owned boundary. These references and the assessment request remain sealed.

A failure appends a technical correction and pauses. The exact original answer stays
in the journal; the answer and conservatively dependent intervening material are
withdrawn from character packets. Affected sessions rebuild without their polluted
private notes. Unaffected identities retain their sessions. Ballots/verdicts clear
and decisions can be reopened after a grounded repair. Technical interruptions are
not portrayed as hesitation, evasion or credibility evidence inside the scene.

The checker is fallible. A pause or check result is a meta-signal the human cannot
unlearn; this limitation is disclosed, not disguised. Checking supplements authoring
depth and does not make it safe to improvise historical colour.

## Amendment consistency exception

The fresh consistency checker receives the targeted substrate entry, linked events
and affected identities' committed views, limits and divergences. This scope is
computed from shared entry references; V2 has no manual amendment_consistency map.
It is a documented exception to the no-sealed-truth rule for a technical session
that never speaks in court, returns pass/fail with reasons, and closes after each
check. Unrelated truth, player strategy, side, desired outcome and live transcript
are withheld. Authors receive only the precommitted blinded excerpts.

Each candidate has a separate fresh author session with identical inputs. Any
failed candidate rejects the entire set; retries use fresh authors and checker,
capped by amendments.max_attempts. Receipts retain attempts, selection and sealed
alternatives. The original commitment survives. Changed projections rebuild each
affected context independently and dependent decisions reopen. Semantic consistency
and the candidate distribution remain fallible; deterministic reference checks do
not establish exhaustive real-world truth.
