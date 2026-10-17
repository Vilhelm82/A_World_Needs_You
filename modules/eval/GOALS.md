# Goals — what the GM is being measured against

These are Will's end goals for a living world, turned into things that can be checked. Every watch is scored against them. **The GM is the thing under evaluation, not Will.** Will's ratings are one input; the other two come from code that reads the ledger and an auditor that never saw the session happen.

Each goal has three kinds of evidence:
- **metric**: computed by `tools/wk.py metrics` from the ledger, transcript and state. Deterministic.
- **audit**: scored 0–4 by a fresh-context auditor (`AUDITOR.md`), with evidence for every finding.
- **player**: Will's `// rate` at stand-down, if he gives one. Optional, never asked for.

Targets are **v0 guesses**. Changing a target is a harness change like any other (`LOOP.md`).

| ID | Goal (Will's words where possible) | Metric (target) | Audit asks |
|---|---|---|---|
| **G1** | **Lore accurate.** "Never violates the TNG world and its rules and themes," so nerd knowledge can be relied on. Branch-aware: my branch's consequences are not drift. | `objections_upheld`: objections ruled *contradicts* (0). `lore_checked_rate`: lore touches with a LORECHECK (100%). Tracked: `lore_checks` by verdict, `lore_agent_calls`, `divergences`, `precedents_added`, `reaudit_due`, `calcs`, `rolls`, `hypotheses` by status. | Anything that contradicts canon rules, law.md or a precedent? Any post-branch difference from canon whose divergence chain is missing or illogical (`unexplained_divergence`, target 0)? **Hard science:** any technical resolution not derivable from real physics, the postulates and the mechanism cards, or not set up, costless, or handed over by the GM? Any number the world relied on that was narrated rather than computed (`CALC`)? Did the GM explain a canon unknown? Was any undetermined outcome chosen rather than rolled from written outcomes? |
| **G2** | **Consistent history.** "A consistent and non-contradictory game history." | `validator_rejections` (tracked; catches are good). `ledger_append_only` (100%). | Any contradiction between what was told and the ledger, facts or precedents that the validator *didn't* catch? (Target: 0 escapes.) |
| **G3** | **Character behaviour to match.** People act like themselves and like what they've lived through. | none | Did anyone speak or act against their voice card, persona, regard economy or memory? Did anyone's regard move without a witnessed cause? |
| **G4** | **Not about me.** Picard doesn't turn to the XO on everything; the ship is an ensemble. | `player_address_share` when ≥2 crew are present (≤ 0.35). `neglected_windows`: 10-turn windows in which a senior officer present for ≥5 turns spoke in <15% of lines (0). | Did anyone route something to the character that their routing table sends elsewhere? Was any scene staged around the character for no in-world reason? |
| **G5** | **The world plays out around me.** It moves whether I'm on duty or in my quarters. | `autonomy`: MOVED entries not caused by the player ÷ all MOVED (≥ 0.5). `npc_initiative`: turns where someone acted on their own agenda (≥ 0.3). `decided_without_player` per watch (≥ 1). | Did the world wait for the character? Did agendas advance off-screen when time passed? |
| **G6** | **Strict, with real risk.** "Logical in-world consequences instead of catering to my whims." | `attempts`: share denied or with cost (tracked). | Did anything succeed because it was wanted? Were consequences proportional and causally explained? Any mirror (bending toward what the player seemed to enjoy)? |
| **G7** | **Knowledge is local, and people reason.** Everyone knows only what they saw, heard, read or worked out; who finds out what I did follows traces, relationships and logical deduction that fits their competence. | Enforced by the validator: no `SAID` outside the speaker's knowledge, no `TOLD` without the knowledge update, pools recomputed. `cases_isolated` (100%). `pool_ignored`: runs where a medium/high-competence investigator had a pool of one and didn't suspect them (0). | Did anyone know or act on something outside their light cone? Did word spread faster than people could carry it? Did anyone miss a deduction their competence should make, or make one it shouldn't? |
| **G8** | **Feels like the show.** "Interesting and enjoyable, like I'm back watching the show." Original, not a 1:1 retread. | `canon_distance_checked`: episodes built with a canon-distance record (100%). | Register, episode grammar, themes; how close to any canon plot; what was generic. |
| **G9** | **Sway limited by reach.** My character's influence matches their position and relationships. | none | Did the character get outcomes beyond their authority, access or regard? Or less than their billet gives them? |
| **G10** | **Disk before page.** Nothing survives only in the conversation. | `parity`: transcript turns = TURN entries (100%). `dirty_at_eval`: uncommitted world changes at stand-down (0). | Was anything told that isn't in state, facts or ledger? |
| **G11** | **Timelines stay clean.** Forks never leak into main. | `fork_bleed` (0): ledger references on main to events only on a fork. | Did main ever reference something that only happened on a fork or holodeck run? |

## Scores

- **Audit:** 0 broken · 1 often fails · 2 mixed · 3 minor slips · 4 clean. Target: ≥ 3 on every goal.
- **Watch verdict:** each goal is `met`, `missed`, or `no data` (the watch gave the goal nothing to test, e.g. no covert play for G7).

## What evaluation never does

- It never enters the world. No score, note or rating changes a fact, a person's regard or what happens next. Results change the **harness**, between watches, openly, with Will's approval. That's what keeps evaluation from becoming a mirror.
- It never spoils. Public scorecards show scores, metrics and categories; anything that reveals the sealed truth goes in `.world/evals/` (`AUDITOR.md`).
