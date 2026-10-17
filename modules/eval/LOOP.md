# The loop — how the harness improves through use

The harness is a prototype. Each watch is a measurement, and each change to the harness is an experiment with a stated expected effect. Nothing changes mid-watch; nothing changes without Will's approval; every change can be traced to the goal it was meant to move and checked against whether it did.

## Every watch, at stand-down

After the record and the commit, outside the world's voices:

1. **Metrics.** `python3 tools/wk.py metrics worlds/<world> --watch NNN --write`. This writes `.world/evals/watch-NNN.metrics.json`.
2. **Audit.** Spawn one fresh-context agent with `modules/eval/AUDITOR.md` as its instructions and the paths it lists. Pass paths, not summaries; it reads for itself. It writes `.world/evals/watch-NNN.audit.json`.
3. **Player input.** If Will gave `// rate` (G1–G11 scores, any he likes) or `// note` lines during the watch, they're in the ledger. Nobody asks for them.
4. **Report.** `python3 tools/wk.py report worlds/<world> --watch NNN`. This merges metrics, audit and player input into:
   - `worlds/<world>/evals/watch-NNN.md`: the public scorecard. Scores, metrics against targets, finding counts by severity, and the text of non-spoiler findings. Spoiler findings appear as a count only.
   - `worlds/<world>/evals/TREND.md`: one row per watch with the harness version, so a change's effect shows up as a step in the row after it.
5. **Proposals.** Append the auditor's proposals to `worlds/<world>/evals/PROPOSALS.md` as `P-NNN`, status `pending`, each with its target goal and metric, the change, and the baseline value it should move from. Proposals with spoiler findings keep their reasoning in `.world/evals/` and show only the change itself.
6. **Lore re-audit, when due.** If the metrics say `reaudit_due` (five watches since the last re-audit, or ten new precedents), spawn a fresh agent with `modules/eval/LORE_AGENT.md` in re-audit mode over the preset's law and `canon/` cards and the world's precedents and divergences. Its corrections become proposals (superseding cards and refining precedents included). Log `REAUDIT` in the ledger.
7. Commit: `<world>: watch NNN evaluation`. Tell Will one line: the record and the scorecard are written, and how many proposals are pending.

## Between watches

- `// proposals`: list what's pending.
- `// approve P-NNN` (or `// reject P-NNN`, or `// approve P-NNN with <changes>`): Will rules.
- An approved proposal is applied as **one commit touching only harness files**, message `harness: P-NNN <short>`, and a line appended to `HARNESS_CHANGELOG.md`: date, proposal, files, the goal and metric it targets, and the baseline.
- The next watch's trend row carries the new harness version. A change that didn't move its metric after two watches is flagged in `TREND.md` for Will to keep or revert.

## Rules

- **The world never sees evaluation.** Scores and notes change the harness, never the world's facts, people or regard. *(This is what stops evaluation from turning into a mirror.)*
- **Evaluate the GM against the goals, not against Will's mood.** Player ratings are recorded and trended; they are one input, never the only one.
- **One variable at a time where possible.** If several proposals are approved at once, `TREND.md` says so, so their effects aren't confused.
- **Targets are harness too.** Moving a target needs a proposal and an approval, like anything else.
