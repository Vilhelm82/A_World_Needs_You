# State — the structured world

A world under this preset keeps everything that has to be exact as JSON under `.world/state/`, validated by `tools/wk.py` on every commit. Prose that carries voice — voice cards, the chronicle, what the player was told — stays as markdown. **JSON for facts, prose for voice.**

The GM never edits state freehand and then hopes. Each turn it writes a change, runs `python3 tools/wk.py validate worlds/<world>`, and only tells the player once the change has committed. The pre-commit hook runs the same validation, so an invalid change cannot commit, and what hasn't committed hasn't happened.

## Layout

```
worlds/<world>/
  charter.md                     Will's
  chronicle/                     in-world paper (logs, orders, letters)
  evals/                         public scorecards — no spoilers (modules/eval)
  .world/                        sealed
    build.md                     build notes: candidates, rolls, choices
    rules.md                     the charter resolved into absolutes at build
    timeline.json                {"main": "<branch the main timeline lives on>"}
    ledger.jsonl                 append-only; one JSON object per line
    transcript/watch-NNN.md      append-only; exactly what the player was told
    evals/                       sealed audit detail
    state/
      clock.json  ship.json  player.json  facts.json  precedents.json
      forces.json  divergence.json  deeds.json  projects.json
      unknowns.json  hypotheses.json  premises.json  pins.json
      crew/<id>/soul.json        one folder per person (tiers below)
      crew/<id>/memory.json
      episodes/<id>.json
```

## Files and their rules

**clock.json**: `stardate` (number, never decreases on a timeline), `ship_time` ("HH:MM"), `day` (int), `alert` (`normal` / `yellow` / `red`), `location` (str), `episode_open` (episode id or null), `timeline` (`main` or a fork name).

**ship.json**: `course`, `orders` (list), `systems` (object of system → status string). Free otherwise.

**player.json**: the player's character as the world sees them: `name`, `rank`, `post`, `access` (as below), `location`. Their inner life is never here; it's theirs.

**crew/&lt;id&gt;/soul.json**: one per person. Required: `id`, `name`, `rank`, `post`, `tier` (`canon` / `recurring`), `created_at`, `persona`, `regard`, `routing`, `agenda`, `relationships`, `schedule`, `location`, `access`, `roles`, `competence`.
- `persona`: `values`, `traits`, `tired_of`, `wrong_about`, `cares_about`. **Immutable**: it can change only in a commit whose ledger appends a `CHANGED` entry naming this person and the cause.
- `regard`: `gives_freely` and `gives_rarely` (lists from praise, trust, candour, warmth, anger, desire), plus `toward` (object of id → short current stance).
- `routing`: object of topic → ordered list of ids they take it to first. Ids must exist, or be `player`.
- `agenda`: list of `{goal, next_step, horizon}`, with `horizon` one of `shift` / `week` / `career`.
- `access`: `areas`, `systems`, `codes`, `skills` (lists of short tokens, e.g. `armoury`, `transporter`, `engineering-override`, `warp-systems`). Mostly decided by rank and billet. Used for deduction (`deeds.md`).
- `roles`: which records they can read by role, from `security`, `captain`, `ops`, `medical`, `engineering`.
- `competence`: `deduction` (`high` / `medium` / `low`), plus anything else worth stating (`instruments`, free text).
- `voice` (optional): a path to a voice card. Canon crew point at `modules/tng-d/voices.md`.

**crew/&lt;id&gt;/memory.json**: `learned` (fact ids they know), `beliefs` (list of `{about, belief, from, at}`), `recent` (short list). Writable each turn. A person's memory is their light cone: what they witnessed, were told or read.

**facts.json**: `{"facts": [...]}`, each `{id, statement, known_by, surfaced_at, source, created_at}`. `known_by` lists ids, `player` or `all`. `surfaced_at` is null until the player has perceived it. **A fact with `surfaced_at` set is immutable and can never be removed.** New truth goes in as new facts beneath it. Optional `reinterprets`: the id of an earlier fact this one explains (an instrument artifact, different conditions, a limit of resolution); the earlier fact stays as it was.

**precedents.json**: `{"precedents": [...]}`, each `{id, ruling, kind, reason, source, created_at}`, with `kind` one of `lore` / `procedure` / `tech` / `person`. Append-only and immutable: a later precedent may *refine* an earlier one by citing its id, but never edits it.

**forces.json**: `{"forces": [...]}`, each `{id, state, wants, capabilities, trajectory}`. `trajectory` is a list of `{step, preconditions, status, cause}`, with `status` one of `on_track` / `delayed` / `averted` / `altered` / `done`, and `cause` whenever status isn't `on_track`: a divergence id (`D-…`) or a ledger reference.

**Ledger references** are written `L:<watch>:<turn>` and must match at least one ledger entry.

**divergence.json**: `{"divergences": [...]}`, each `{id, canon, branch, parents, at}`. `canon` is what canon's history had; `branch` is what happened here instead; `parents` lists the earlier divergences (`D-…`) or ledger references (`L:w:t`) that caused it. The validator requires every parent to exist, no cycles, and every chain to end in a real ledger entry: every difference from canon traces back to something somebody actually did. Append-only.

**deeds.json**: `{"acts": [...], "traces": [...], "cases": [...]}`, as in `deeds.md`.
- Act: `{id, actor, what, at, where, visibility, valence, constraints, traces}`. `actor` is an id or `player`. `constraints` holds `means` (`areas`, `systems`, `codes`, `skills`) and `opportunity` (`where`, `window` [from, to] stardates).
- Trace: `{id, type, where, who_can_read, lasts, created_at}`, plus `act` (which act left it) and, for `location` traces, `subject` and `window`. `who_can_read` holds ids or roles (`security`, `captain`, `ops`, `medical`, `engineering`, `anyone`).
- Case: `{case_id, investigator, trigger, known, next_step, status}`, `status` one of `open` / `closed` / `cold`. `known` lists trace ids. `runs` records each investigator turn: `{watch, turn, act, isolated, cited, pool, suspects}`. The validator rejects a run that cites a trace outside `known`, and recomputes `pool` for every new run (`wk suspects`), rejecting a mismatch.

**projects.json**: `{"projects": [...]}`, each `{id, title, owner, collaborators, kind, goal, stages, status, precedents, started_at}`. `kind` is `duty` / `experiment` / `personal` / `covert` / `other`. `stages` is a list of `{name, status, needs, cost}`, with stage `status` one of `todo` / `doing` / `done` / `failed`. Project `status` is `active` / `paused` / `done` / `abandoned`. Owner and collaborators must exist (or be `player`); precedents must exist. A project is how a ship-life thread stays consistent across watches: an experiment with La Forge, an XO initiative, a personal pursuit.

**episodes/&lt;id&gt;.json**: `{id, status, arrival, premise, lands_on, b_plot, forces, truth}`, with `status` one of `pending` / `open` / `closed`. `lands_on` ids must exist.

**unknowns.json**: `{"unknowns": [...]}`, each `{id, subject, canon_record, observations}`: a canon unknown as a black box (`physics.md`). `canon_record` lists canon card ids (what the show established); `observations` lists fact ids (what this branch has measured). **No explanation field, ever**; the validator rejects one.

**hypotheses.json**: `{"hypotheses": [...]}`, each `{id, subject, statement, proposed_by, held_by, physics_basis, predictions, tests, status, created_at}`. `predictions` is a list of `{id, if, then}`; `tests` a list of `{prediction, via, observation, result}` where `observation` is a fact id and `result` is `supported` / `falsified` / `inconclusive`. `status` is `open` / `surviving` / `falsified`. The validator enforces: any falsifying test makes it `falsified`; `surviving` needs a supported test; falsified is permanent; statements never change and tests are append-only (refine into a new hypothesis instead). Optional `revives: {hypothesis, via}`: a new hypothesis may take up a falsified one, but only `via` a fact that reinterprets an observation that falsified it. The old one stays falsified.

**premises.json**: `{"premises": [...]}`, each `{id, candidates, roll, chosen, canon_distance}`.

**pins.json**: `{"pins": [...]}`, each `{when: {path, op, value}, attach}`. A deterministic pin: when `path` in state (e.g. `clock.alert`) meets `op` (`==`, `!=`, `in`) `value`, the file at `attach` is read before the turn. Attach paths must exist.

## Crew tiers

- **canon / recurring**: a full soul folder, made before they first speak.
- **crowd**: no file; written as `crowd:<label>` (e.g. `crowd:ensign-at-ops`). Crowd people carry no hidden knowledge and can't change the world beyond what they're seen to do. When one matters twice, they're promoted to a soul folder.

## Context attachment

| What | When it's read |
|---|---|
| the card (`state.md`), `clock.json`, `rules.md` | every turn |
| a speaker's `soul.json`, `memory.json` and voice card | before they speak |
| facts, evidence, forces, precedents, episode truth | by reach: when the action touches them (search, don't skim) |
| pins | when their condition holds |

## The ledger

One JSON object per line, always with `watch`, `turn` and `type`.

| type | fields |
|---|---|
| `TURN` | `stardate`, `present` (ids), `speakers` (ids, in order), `addressed` (object of id or `player` → count of lines addressed to them), `initiated` (ids who acted on their own agenda this turn), `transcript` (`watch-NNN.md#turn-N`); optional `lore_touch` (list of `{what, layer}` for anything the turn introduced that canon governs: a technology, species, procedure or canon fact) |
| `LORECHECK` | `claim`, `layer` (`rules` / `history-pre` / `history-post`), `verdict` (`consistent` / `diverged` / `unsupported` / `contradicts`), `cards` (ids), `divergence` (ids), `agent` (bool: a fresh lore agent was used) |
| `REAUDIT` | `scope`, `findings` (count) |
| `CALC` | `expression`, `result`, `units`, `purpose`. Re-evaluated by the validator; a wrong result is refused (`python3 tools/wk.py calc`) |
| `DID` | `decision` (the person's words), `changed`, `distance` (object of resolution → [before, after]) |
| `SAID` | `by`, `claim`, `truth` (`true` / `false` / `partial`), `fact` |
| `TOLD` | `to`, `fact` |
| `HAS` | `item`, `change` (`+` / `-`) |
| `MOVED` | `by`, `what`, `cause` (`player` / `world` / `force:<id>` / `npc:<id>`) |
| `DECIDED` | `by`, `what`, `without_player` (bool) |
| `ATTEMPT` | `what`, `outcome` (`done` / `denied` / `cost`), `reason` |
| `CHANGED` | `who`, `field`, `cause` |
| `PRECEDENT` | `id` |
| `OBJECTION` | `claim`, `verdict` (`consistent` / `diverged` / `unsupported` / `contradicts`), `ruling` |
| `WORLDTURN` | `steps` (list of what moved) |
| `NOTE` | `text`, Will's `// note`, for the evaluation only |
| `ROLL` | for undetermined outcomes: `outcomes` (written first), `roll` (1-based, from the shell), `result` (must be `outcomes[roll-1]`). The result is recorded as a scoped observation fact, never a precedent (`physics.md`) |
| `LAW` `REWOUND` `SAVE` `FORK` `RETURN` `HOLODECK` | as they happen |

Every `lore_touch` item on a `TURN` needs a `LORECHECK` with the same watch and turn in the same commit. The validator counts them.

`SAID` with a `fact`: if `by` is a crew id, the fact's `known_by` must include them (or `all`); a crowd speaker can only cite facts known by `all`. `TOLD` with a `fact`: everyone in `to` must be in the fact's `known_by` by the end of that commit.

The ledger is append-only. The validator rejects any commit whose ledger doesn't begin with the previous commit's ledger, byte for byte. Transcripts work the same way.

## Timelines

The main timeline is permanent. Forks are where anything goes.

| Command (Will types it outside the world) | What `wk` does |
|---|---|
| `// save <name>` | Checkpoint, then tag `save/<world>/<name>` at a neutral point (no scene open). |
| `// fork <name>` | Branch `fork/<world>/<name>` from here and switch to it. Main is untouched. |
| `// holodeck` | "That was a holodeck run": everything since the last save moves onto a new fork branch, and main resets to that save. Nothing is lost. |
| `// return` | Back to main. |

After any of the four, the GM tells Will to **end the session and open a fresh one**: the conversation still remembers what the files no longer contain, and that bleeds. On the next open the GM reads only the files.
