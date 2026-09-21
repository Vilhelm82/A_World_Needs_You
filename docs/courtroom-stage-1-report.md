# Stage 1 report — coverage rehearsal readiness gate

Status: implementation and deterministic verification passed. No claim of live
coverage for a new case is made in this report.

Reporting correction: a brief progress update was sent before Stage 2, but this
reviewable report was not delivered then. Subsequent stages were started before
this reporting omission was corrected.

## Thresholds

These thresholds were stated to the player before enforcement:

- Every witness must answer all seven ordinary foundation areas.
- Each area must have at least two distinct natural follow-ups generated after
  the foundation answers: at least 21 ordinary questions per witness.
- 100% of ordinary answers must be assessed as grounded or authored uncertainty.
- Any ordinary gap or unsupported invention blocks commitment.
- Deliberately unauthored probes are counted separately and must all return gaps.

The implementation additionally sets a minimum of two deliberate probes per
witness. That minimum was reported during Stage 1 implementation; it was not in
the initial threshold announcement.

The seven areas are occupation/experience, training/qualifications/licences,
actual activity or observations, tools/materials/equipment, purpose/authority,
knowledge basis, and recall/perception limits.

## What the gate does

1. Creates a separate rehearsal witness session, examiner session and checker
   session for each witness, using the existing backend abstraction.
2. Exercises the seven foundation questions from that witness's permitted packet.
3. Has the examiner generate two natural follow-ups per area after seeing those
   foundation answers; exercises those questions against the witness.
4. Exercises at least two author-declared deliberately unauthored probes. The
   witness is not given an expected-answer label for those questions.
5. Has the independent checker classify every answer as grounded, authored
   uncertainty, gap or unsupported invention, with permitted source references.
6. Saves the exact questions, answers, assessment records and session handles in a
   sealed report embedded in the output case. Failed reports are saved for review
   but cannot authorise commitment.
7. Binds the report to the case and each permitted packet by digest. Changed case
   content requires a fresh rehearsal. Closes the practice sessions; their answers
   do not enter live testimony or live witness history.

Live startup rejects mock rehearsal reports. Deterministic tests explicitly opt
into synthetic reports; they are not represented as provider-backed rehearsal.
Last Light and Second Signature remain blocked.

## Verification at the Stage 1 boundary

Complete deterministic suite: **237 tests run, 237 passed**.

Seven new coverage tests exercised:

- Refusal to commit an unrehearsed case, before world storage is created.
- Invalidation when authored case content changes.
- Refusal of ordinary gaps and unsupported inventions.
- Separate treatment and rejection of failed deliberate probes.
- Refusal of missing follow-ups and references to another witness's sources.
- Refusal to use a mock report for live commitment.
- Actual rehearsal orchestration through isolated scripted sessions, including
  independent assessment, closed practice sessions, exclusion of author truth and
  cross-witness canaries, and absence of practice answers from live packets.

The scripted rehearsal exercised **42 ordinary answers and 4 deliberate probes**
across two synthetic witnesses. Its expected result was 42 grounded ordinary
answers and four probe gaps. These counts verify execution and gate mechanics,
not the factual adequacy of a newly authored playable case.

## Live evidence retained from before this build

The earlier Grok 4.3 / medium smoke check used one synthetic witness:

- Three covered foundation questions: three substantive answers, zero gaps.
- One deliberately unauthored exact-time question: one gap and pause.
- Overall: one gap in four questions; zero gaps in the three covered questions.

That check predates this larger rehearsal gate. It is not a full Stage 1 rehearsal
and is not evidence that a new case passes the new threshold.

## Limits and outstanding evidence

The grader is a model and can misclassify an answer. Source-reference validation
checks allocation and existence, not logical entailment. An examiner can produce
weak follow-ups despite meeting the count and linkage checks. A finite rehearsal
cannot guarantee coverage of arbitrary future questions. Local authored inputs
and reports are trusted files, not cryptographic provider attestations.

Consequently, a new case must undergo a real rehearsal before it is offered for
play. Its ordinary-answer and probe counts must be reported separately, including
failures. At the time this report is delivered, the fresh-context case author is
still working and that new-case live report is pending.

## Files and use

- `tools/courtroom_rehearsal.py`: rehearsal execution, report validation and counts.
- `tools/courtroom_grounding.py`: permitted-source catalogue.
- `tools/courtroom_v2.py`: commitment/readiness gate.
- `tools/courtroom.py`: rehearsal command and live/mock separation.
- `tests/test_courtroom_coverage.py`: coverage-gate regression tests.

```bash
python3 tools/courtroom.py rehearse \
  --case /private/draft.json \
  --out /private/rehearsed.json \
  --config "$HOME/.config/courtroom/runtime.json"
```

The output contains private witness knowledge and assessments. It must remain
sealed. A successful gate is necessary before startup; no hearing is started by
the rehearsal itself.
