# Stage 5 follow-up report — envelopes, independent authors and consistency scope

**292 deterministic tests run, 292 passed.** These follow-ups began after delivery
of the Stage 1 revision report. The later no-player-rulings amendment is documented
separately. No live amendment or revised live rehearsal was run.

## Rehearsal-derived envelopes

Each accepted blind-examiner probe gap generates a sealed, digest-bound envelope.
The pre-play probe supplies its topic; the affected packet supplies the witness
layer/entry, permitted family/boundary source references and preservation constraints.
No extra generation model supplies historical facts. Probe IDs and exact answer
digests preserve provenance. Rehearsal after a patch removes a no-longer-missing
probe from the generated set. Author-declared envelopes remain supported, and original
precommitted envelopes survive later amended revisions with their source attribution.

Reports count author and rehearsal sources separately. The mixed-source deterministic
fixture produced **1 author envelope and 1 rehearsal envelope**. The fresh local draft
contains **2 author-declared envelopes**. Its revised live rehearsal has not run, so
there is no live rehearsal-derived envelope count to report.

An envelope is not a waiver of the coverage gate. A hearing-plausible gap still blocks
commitment. Only diagnostic gaps already allowed by the gate may remain at commitment.
Three-way grader splits first return to authoring; they are not treated as accepted gaps.

## One independent author per candidate

Each attempt uses three fresh independent author sessions with identical blinded
inputs. Each produces one candidate; none sees the other candidates, previous attempts,
player theory, side, desired outcome or live transcript. A fresh checker tests the
complete set. Any failed candidate rejects all three; duplicate completions also
reject the whole set. There is no cherry-picking from a failed attempt.

Rejected sets retry with new authors and checker, up to `amendments.max_attempts`
(default 3, configurable 1–5). Only a fully accepted set reaches uniform system-random
selection. Attempt counts, limits, handles, candidates and checks are sealed. A
successful receipt binds the attempt history; exhausted requests retain their history
in sealed runtime state and leave play paused. Backend/protocol errors fail closed
and preserve the error attempt rather than being passed off as a valid candidate set.

The retry test rejects the first set and accepts the second: six separate author
contexts, two separate checker contexts, identical author inputs, and exactly one
random selection from the accepted three. Cap-exhaustion and duplicate-set tests
prove that no rejected candidate is applied.

## Cross-witness consistency access

Confirmed: the prior checker saw only the target witness's packet. It now receives
topic-scoped committed accounts from other affected witnesses, selected by the
precommitted `amendment_consistency[topic]` reference map. Every witness must be
accounted for; an empty list explicitly records no relevant account. Invalid source
owners or omitted target anchors are rejected. Missing scope blocks commitment and
amendment, including through the rehearsal command's final readiness check.

In the current free-text format this scope must be authored before commitment. A
generated envelope is therefore not immediately playable if its scope is missing:
the fresh author completes the reference map and re-rehearses the changed draft.
The controller does not claim that lexical search proves semantic relevance or that
an omitted contradiction has been checked. Deriving affected projections from a
shared substrate remains work for the forthcoming Authoring V2 specification.

This is the documented exception for a fresh technical checker, not courtroom roles.
It receives only scoped committed accounts, constraints and public rules, returns
pass/fail with reasons, and closes after the check. Reasons remain sealed. Candidate
authors, witnesses, counsel, judges, jurors and player never receive the extra excerpts.
Global author truth, unrelated private facts, live strategy and transcript remain
outside its inputs. Canary tests verify both the intended scoped access and exclusions.

## Review and limitations

The full diff review also closed two grounding boundary bugs: rebuild bookkeeping
is stripped from model payloads, and a withdrawn answer cannot justify its own repair.
The entire deterministic regression suite passes. All 34 protected-case files match
their saved hashes; Last Light and Second Signature remain blocked.

Independent authors can still share biases. A topic reveals the direction of inquiry.
The scope map and consistency checker remain fallible, especially without the future
shared substrate. Reference validation proves ownership, not completeness or semantic
entailment. All accepted meta-signal limitations remain disclosed.
