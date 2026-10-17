# Harness changelog

One line per approved change to the harness (`CLAUDE.md`, `modules/`, `tools/`, evaluation targets). The harness version stamped on each watch is the short hash of the last commit touching those paths (`python3 tools/wk.py stamp`).

| Date | Proposal | Files | Targets | Baseline |
|---|---|---|---|---|
| 2026-10-17 | — (initial prototype) | `modules/tng-d/`, `modules/eval/`, `tools/wk.py`, `CLAUDE.md` § Structured worlds | all | none yet |
| 2026-10-18 | — (lore audit, initial) | `modules/tng-d/law.md`, `forces.md`, `voices.md`, `justice.md`, `deeds.md`, `canon/cards.jsonl` (36 cards) | G1 | 8 errors, 16 risky, 8 missing found by a fresh-context audit against season one |
| 2026-10-18 | — (physics charter) | `modules/tng-d/physics.md`, `canon/mechanisms.jsonl` (14 cards, M-001 to M-014), `tools/wk.py` (calc, CALC/ROLL re-checks, unknowns, hypotheses), `CLAUDE.md` § Structured worlds, `modules/eval/LORE_AGENT.md` physics mode | G1 | none yet |
| 2026-10-18 | — (physics refinements, approved by Will) | `physics.md` (cards case by case, nobody speaks past a card's edge, open problems in-universe, canon contradictions settled by physics, Trek vocabulary on screen, rolls as scoped observations, P2 covers ships and fields, P4 covers disintegration), `canon/mechanisms.jsonl` (M-015 supersedes M-008), `tools/wk.py` (`reinterprets`, `revives`), `STATE.md`, `LORE_AGENT.md`, `LOOP.md`, `CLAUDE.md` | G1 | none yet |
| 2026-10-18 | — (P5, Will's ruling) | `physics.md` (P5 neutrino conversion added; P4 back to transport only), `canon/mechanisms.jsonl` (M-016 supersedes M-015), `tools/wk.py` (P5 in the closed list), `LORE_AGENT.md` | G1 | none yet |
| 2026-10-18 | — (Riker's shoes, Will's ruling) | `law.md` (Lloyd lived Riker's life; invariants listed; non-material details his), `voices.md`, `deeds.md`, `canon/README.md`, preset `README.md`; world: `charter.md`, new `sheet.md` | G1 | none yet |
| 2026-10-18 | — (runs from disk, Will's ruling) | `tools/wk.py` (post-commit push hook; save/fork/holodeck push their refs; holodeck mirrors main's reset), `CLAUDE.md` § Structured worlds, `STATE.md` § Timelines, both READMEs | — | none yet |
