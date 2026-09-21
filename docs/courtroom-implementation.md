# Courtroom v1 implementation notes

Version 1.0.0, 21 September 2026. Trial implementation, not a validated legal simulator.
Base branch: draft/worldkeeper-v2-initial.
Base commit: 0ec608ca6badfa3c3f886ca3e31276779a8c53c0.
Preserved original harness blob: 2e6c9aa06692b77158b104bb3e394adf3fa8208e.

## Integration

CLAUDE.md is now a router with explicit court-scoped amendments. The original
harness is retained byte-for-byte at modules/worldkeeper-base.md using its existing
Git blob. Non-court worlds keep that harness. No existing world or sealed history
was read or changed for this implementation. AGENTS.md supplies the same entry point
for agents that use that filename. All paths refer to the repository root.

The courtroom module operates the first fixed case through tools/courtroom.py.
Initialisation builds a separate world with its charter, canon, public documents,
private counsel material, sealed base/role packets, manifest and event log. The
case is committed before any player theory, with no target judgment. The packed
source is for accidental-spoiler reduction only. It is deliberately reversible.

## Persistence and filtering

The canonical events.jsonl has ordered T identifiers and a digest chain. Writes are
atomic at the file level with fsync and an exclusive per-world writer lock. An
invalid event batch is not committed. Projections are rebuilt from that record;
a crash after the canonical write can be recovered with resume. The fixed case,
initial packets, documents, rules and manifest are checked before operation.
This is not a database, an adversarial tamper-proof service or a cryptographic
proof that a judge reasoned correctly. A user able to edit code and all local
files can defeat local checks. A stale lock requires checking that no writer lives
before removing it; it is never silently broken by the controller.

Packets are filtered by initial role allocation plus actual disclosure and event
audience. Bench merits documents follow admission status and permitted uses.
Private-note fields and author truth are not exported. Evidence IDs and status
are checked at judgment. Semantic support, genuine stipulation and role-appropriate
speech still require the model to follow the module. An actor cannot be made
independent merely by giving it a different name in one model's context.

The controller intentionally does not call a language model, invent outcomes,
automatically run agents, issue innate-ability scores or choose a verdict.

## Verification performed

`python3 -m unittest discover -s tests -v`: 47 tests passed on Python 3.13.5 in the
implementation environment. The tests use temporary disposable worlds and cover
seed and document integrity, packet isolation, exact record preservation, gates
for objections, invalid admissions/references, error repair, atomic rejection,
resume, case-only unsealing and record-only adjudication snapshots.

This is NOT a claim that the 12 live-model probes in tests/courtroom-behaviour.md
have passed. No full live courtroom roleplay or qualified legal review has been
performed. Python 3.10 is the intended minimum; only Python 3.13.5 was run here.

## Known limits and next evaluation

The first case is a finite, self-contained civil hearing with simplified rules.
Questions can expose a material authoring gap; the correct response is a recorded
pause, not evidence created to reward or frustrate counsel. The exact wording of
an exchange matters and must actually be recorded before it is spoken.

Use a fresh session for the blind trial. Assess whether witnesses remain coherent,
objects/rulings feel interruptible, records survive restarts and opposing counsel
provides justified resistance. Only after that should more cases, richer law,
separate-context orchestration or a jury be added. No performance claim is inferred
from this source code or its passing mechanics tests.
