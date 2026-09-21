# Stage 4 report — player and sampled grounding checks

Implementation verified: **254 deterministic tests run, 254 passed** at the Stage 4
boundary. This report was written retrospectively after the requested reporting
order was missed; it does not claim it was delivered before Stage 5.

- `// ground` checks the latest witness answer heard by the player;
  `// ground T0123` targets a particular recorded answer. CLI `ground --target`
  exposes the same operation. Private unheard answers cannot be inspected.
- Random sampling is independent of whether a witness reports a gap. Runtime
  `grounding.sample_rate` is configurable from 0 to 1, default 0.1.
- Sample selections are persisted with the answer transaction. An unfinished
  sampled check blocks subsequent model answers and is recovered after restart.
- Each referee call uses a fresh isolated technical session with only permitted
  sources at answer time, public rules and the target answer/question. No later
  discovery, other witness knowledge, sealed truth or private player theory enters.
- The only accepted results are supported, supported uncertainty and missing
  coverage, with permitted references. No replacement speech/facts are accepted.
- Failed checks preserve the original journal, mark the answer corrected and pause.
  Affected contexts rebuild without contaminated notes/record. Unaffected witnesses
  retain their contexts. Ballots and verdicts are invalidated.

Tests include confident invention without a gap signal, historical source cutoff,
private strategy/truth canaries, unavailable check/restart recovery, embedded court
answer withdrawal, affected-only rebuilds, foreign-reference rejection, no replacement
speech, and owned uncertainty references.

Limits: a referee is fallible; a 10% sample does not check every answer. The player
cannot unlearn a pause or a check result. These are disclosed technical signals,
not in-world credibility evidence. This stage does not replace authoring depth.
