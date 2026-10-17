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
      clock.json  ship.json  facts.json  precedents.json  forces.json
      evidence.json  premises.json  pins.json
      crew/<id>/soul.json        one folder per person (tiers below)
      crew/<id>/memory.json
      episodes/<id>.json
```

## Files and their rules

**clock.json**: `stardate` (number, never decreases on a timeline), `ship_time` ("HH:MM"), `day` (int), `alert` (`normal` / `yellow` / `red`), `location` (str), `episode_open` (episode id or null), `timeline` (`main` or a fork name).

**ship.json**: `course`, `orders` (list), `systems` (object of system → status string). Free otherwise.

**crew/&lt;id&gt;/soul.json**: one per person. Required: `id`, `name`, `rank`, `post`, `tier` (`canon` / `recurring`), `created_at`, `persona`, `regard`, `routing`, `agenda`, `relationships`, `schedule`, `location`.
- `persona`: `values`, `traits`, `tired_of`, `wrong_about`, `cares_about`. **Immutable**: it can change only in a commit whose ledger appends a `CHANGED` entry naming this person and the cause.
- `regard`: `gives_freely` and `gives_rarely` (lists from praise, trust, candour, warmth, anger, desire), plus `toward` (object of id → short current stance).
- `routing`: object of topic → ordered list of ids they take it to first. Ids must exist, or be `player`.
- `agenda`: list of `{goal, next_step, horizon}`, with `horizon` one of `shift` / `week` / `career`.
- `voice` (optional): a path to a voice card. Canon crew point at `modules/tng-d/voices.md`.

**crew/&lt;id&gt;/memory.json**: `learned` (fact ids they know), `beliefs` (list of `{about, belief, from, at}`), `recent` (short list). Writable each turn. A person's memory is their light cone: what they witnessed, were told or read.

**facts.json**: `{"facts": [...]}`, each `{id, statement, known_by, surfaced_at, source, created_at}`. `known_by` lists ids, `player` or `all`. `surfaced_at` is null until the player has perceived it. **A fact with `surfaced_at` set is immutable and can never be removed.** New truth goes in as new facts beneath it.

**precedents.json**: `{"precedents": [...]}`, each `{id, ruling, kind, reason, source, created_at}`, with `kind` one of `lore` / `procedure` / `tech` / `person`. Append-only and immutable: a later precedent may *refine* an earlier one by citing its id, but never edits it.

**forces.json**: `{"forces": [...]}`, each `{id, state, wants, capabilities, trajectory}`. `trajectory` is a list of `{step, preconditions, status, cause}`, with `status` one of `on_track` / `delayed` / `averted` / `altered` / `done`, and `cause` a ledger reference whenever status isn't `on_track`.

**evidence.json**: `{"traces": [...], "cases": [...]}`, as in `covert.md`. Trace `who_can_read` holds ids or roles (`security`, `captain`, `ops`, `anyone`). Case `investigator` must exist. Case `known` lists trace ids that must exist.

**episodes/&lt;id&gt;.json**: `{id, status, arrival, premise, lands_on, b_plot, forces, truth}`, with `status` one of `pending` / `open` / `closed`. `lands_on` ids must exist.

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
| `TURN` | `stardate`, `present` (ids), `speakers` (ids, in order), `addressed` (object of id or `player` → count of lines addressed to them), `initiated` (ids who acted on their own agenda this turn), `transcript` (`watch-NNN.md#turn-N`) |
| `DID` | `decision` (the person's words), `changed`, `distance` (object of resolution → [before, after]) |
| `SAID` | `by`, `claim`, `truth` (`true` / `false` / `partial`), `fact` |
| `TOLD` | `to`, `fact` |
| `HAS` | `item`, `change` (`+` / `-`) |
| `MOVED` | `by`, `what`, `cause` (`player` / `world` / `force:<id>` / `npc:<id>`) |
| `DECIDED` | `by`, `what`, `without_player` (bool) |
| `ATTEMPT` | `what`, `outcome` (`done` / `denied` / `cost`), `reason` |
| `CHANGED` | `who`, `field`, `cause` |
| `PRECEDENT` | `id` |
| `OBJECTION` | `claim`, `verdict` (`consistent` / `unsupported` / `contradicts`), `ruling` |
| `WORLDTURN` | `steps` (list of what moved) |
| `NOTE` | `text`, Will's `// note`, for the evaluation only |
| `LAW` `ROLL` `REWOUND` `SAVE` `FORK` `RETURN` `HOLODECK` | as they happen |

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
