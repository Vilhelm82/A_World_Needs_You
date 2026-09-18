# Worldkeeper — design notes (v1 → v2)

Working title; rename at will. v1 is "A World Needs You". v2 is the same engine with the experiment taken out of the walls and put on dials.

## Verdict

The field fights two enemies: **forgetting** (memory layers, lorebooks, summaries, state on disk) and **fudged numbers** (rules engines, real dice). One harness adds a third: **genericness**. v1 fights a fourth that almost nobody else treats as a design problem at all: **flattery** — the world that quietly becomes whatever pleases the player.

So v1 was ahead on epistemics and behind on plumbing and player control. v2 keeps the first, fixes the second, and adds a fifth thing nobody had: a clean rule for absorbing *any* request without letting requests corrode the world — **laws may change, facts may not.**

## What v1 already does better than anything I found

| v1 mechanism | Nearest outside equivalent | Difference |
|---|---|---|
| Truth written before play: hidden causes, lying sources, a resolution space with costs; consequences written before they are described | `claude-dnd`'s "secrets-first quest design" (pre-defined truth, evidence trail, NPC knowledge seeds); Lazy DM's secrets and clues; the Alexandrian's "prep situations, not plots" | v1 adds the commit discipline (write, *then* tell), sources that lie, and a record that lets the telling be audited against the truth. I found nobody else who audits. |
| Knowledge is local; nobody in the world integrates | SillyTavern "gated context injection" — keep a secret out of the prompt until a trigger fires, because models leak what they can see | They hide the secret from the model. v1 leaves it in view and makes locality a law of the world — which also hands the player a structural job: be the one who sees the whole. |
| A place, not a mirror — growth only from decisions | Community lorebooks that roll good/bad outcomes to counter the model's positivity bias | They randomise against the bias. v1 removes the bias's input. |
| Per-person praise economies | Numeric NPC attitude trackers | Nothing comparable found. A meter says how much someone likes you; an economy says what it costs them to say so. |
| No walls, only paths | Three Clue Rule; Blades' refusal to block; GUMSHOE's free core clues | v1 states the general principle. v2 turns it into a build-time check: three doors per secret, of different kinds. |
| Pressure as consequence, never a displayed clock | PbtA fronts, Blades progress clocks, threat clocks in other Claude Code harnesses | Same process underneath; v1 keeps the counter out of sight. |
| Decision log with distance-to-resolution | — | Forces a straight estimate of progress every turn. Kept as `DID` lines. |

## What the field does that v1 didn't — and what v2 took

1. **Persist before narrate, every turn, with checkpoints.** Both serious Claude Code GM harnesses enforce it; one checkpoints at scene boundaries and re-reads a compact state block after compaction. v1 wrote the carry only at stand down — which is how record 001 got lost when the PC closed. → floor 7, checkpoints at every scene change, crash recovery at open.
2. **A bounded working context.** Friends & Fables filters a "working context" per turn; AI Dungeon splits always-loaded essentials from keyword-triggered cards; SillyTavern triggers lore by keyword. v1 says read the whole truth every turn. Your third world's truth was ~25 KB at build — roughly 6–7k tokens a read. If the engine obeyed, thirty turns is ~200k tokens of the same file, which forces compaction, and compaction is when a world starts forgetting what it was told. *Hypothesis, not proof:* that is part of why long sittings had you re-telling things. → the card every turn, the truth by reach, the ledger by search.
3. **A record of the surface.** v1 tracked what is *true* and what was *decided*, never what had been *said* or who had been *told*. Everything else out there tracks established state. → the ledger's `SAID` / `TOLD` / `HAS` lines. With the compression rule, this is the direct fix for relay fatigue: `*I tell them…*` becomes a knowledge transfer on disk.
4. **Style guidance at the recency end.** AI Dungeon puts its Author's Note at the bottom of the context because position beats volume. → the charter is re-read at every scene change, and its Telling sits on the card in three lines.
5. **A control surface for the player.** Session zero, personas, AI instructions. v1 had none, on purpose. → `charter.md` plus `//`.
6. **The character is the player's.** Rule one of every RP prompt in the wild. v1 only implied it. → floor 4, with its two edges: backstory is theirs to state, and anything that solves a problem for free is an attempt.
7. **An anti-generic pass.** One harness runs a "genericness critic" over its world. → six candidates and a die when the setting is yours to choose; the *Particular* pass; *never take the first name*.
8. **Real dice, committed stakes.** The commercial platforms I read agree the model shouldn't own the numbers. → `resolution: dice`: stakes and odds to the ledger, then a shell roll, then the telling. Same principle as truth-first, one layer down.
9. **A world that moves offscreen, in bounded steps.** Faction turns, PbtA's "think offscreen too", scheduled consequences. v1 had one sentence. → `movers`, `pressures` as staged processes, and the world's own turn — deliberately small.
10. **Telegraphing.** Blades and one of the harnesses both insist on it. → *signs before blows*, which is what makes a harsh world feel fair.
11. **Safety tools.** Lines and veils; Script Change's rewind, pause, fast-forward. → Table dials and `//` commands.
12. **NPC reflection.** Generative Agents' reflection step. → *they draw their own conclusions* — from what they witnessed only, and they may be wrong.

## What I left on the shelf

- **Vector stores, Python tooling, rules APIs.** Grep over an append-only ledger does the job with zero dependencies and still runs over Desktop Commander.
- **Showing the player the world skeleton for approval.** Kills the seal.
- **Auto-summarised memory.** A summary is the narrator sneaking back in. The chronicle is written by someone *in* the world, wrongness included.
- **Visible quest logs and clocks.** Available through the charter; never the default.

## What was instrumentation, not engine

| v1 rule | v2 home |
|---|---|
| The `~` mark | `marks` dial |
| The clock question | `standdown` dial |
| No narrator | `delivery: voices` |
| A need, not a task | `hook: need` — still the default |
| Nothing asked about the person | still the default; `checkins` dial |
| "Without thanks" at stand down | each closer's own economy |
| Hidden purpose; "nobody knows the person is observed" | removed from the core. A general framework shouldn't run a concealed observation on whoever sits down. The observer setup is now a charter you write yourself, on yourself. |
| Never read engagement | **stays on the floor.** That was never instrumentation; it is the anti-mirror. One loosening: `attunement: camera`. |

## Evidence from your own worlds

I looked at the repo's shape — file sizes and section names, not content. Your seal is intact.

- Left alone, the v1 engine invented sections the spec never asked for: doors, resolutions with costs, lying and honest sources, things already in motion, a distance scale, rules kept versus plot discarded. v2 makes those mandatory. The model was already reaching for them.
- The log format it settled on — your words, what changed, distance before → after, plus the world's own moves — was good. Kept.
- The harness copied into each world folder → one harness at the root, many worlds beneath it.
- Your observation that a world rebuilt in the same context as a mistaken brief stays anchored → *clean hands*.

## Rulings for you

Judgment calls I made that you may want to overrule:

1. **Default `delivery` is `senses`, not `voices`.** Voices-only collapses when nobody is in the room, and solitary exploration is half of what you want next. `voices` is one line in a charter.
2. **The seal opens if asked twice.** It is the player's disk. One warning, then obey.
3. **`//` for outside.** `(( ))` also accepted.
4. **`rewind: telling` by default** — only when the telling misled. Consequences holding is the point; a miscommunicated ten-metre gap is not a consequence.
5. **The ledger is never cleared.** v1 wiped the log each watch. Append-only is safer, and it is what makes recovery and grep work.
6. **One file, ~5.7k words — 2.4× v1.** Build and stand-down procedure could move to on-demand files. I kept one file because you asked for one and v1's single-file reliability is a feature. If per-turn rules start slipping in long sittings, that is the first thing to split out.
7. **"Watch"** kept as the word for a sitting.

## v1 as a preset

The test of the generalisation: v1 should fall out as one configuration. Save as `worlds/<name>/charter.md`:

```markdown
# Charter — A World Needs You

## Law
(the setting named in the first message; otherwise the engine chooses)

## Stance
- who: the person, as themselves
- hook: need
- hardness: fair
- Prefer worlds where holding a whole system, finding the fault by the discrepancy,
  and refusing to believe the panel is what is needed. Never say so.

## Telling
- delivery: voices
- recap: none
- options: off

## Table
- resolution: causal
- authority: character
- rewind: never
- seal: closed
- checkins: none
- attunement: off
- marks: `~` alone on a line — no reaction; note it; one short line of the world continuing
- standdown: "How long did that feel?" — blank is a fine answer
- Whoever closes the watch does so without thanks.
- Records go to the office at thirty.
```

## Migrating an existing world

1. Put the new `CLAUDE.md` and `README.md` at the repo root. **Delete the copies inside each world folder** — a nested `CLAUDE.md` loads alongside the root one and they will fight.
2. Drop the preset above in as that world's `charter.md`, so it keeps behaving the way it was built.
3. Rename `.world/log.md` → `.world/ledger.md` and head it `## watch 001`. At next open the engine finds a watch with no record and runs recovery — which is exactly the job that was pending anyway.
4. First message: `// migrate this world to the current harness; change nothing that has surfaced`. Its truth file uses different section names; v2 only says "holds, at least", so the engine should add `pressures` and `movers` beneath what exists rather than restructure it.
5. World-per-branch is no longer needed; everything can live on `main` under `worlds/`.

## Hardening, when you feel like it

- **A Stop hook** that checks `ledger.md` changed during the turn. Deterministic backstop for floor 7; one of the other harnesses does the same for autosave.
- **Fresh-context helpers** for the build (clean hands) and for the stand-down audit — a reader with no stake in the conversation's momentum is a better auditor than the narrator marking its own homework.
- **The scrollback leak.** Claude Code prints file writes, so the truth flashes past in your terminal. v1 relied on you not reading it. Hidden writes done by a helper should stay out of your scrollback — untested on your setup.
- **`modules/`** is where a stat-driven combat system would live if you want one. The core doesn't need to know.

## Sources

AI-side, read September 2026:
- Sstobo/Claude-Code-Game-Master — https://github.com/Sstobo/Claude-Code-Game-Master
- SergeyKhval/claude-dnd — https://github.com/SergeyKhval/claude-dnd
- neuralinitiative/claude-dnd-skill — https://github.com/neuralinitiative/claude-dnd-skill
- SillyTavern World Info docs — https://docs.sillytavern.app/usage/core-concepts/worldinfo/
- Lorebooks as active guidance (positivity-bias rolls) — https://huggingface.co/sphiratrioth666/Lorebooks_as_ACTIVE_scenario_and_character_guidance_tool
- AI Dungeon context assembly and memory system — https://latitudegames.notion.site/What-goes-into-the-Context-sent-to-the-AI-7e5881352de6427da9c92b04149e8e50
- Platform comparisons (vendor blogs — read sceptically): dungeonsdeep.ai, arcanumrpgs.com, roleforge.ai
- "Fluctuating agency" in LLM-run play — ROBOPSY PL[AI], https://arxiv.org/pdf/2510.09874

Tabletop and research, from memory rather than lookup: Apocalypse World (agenda, principles, threats); Dungeon World (fronts, grim portents); Blades in the Dark (clocks, telegraphing, don't block); The Alexandrian (Three Clue Rule, prep situations, node-based design); Return of the Lazy Dungeon Master (secrets and clues); GUMSHOE (core clues are never rolled for); Mythic GME (surprise has to come from outside the author); Ironsworn (success at a cost); Worlds Without Number (faction turns); Generative Agents, Park et al. 2023 (memory, reflection); Lines and Veils, X-Card, Script Change.
