# Courtroom v2: executed checks and limits

Build date: 21 September 2026.
Base for installation: trial/courtroom-v1 at 8455080a5fc8eda5c3ad360fa1f5e10b32b7a0ca.
Paused controller recovered from Git blob 2149253cee3714e386dd958a66059a8f6f4507fc.

## Actually executed in this build

Python 3.13.5 on Linux; standard library only.

`python3 -m unittest discover -s tests -v` in the isolated v2 build:
**96 v2 test methods passed.** One method exercises 48 civil/criminal, bench/jury,
style, party and pacing combinations. Another exercises both historical example structures in
both forums, on either side, under both standard styles. Those are matrix checks,
not 48 independent live-model trials or extra test methods added to the count.

Executed CLI checks include validation, initialisation, verification, packet export,
new-case scaffolding and restart recovery. Regression probes cover timely flow
objections, strict pre-answer gates, no reference to an unanswered question,
private counsel strategy, juror ballots and deliberation privacy, unpublished and
excluded exhibits, limited uses, absent-jury testimony, exact wording, atomic event
batch rejection, stale writer/lock rejection, tampering, explicit error repair,
case-only unsealing, per-count mixed/hung results, and record-only decision snapshots.

The saved draft was corrected to avoid leaking the counsel brief to jurors,
unpublished exhibits to jurors, and pending answers to absent witnesses. Jury
ballots cannot be returned by counsel or the judge. A first split ballot cannot
silently become a completed deadlock. Admission and publication are distinct.

## Installer verification

**11 installer tests passed** in disposable local repositories. These include a
successful application that really ran all 96 v2 tests and made a local Git commit,
rollback after an intentionally failing test, no-tests rejection, dirty/wrong-base/
wrong-branch refusal, symlink protection, payload checksums, source extraction and
refusal to push to an unexpected origin. This was not the user's actual checkout;
no real remote push was performed in these installer tests.

## Not executed or claimed

The supplied archive was installed locally at commit 06bfee8. At that point all
143 tests passed (96 v2 and 47 v1). The user confirmed that v1 had never been played
and was a rejected prototype, so the v1 controller, fixtures, tests and routing
have since been removed. Those 96 state-machine tests are retained, with the CLI startup test migrated to
the required session runtime. Additional session-isolation tests are maintained in
`tests/test_courtroom_sessions.py`; run discovery for the current total.

No full live-model hearing, independent multi-agent trial, human legal review,
calibrated jury simulation or entertainment user test has been completed. The
controller validates packet structure and references, not the semantic truth of a
quotation or inference. Independent persistent contexts are now required, exercised
with a durable deterministic backend. The OpenCode adapter is additionally tested
against a fake HTTP server and the actual JavaScript guard, without external models.
The application cannot
prevent an operator with full write access from altering files and all their hashes.

New cases are authored by the host agent, not by an embedded network service. The
two historical examples are no longer considered ready for play: witness background
was insufficient despite structural validity. They now fail the readiness gate.
A new-case scaffold intentionally fails validation until authored. Real-world
court-system fidelity is not asserted.

## Local-first delivery

The archive was applied to the user's local checkout, committed there, and pushed
using existing Git authentication. Subsequent changes follow the same workflow.
`BUILD-MANIFEST.json` describes the current maintained payload; the original source
archive retains the original build checksums. Non-court worlds are unchanged.

## Required multi-session architecture verification

Before OpenCode integration, the complete discovery suite passed **143 tests** on Python 3.14.4:
96 retained controller tests and 47 session-orchestration tests. Tests inspect actual
persisted deterministic backend conversations, separate session/context handles,
role-specific canaries, separate judicial contexts, journal-before-call ordering,
flow/strict examinations, repeated safe rebuilds, interrupted sends and journal
commits, round-robin restart, excluded/withdrawn evidence, immutable case storage,
private ballots/strategy, backend refusal and CLI execution. No external model calls
were made. This verifies the implemented application boundary and deterministic
adapter, not provider infrastructure or live-model reasoning quality.

## OpenCode integration verification

The complete deterministic suite now passes **206 tests**: the 143 existing tests
plus 63 configuration, CLI, delta-delivery, adapter and host tests. Tests cover
provider-neutral selection, distinct persisted HTTP sessions, canary separation,
private strategy/ballots, split judges, mediated deliberation, restart, altered
history, empty external working directories, all-tool denial, missing capabilities,
failed preflight cleanup, writable runtime storage, credential nonpersistence and
the real JavaScript prompt-guard hooks. The full diff was checked for obsolete
single-context assumptions.

OpenCode 1.18.31 was installed locally. The real hardened server started and
`backend-check` passed for all 20 starter-case identities. The optional live model
smoke **ran and failed**: the exposed provider returned HTTP 403. No provider login
or local model was configured. This is not a live-model integration pass; a full
hearing or model reasoning-quality pass is not claimed. After external provider
setup, rerun `tools/courtroom_opencode_smoke.py` as documented in
`docs/courtroom-opencode.md`.

With `@ex-machina/opencode-anthropic-auth@1.8.4` installed externally, the real
managed server exposed the `Claude Pro/Max` OAuth method and again passed preflight
for all 20 starter identities. A separate installed-plugin transport check used
synthetic credentials and stubbed network calls: both role requests retained their
own messages and courtroom guard, with no tools or cross-role canaries added.
The three new deterministic tests cover external plugin configuration, source
fingerprints and authentication-only hook enforcement. No Claude login or live
Claude generation was performed at that installation checkpoint.

After the user configured provider authentication, live smoke tests passed for
`anthropic/claude-sonnet-4-6`, `openai/gpt-5.6-sol`, and `xai/grok-4.3`.
Each test created two distinct sessions, checked each model's recall of its own
synthetic canary without the other canary, and resumed both sessions through a new
backend instance. Claude initially wrapped valid JSON in Markdown; the shared
system instruction now explicitly requires raw JSON without fences. All three
providers passed after that change, and all 206 deterministic tests passed.
These are connection/session checks, not complete hearings or a measurement of
legal reasoning quality. Runtime role/model assignments remain operator choices.

## Per-role reasoning verification

The complete suite now passes **215 deterministic tests**. Nine additional tests
cover role-specific reasoning defaults/overrides, invalid settings, unavailable
levels, persisted selections across restart, legacy session compatibility,
changed-assignment refusal, dropped or altered server settings, and custom/disabled
variants. Existing CLI and JavaScript guard tests now also check advertised levels
and reject selected variants whose options were not applied.

Explicit-effort live smoke tests passed for `openai/gpt-5.6-sol` at `high`,
`xai/grok-4.3` at `medium`, `anthropic/claude-sonnet-4-6` at `high`, and
`anthropic/claude-sonnet-5` at `medium`. OpenCode's persisted user messages recorded
the selected variant; the guard checked its options before model calls. An
additional `anthropic/claude-opus-5` / `high` smoke failed with a provider
`ContentFilterError`; that model is not claimed as a live pass. No real case or
testimony-length restriction was introduced by these synthetic checks.

## Witness foundations and missing authoring

The complete deterministic suite passes **230 tests**. Fifteen new tests cover
required personal backgrounds and relevant activities, blank/placeholder rejection,
validation and startup refusal before backend construction, historical example
readability without readiness, witness-only background routing and independent
rebuilds, genuine authored memory limits, and the `authoring_gap` response through
both the orchestrator and OpenCode adapter. Gap tests cover conferences and
examination, no fabricated testimony or private-detail disclosure, no further model
calls while paused, wrong-role/mixed-response rejection, and interrupted journal
commit recovery.

A live synthetic Grok 4.3 witness at medium reasoning, with no documents in its
packet, answered three foundation questions from its authored background and
activities: occupation/work performed, tools used, and trade qualifications. It
described counting paper packs with a stock card and pencil, and stated its in-house
training and absence of a trade qualification. When asked for an exact entry time
that was not authored, it returned an authoring gap; the controller recorded only
an engine notice, paused, and produced no witness answer. This is one successful
live regression exercise, not proof that every model will recognise every omission.

The readiness gate checks required structure and obvious placeholders. Semantic
coherence and adequate detail still require the pre-commitment authoring review.
Existing Last Light world and staging files were preserved byte-for-byte; no
replacement hearing was created and no missing historical fact was backfilled.
