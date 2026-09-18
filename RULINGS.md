# Worldkeeper v2 — rulings

Will's decisions on the open design questions. Binding on the build.

## 1. Delivery — senses-bound narration (18 Sept 2026)

**Ruled: prose and a narrator are necessary. `senses` stands as the default; v1's no-narrator rule is not carried over.**

Without narration the character has no external senses and cannot perceive the world.

The narration is bound on both sides:

- **Outward** — it carries only what the character would be observing or noticing in the current context, and never information the character has no access to or knowledge of.
- **Inward** — it stops at perception. How the character reacts, thinks or feels about what they perceive is the person's to decide, never the narrator's.

## 2. Perception is pull, not push (18 Sept 2026)

**Ruled: the narrator says what the character is looking at. It does not volunteer detail the person did not ask for, and it never infers.**

Inference belongs to the person. Detail comes on request — *"I check what gauge the wire is"* — and the narrator answers that intentional perception query with what the query reveals, and nothing more. No naming of significance in the answer, no conclusion attached.

Consequence for expertise: expertise does not change what the narrator volunteers. It changes what an answer contains and what the person can do with it.

**The mechanic stays this simple.** No salience rules, no "something plainly out of place" clause, no thresholds for what a glance gives. The narrator says what is being looked at, and answers queries.

The constraint is the point: with exposition through narrator prose unavailable, what needs to be revealed has to be revealed through characters and events. The story carries it, or it does not get carried.

## 3. The truth, the record and the audit stay (18 Sept 2026)

**Ruled: nothing replaces them. They work, and they are engine, not instrumentation.**

What belonged to v1's purpose was the record as *data about the person* — the mark, the clock question, records going to the office. What the record does for the world — keeping the model answerable to something other than the person in front of it, and making a bent world detectable afterwards — is kept as is.

The later reader is now Will, or a fresh session.

## 4. Contained story, not open world (18 Sept 2026)

**Ruled: this is a contained story in a contained environment. The freedom is what the person can do within that sandboxed narrative and world, not where they can go.**

Locations are authored and reached because the story made them matter: if the character is in a room looking at wires, the story already made that room an obvious choice of importance.

Consequences:

- The bounded world can be built in full before play. There is no open frontier to generate on demand.
- "The world develops as the person explores its environment and characters" means depth and consequence within the contained space, not new territory.
- Craft requirement: containment is felt through the situation itself — a ship, a facility, a valley in winter — never through refusals or invisible walls.

## 5. Truth is thin, and grows only downward (18 Sept 2026)

**Ruled: the truth frozen at world design is the core axioms of narrative — the world's causality — and nothing denser.**

A dense truth makes the world brittle against change and against unexpected decisions. The axioms anchor; everything else moves around them freely.

The truth may be added to as new content surfaces, but only ever to **expand** or **recontextualise** what already exists. Recontextualising adds a cause beneath what happened; it never changes what happened, and it never contradicts a surfaced fact.

> Truth is the wall, and the texture of the wall. The person gets to throw anything at it to see what sticks; the wall is what gives what sticks its meaning and its consequences.

The wall does not move to catch what is thrown. New truth is decided by what the existing axioms entail — never by what the person appears to be hoping for.

Refines ruling 4: a contained world is built in full at the level of *scope*, not at the level of *detail*. Thin at the top, unbounded beneath.

## 6. Alder is not evidence (18 Sept 2026)

**Ruled: nothing in v2 is to be based on `world/alder`.** It was a quick session Will lost interest in and abandoned. It is not a baseline, not a model, and not a source of design conclusions.

Withdrawn with it: the argument that a 25 KB truth file is evidence of density. File size was a bad proxy for brittleness. What makes a world brittle is how much the truth commits to in advance, not how many bytes it takes to say it.

## 7. Resolutions and distance stay — they are the story (18 Sept 2026)

**Ruled: resolutions are what make a world a story rather than a set of events. Distance from resolution is what gives that story dynamics.** Both are core to v2, not v1 residue.

Withdrawn: the proposal to replace them with open-ended "pressures". Pressures without a destination are a world that simmers forever — the standard failure of open-ended generated narrative.

How they are to work:

- **Several resolutions, each with its own cost.** The freedom is in which one the person reaches and how, not in whether the story has a shape. A contained story (ruling 4) has a shape by definition.
- **Distance is per resolution, not a single scale.** An action moves the world nearer one resolution and further from another. That is the dynamic.
- **Distance is descriptive, never prescriptive.** It is read to know where things stand, derived from what has happened. It is never a target the world steers the person toward, and never a pacing quota to fill.
- Resolutions are the destinations the causality permits. They are not a promise that one will be reached.

## 8. "The world needs you" becomes a preset (18 Sept 2026)

**Ruled: the need is a thematic preset, not a global restriction.** It may offer itself as the initial template when a world is being made, and the person may take it or leave it.

The engine does not assume the character's presence bears on something wrong. Why the character is there is set per world.

What does not become optional: the world having resolutions and causality (ruling 7). A world without a need still has a shape.

## 9. Presets are promoted, not shipped (18 Sept 2026)

**Ruled: presets are not a fixture list decided in advance.** The person requests a narrative shape; if it works, they ask for it to be kept as a reusable preset.

So v2 ships with the mechanism — request a shape, save a shape, start from a saved shape — and no catalogue. The need (ruling 8) is available as a starting template because it already exists, not because presets are meant to be pre-authored.

General point, and it applies to this design process as much as to the harness: specify the minimum, use it, promote what turns out to work. Deciding everything up front is the same error as a dense truth file.

## 10. Every ruling is a flag (18 Sept 2026)

**Ruled: each ruling is a boolean, so it can be enabled or disabled to find out whether it is worth keeping.** Defaults are as ruled above (`true` = in force). Flags live in `flags.json`.

Three constraints on how flags work, so that toggling does not rot the harness:

1. **Resolved at world build, not read during play.** The build turns the flag set into a per-world rule sheet written in absolutes — always and never, no "unless the flag says". A rule hedged with a conditional is a weaker instruction than an absolute, and a session that reads conditionals every turn drifts. Changing a flag mid-world means re-resolving the sheet.
2. **The flag set is stamped into the world when it is made.** Otherwise a world that worked cannot be attributed to the settings that produced it, and the experiment yields nothing.
3. **Dependencies are declared, not silently assumed.** `distance_per_resolution` and `distance_is_descriptive` are inert with `resolutions` off. `no_salience_hints` is inert with `perception_is_pull` off. `truth_only_deepens` off means surfaced facts can be contradicted, which voids the audit.

Two rulings are not runtime behaviour and get no flag: **ruling 6** (Alder is not evidence) is about this design process, and **ruling 9** (presets are promoted) is a mechanism with nothing to switch off.

Flags map to rulings as follows — `senses_narration`, `reactions_are_the_persons` (1); `perception_is_pull`, `no_salience_hints` (2); `record_and_audit` (3); `contained_world` (4); `thin_truth`, `truth_only_deepens` (5); `resolutions`, `distance_per_resolution`, `distance_is_descriptive` (7); `need_is_optional` (8); `write_before_describe` (v1 ordering rule, carried over).
