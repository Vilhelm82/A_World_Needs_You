# Stage 1 revision report — independent grading and broader coverage

Historical checkpoint: the default human-review path below was subsequently replaced
by the [independent tiebreaker amendment](courtroom-stage-1-tiebreaker-report.md).
Its original test count and delivery order are preserved here.

**272 deterministic tests run, 272 passed.** This report precedes implementation of
the three follow-ups accepted in the Stage 5 review. Those follow-ups are not claimed
as part of this result. No revised live rehearsal has run.

## Enforced gate

The ordinary-answer threshold remains **100% grounded or authored uncertainty**.
Any ordinary gap, unsupported invention in any group, incomplete assessment or
unresolved grader dispute blocks commitment. Mock reports cannot authorise live
play. Old single-grader reports cannot pass the revised contract.

Every answer is assessed by two independent grader sessions with the same frozen
input. Neither sees the other's output. Agreement requires both the classification
and hearing-plausibility assessment to match; valid source references may differ.
Disagreements remain in a sealed disputed list. Only a logged human decision with
reviewer, reason and source references can settle one. The ruling binds the exact
answer and assessments, and enters the report digest. Raw assessments are preserved.
Agreement rate remains the original raw agreement, even after human rulings.

There are now fifteen question families: the seven foundations, perception,
step-by-step episode, basis of each claimed fact, bias/motive, relationships, prior
statements, document exposure, and deliberately off-topic questions. Every family
has a root. Role templates specify mandatory families and depth weights; each unit
of weight requires two distinct natural follow-ups. Mandatory families have positive
weight; the original foundations stay mandatory. Counts are reported per family.

A separate blind examiner receives only the public setting and neutral role-template
name/weights. It sees no authored witness fields, documents, answers or informed
examiner output. It generates six probes across at least three families. A gap on
a hearing-plausible probe is a case defect, not a diagnostic success.

Author-declared probes, blind examiner probes and off-topic answers have separate
counts. Author probes must produce gaps. An off-topic or blind probe gap can pass
only when agreed grading or the logged human ruling places the question outside
plausible hearing coverage. Invention fails every group.

Default per-witness depth: 42 ordinary answers, 3 off-topic answers, at least 2 author
probes and 6 blind probes. Five distinct sessions are used: witness, informed examiner,
blind examiner, grader A and grader B. All close after practice; practice answers
never become hearing knowledge. Models/reasoning can be configured separately under
runtime `coverage`, without provider-specific restrictions.

## Operation and verification

`rehearse` now checkpoints the sealed report after answer batches and assessments.
A failed provider call leaves an incomplete report with owner-only file permissions;
it cannot pass readiness. No world is created by rehearsal or appeal.

```bash
python3 tools/courtroom.py rehearse --case /private/draft.json \
  --out /private/rehearsed.json --config /private/runtime.json
python3 tools/courtroom.py coverage-rule --case /private/rehearsed.json \
  --rulings /private/human-rulings.json --out /private/reviewed.json \
  --confirm-human-review
```

The second command requires actual human rulings and makes no model calls. Rulings
contain witness, answer ID, bin, references, hearing-plausibility, reviewer and reason.
It saves a new sealed output even if remaining disputes or defects still block play.
It never overwrites the input case. See the authoring guide for the exact field names.

Tests cover paired identical grader inputs with separate contexts, blind-examiner
canary exclusion, broader family counts, weighted follow-up minimums, plausible probe
failure, human confirmation, ruling digest binding, stale-answer refusal, foreign
source refusal, partial failure retention, independent runtime model assignment,
mock refusal and the existing courtroom isolation/regression suite.

The scripted runner exercised 106 answers across two synthetic witnesses: 84 ordinary,
4 author probes, 12 blind probes and 6 off-topic answers. Its artificial graders
agreed on all 106; this demonstrates orchestration and accounting, not live grader
accuracy. Dedicated disagreement tests exercise the blocking and human-review path.

## Preserved live findings and case status

The earlier small Grok check had three covered ordinary questions, all answered
without gaps, and one deliberately unauthored exact-time probe, which produced a gap.

The subsequent full **old checklist/single-grader** rehearsal of the fresh case had
63 ordinary answers: 44 grounded, 14 authored uncertainty, zero gaps and five flagged
unsupported inventions. All six deliberate probes produced gaps. By witness:

- W1: 15 grounded, 3 uncertainty, 3 flagged inventions; 2 probe gaps.
- W2: 13 grounded, 7 uncertainty, 1 flagged invention; 2 probe gaps.
- W3: 16 grounded, 4 uncertainty, 1 flagged invention; 2 probe gaps.

That exercise failed readiness. It is not a two-grader result or evidence that the
new gate passes. The fresh case remains uncommitted and has not been offered for
play. No live rehearsal is running at this reporting checkpoint. Last Light and
Second Signature remain untouched and blocked.

## Limits

Two models can share errors. Grading, hearing-plausibility judgments and follow-up
quality remain fallible. Finite coverage does not exhaust possible questions.
Reference checks verify ownership/existence, not logical entailment. Report digests
bind trusted local records; they are not provider attestations or proof that a named
reviewer was human. A pause or a grounding result remains a meta-signal the player
cannot unlearn. These checks supplement authoring depth; they do not replace it.
