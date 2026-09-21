# Stage 5 report — explicit, layer-addressed amended continuation

Historical checkpoint: subsequent changes are recorded in the
[Stage 5 follow-up report](courtroom-stage-5-followup-report.md), including separate
authors per candidate, retries, generated envelopes and scoped cross-witness checking.

Implementation and deterministic verification: **260 tests run, 260 passed**.
This report includes the requested layer/entry change and is delivered before work
starts on the two-grader/question-family revision of Stage 1.

## Interface

Precommitted amendment envelopes now specify `target_layer` and `entry`, alongside
a neutral `topic`, necessary `constraints`, and permitted source `refs`.

`apply_entry(case, target_layer, entry, patch)` is the projection boundary. The only
implemented layer is `witness`; its entry names the affected witness and its patch
adds personal knowledge. Unsupported substrate layers fail closed. No shared space,
time, records or flows substrate is claimed to exist yet. Those future projectors
can extend this boundary without replacing candidate selection, commitment linkage,
disclosure, rehearsal, affected-session rebuild or decision reopening.

## Pipeline and isolation

1. While paused, explicit player choice leaves strict fixed-case play for a labelled
   amended continuation. Without this choice, no author call or amendment occurs.
2. A fresh isolated author receives only the selected precommitted topic, layer/entry,
   constraints and referenced initial sources. No live question, gap explanation,
   transcript, player side, player strategy or desired outcome is forwarded.
3. The author supplies three distinct alternative completions. A separate fresh
   checker tests all three against the constraints and knowledge allocation. Any
   failed candidate rejects the entire set rather than permitting cherry-picking.
4. The controller selects uniformly using system randomness. Callers cannot choose
   an index or replace the selection with a favoured completion.
5. The revised case undergoes coverage rehearsal before application. Failed coverage
   leaves the case paused and does not add the selected historical detail.
6. The controller appends a linked amendment receipt. Original case bytes and their
   commitment remain unchanged. Candidates, selection and assessment/rehearsal
   evidence remain sealed; public disclosure contains revision linkage, not facts.
7. Changed identity projections force context rebuilds without stale private notes.
   Unaffected identities retain their contexts. Pending decisions/ballots/verdicts
   reopen; original transcript wording remains in the authoritative journal.

## Verification

Six dedicated amendment tests cover:

- Rejection before author calls without explicit choice or a precommitted topic.
- Rejection of unimplemented substrate layers; witness entry patches preserve input.
- Blinded author inputs, deterministic testing of the random-selection boundary,
  preservation of the original commitment, hidden alternatives, affected-only
  rebuilds and restart with the selected projection.
- Rejection of a candidate set containing an inconsistent completion.
- Refusal to apply a selected addition when its rehearsal fails.
- Rejection of altered parent commitments and invalid selection receipts.

The complete deterministic suite also covers the existing court, backend, evidence,
model-session isolation, transcript, repair, grounding and jury behaviours.

These are deterministic integration tests, not a claim that live amendment authors
or consistency checkers are infallible. No live hearing or amendment was performed
on Last Light or Second Signature. Neither case was modified.

## Limits

The candidate set can be skewed. Selecting a topic reveals the direction of inquiry.
Consistency checks are fallible, and an insufficient precommitted constraint envelope
cannot guarantee global consistency. The current projection layer is witness-only;
shared-substrate consistency is deliberately deferred to the forthcoming authoring-v2
specification, not approximated by undisclosed cross-witness knowledge injection.

The player cannot unlearn technical disclosures. An amended continuation is labelled
as such and is not represented as an unchanged original fixed-history case.

## Operation

```bash
python3 tools/courtroom.py amend --world CASE --topic TOPIC \
  --accept-amended-case --config /private/runtime.json
```

This command is available only for a paused fault with a matching precommitted
amendment envelope. It performs real model calls and coverage rehearsal on a live
backend. Credentials remain outside the repository.
