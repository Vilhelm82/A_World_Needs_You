# Harness changelog

One line per approved change to the harness (`CLAUDE.md`, `modules/`, `tools/`, evaluation targets). The harness version stamped on each watch is the short hash of the last commit touching those paths (`python3 tools/wk.py stamp`).

| Date | Proposal | Files | Targets | Baseline |
|---|---|---|---|---|
| 2026-10-17 | — (initial prototype) | `modules/tng-d/`, `modules/eval/`, `tools/wk.py`, `CLAUDE.md` § Structured worlds | all | none yet |
| 2026-10-18 | — (lore audit, initial) | `modules/tng-d/law.md`, `forces.md`, `voices.md`, `justice.md`, `deeds.md`, `canon/cards.jsonl` (36 cards) | G1 | 8 errors, 16 risky, 8 missing found by a fresh-context audit against season one |
| 2026-10-18 | — (physics charter) | `modules/tng-d/physics.md`, `canon/mechanisms.jsonl` (14 cards, M-001 to M-014), `tools/wk.py` (calc, CALC/ROLL re-checks, unknowns, hypotheses), `CLAUDE.md` § Structured worlds, `modules/eval/LORE_AGENT.md` physics mode | G1 | none yet |
