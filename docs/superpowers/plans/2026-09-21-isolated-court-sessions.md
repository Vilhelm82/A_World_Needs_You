# Isolated courtroom sessions implementation plan

## Required design

Implement the user's seventeen-point specification against b4b6a03, in the selected
checkout and branch. Python 3.10+, standard library, no network calls in tests.
The deterministic orchestrator never generates character content. A trusted backend
adapter must guarantee independent persistent contexts, exclusive identity ownership,
and no ambient filesystem/tools/shared memory in role sessions. Missing capability
or duplicate physical context handles is a startup error. The human has no session.
The judge has separate admissibility and merits contexts; every juror is separate.

## Implementation sequence

- [x] Add failing session-boundary tests using artificial cases and canary secrets.
- [x] Implement backend protocol and isolated durable deterministic backend.
- [x] Implement sealed runtime ownership, restart, safe per-identity rebuild,
      request routing and provenance-bound controller recording.
- [x] Implement separate examiner/witness turns, mediated jury round robin and
      deterministic verdict aggregation; retain all existing court configurations.
- [x] Quarantine revoked evidence and derived reasoning; replace contaminated merits
      contexts instead of asking models to forget. Reject ambiguous crashed sends.
- [x] Replace optional/single-context instructions with required orchestration,
      adapter contract, startup commands, mock-only limitations and security boundary.
- [x] Inspect complete diff, run all tests and verify manifest.
- Delivery: commit locally and push the verified revision on the requested branch.

## Review focus

Duplicate session/context IDs, backend resume misbinding, concurrent sends and
crashes, evidence revocation after delivery, model-authored cross-role events,
private deliberation/ballot leakage, and raw controller bypass. Tests must inspect
actual persisted backend conversations, not just packet construction. Fixtures and
low-level state-machine tests are offline tests, not permission for live roleplay.
