# Stage 3 report — repair requires a basis

Implementation verified: **245 deterministic tests run, 245 passed** at the Stage 3
boundary. This report was written retrospectively after the requested reporting
order was missed; it does not claim it was delivered before Stage 4.

Bare repair no longer resumes play. The recorded resolution names the latest fault,
the affected witness/source owner, permitted source references and one of:

- Delivery repair: committed, entitled sources were actually omitted from the
  recorded delivery. Already delivered sources cannot use this basis.
- Supported resolution: existing permitted facts or authored boundaries supply
  the stated basis. No new historical text can be inserted through repair.

Labelled amendments use their separate explicit-choice workflow. A forged
`kind: amendment` repair is not accepted. Repairs reach the player as technical
notices, not as dialogue to witnesses or factfinders.

Tests reject bare repair, another witness's sources and false delivery repair;
they exercise a real simulated omission and confirm the committed case is unchanged.
Existing decision reopening and invalidation tests remain passing.

Limit: the deterministic controller checks provenance/allocation, not logical
entailment of free-form language. A cited source is not a semantic proof. The
referee and coverage rehearsal remain fallible semantic checks around this boundary.
