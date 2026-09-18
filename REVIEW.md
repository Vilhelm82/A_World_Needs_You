# Worldkeeper v2 — review of the draft (18 Sept 2026)

## Status

**Design stage, rulings pending.** `DESIGN_NOTES.md` is the design deliverable. `CLAUDE.md` and `README.md` on this branch are a first draft against it.

Lines marked **(Will)** are his stated requirements. Everything else is Claude's assessment and is open to overruling.

## The brief, as restated by Will

As restated 18 Sept 2026:

- **(Will)** Generalise the v1 framework (A World Needs You) for a wider use case.
- **(Will)** Draw on popular online frameworks that aim at the same experience: a consistent, coherent world that keeps developing as the user explores its environment and characters.
- **(Will)** Base the mechanics on v1's "Building the world" section, adapted to the wider use case.
- **(Will)** Runnable from just the git repo and its MCP tools.
- **(Will)** Remove everything belonging to v1's original purpose. The `~` mark is part of that purpose, not engine.
- **(Will)** Stages: design and research first, build second.
- **(Will)** Concern: v1 had a real magic in how its narrative evolved. Do not lose it by removing parts of v1 that merely look harmless to remove.

## Draft against brief

| Requirement | Verdict |
|---|---|
| Generalisation | Met in structure: charter plus dials. |
| Draws on existing frameworks | Met. Twelve borrowed mechanisms with sources. Tabletop references are from memory, not lookup. |
| Built on v1's "Building the world" | Met. Truth-first, people spec, lying source, growth from decisions kept as the spine. |
| World develops through exploration | **Not met.** See below. |
| Repo plus MCP tools only | Mostly. Two gaps below. |
| v1's purpose removed | **Not met.** Relocated onto dials rather than removed. |

### Exploration hole

The draft is still situation-shaped. `hook: none` exists, but the truth schema still requires `resolutions` and a `distance` scale, which mean nothing with no central trouble. There is no frontier rule: people are "made in full before they speak", places get no equivalent for when the character walks somewhere the truth has not built.

### Runtime gaps

- Checkpoints commit but never push; push happens only at stand down. On an ephemeral clone a dead session loses every checkpoint.
- Nothing tells a session to read `CLAUDE.md`. Claude Code auto-loads it; a chat session driving MCP tools does not.
- Open question: which runtime? Local Claude Code, Claude Code on the web, or chat plus Desktop Commander.

## Residue of v1's purpose still in the draft

Clear cuts:

- `marks` dial, the Marks paragraph, the `MARK` ledger line, "A mark?" in the turn loop.
- `standdown` dial and "stand-down answers" in the record.
- The "v1 as a preset" section of `DESIGN_NOTES.md`.
- The "yours to know, never said" framing of the purpose section.

Will's call:

- `distance` and before → after on each `DID` line.
- `records/`, sealed, with truth snapshot and audit per watch.
- `hook: need` as the default.
- "Watch" and "stand down" as vocabulary.
- "Prefer situations where how the person thinks is what is needed. Never say so." Tailoring to a *character* is ordinary craft; tailoring covertly to the *person* was v1's purpose.

## Double duty: where the magic may live

Pieces of v1's rig also shaped the model's behaviour. Cut by function, not by origin.

- **A master other than the player.** v1 made the model answer to the truth, the record, and a later reader. That is what resists drift toward pleasing. Remove the purpose and this needs a replacement. The draft's "refuse the mirror and the template" is a negative purpose and may not pull as hard.
- **Distance before → after.** As a score, measurement. As a habit, it forces causal accounting before narration. Keep the accounting; change the yardstick to pressures and movers.
- **The audited record.** Makes fudging detectable. Keep an auditor: the player after a world ends, or a fresh-context reader.
- **"Never a test, never a game."** Suppresses the game-master register.
- **No narrator.** Not instrumentation, but the draft demoted it to a dial and defaulted to second-person narration, the generic roleplay voice. Probably the largest single loss.
- **Absolutes.** v1 is short and every rule is always or never. The draft is 2.4× longer and hedges most rules with "unless the charter says". Proposal: resolve dials once at build time into a per-world rule sheet written in absolutes, so the running session never reads a conditional.

Safe to cut: the `~` itself, the clock question, the office. Keep what rode along: a way to let the world tick without acting, and a closing speech naming which decisions were the character's.

Test rather than argue: compare candidates against a v1 world in fresh sessions. **Not `world/alder`** — Will has ruled it out as evidence or baseline; it was a quick session he lost interest in and abandoned. A baseline has to come from a world that worked.

## Repo housekeeping

- No `main`. The default branch is an auto-named `claude/...` branch. The migration plan in the design notes assumes `main`.
- `worlds/alder/` carries a nested `CLAUDE.md`, which would load alongside a root harness.
- The design notes mention three worlds; this repo holds one, and that one is ruled out as a baseline.

## Open questions for Will

1. Which moments carried the magic: the people, consequences landing late, or the discoveries?
2. Runtime.
3. Rulings on the seven judgment calls in `DESIGN_NOTES.md`, and on the "Will's call" list above.
