# Stage 1 amendment report — no player rulings

**292 deterministic tests run, 292 passed.** No revised live rehearsal ran.
This supersedes the default human-appeal path in the earlier Stage 1 revision report.

## Default dispute resolution

The first two graders still work in separate contexts. When they disagree on either
classification or hearing-plausibility, a third fresh session receives the identical
frozen witness answer batch, permitted sources, public rules and setting. It sees no
peer assessments and is not told which outcome would break the tie. Sending the
whole original batch preserves identical context; its vote is used only for primary
disagreements. The extra session closes after grading.

Classification and hearing-plausibility are each decided by majority. A three-way
classification split remains a defect and blocks commitment. The sealed report returns
an exact patch target for a fresh pre-play author; `author_patch_packet(case, witness)`
supplies that witness's permitted sources, rules and targets for the authoring handoff.
The revised draft must undergo a complete new rehearsal. Changed facts invalidate
the old report. No model invents a replacement ruling or treats a split as a pass.

This gate returns an authoring handoff; it does not automatically launch an unbounded
author/patch/rehearsal loop. No real split or live draft patch was processed in this
verification run. The authoring host must consume the sealed handoff in a fresh context
and return the revised draft through rehearsal before offering it for play.

The player sees counts and readiness status, never the sealed sources or assessments.
Every witness report includes the raw two-grader agreement numerator, denominator
and rate, the number of answers requiring a tiebreaker, and three-way split count.
Majority resolutions do not inflate the primary agreement rate.

## Exceptional human path

The retained `coverage-rule` command now requires both `--confirm-human-review` and
`--reviewer-will-not-play`. The second declaration is also required by the Python API,
recorded with the ruling and bound into the report digest. It is not enough merely
to supply a reviewer name. Human rulings cannot overwrite an existing majority or
silently bypass source ownership checks.

The declaration protects the workflow; software cannot verify a person's future
intention to play. Human review is optional and outside the default player workflow.

## Evidence

Dedicated tests exercise:

- Actual third-session invocation with identical frozen inputs and no peer verdicts.
- Separate session IDs and closure of the tiebreaker session.
- Majority classification and a separate hearing-plausibility disagreement.
- A three-way split, sealed author patch handoff and mandatory new rehearsal after
  the author changes the draft.
- Rejection of human review without the nonplaying-reviewer flag through both CLI
  and Python entry points.

In the synthetic one-witness exercise, primary graders agreed on 52 of 53 answers
(98.11%); one answer invoked the tiebreaker. The majority fixture had zero splits;
the adversarial fixture had one split and was blocked. These are scripted controller
tests, not observed live-model agreement rates.

The original 100% coverage threshold, per-family depth, separately counted probes,
mock refusal and digest binding remain. Third graders are fallible and can share
errors with the first two. The fresh case remains blocked; earlier live findings
remain in the preceding revision report. Last Light and Second Signature remain
unchanged and blocked.
