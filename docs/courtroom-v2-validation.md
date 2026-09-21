# Courtroom v2: executed checks and limits

Build date: 21 September 2026.
Base for installation: trial/courtroom-v1 at 8455080a5fc8eda5c3ad360fa1f5e10b32b7a0ca.
Paused controller recovered from Git blob 2149253cee3714e386dd958a66059a8f6f4507fc.

## Actually executed in this build

Python 3.13.5 on Linux; standard library only.

`python3 -m unittest discover -s tests -v` in the isolated v2 build:
**96 v2 test methods passed.** One method exercises 48 civil/criminal, bench/jury,
style, party and pacing combinations. Another exercises both complete starters in
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
two starters are complete examples; a new-case scaffold intentionally fails
validation until authored. Real-world court-system fidelity is not asserted.

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
Claude generation was performed; those remain pending the user's authentication.
