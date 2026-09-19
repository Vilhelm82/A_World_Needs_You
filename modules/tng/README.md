# TNG — a Worldkeeper preset

Star Trek: The Next Generation as a place the harness can run: a Starfleet ship in the 2360s, a standing crew, and an episode at a time. The preset is the setting's law, its house style, the rule for how episodes begin and end, and voice cards for the people canon already made.

A world is a ship. An episode is a situation. A watch is a sitting; an episode may take several.

## Starting a world from it

1. Copy `charter.template.md` to `worlds/<ship>/charter.md`. Fill the `<...>` fields; delete what you don't want; add anything.
2. Open a session at the repo root and say anything.

The harness reads the charter, follows its `preset:` line here, and builds: the ship, the standing crew (each made in full), and the first episode — six candidate situations with nothing in common, a die rolled from the shell, the one that falls. The candidates and the roll go to the world's `.world/build.md`, so later episodes never repeat one.

## Files

- `law.md` — the setting's rules kept; the plot discarded; what nobody yet knows in this era.
- `style.md` — how a TNG world is told and how its people behave: the table, the log, the away team, the XO's job, what technobabble is for.
- `episode.md` — how an episode opens, runs, closes, and how the next one is made. Applies at every open.
- `voices.md` — voice cards for canon people, held to canon. Read the card before a canon person speaks, every time.
- `charter.template.md` — the charter to copy.

## Reuse

The standing crew and the ship live in the world's `.world/people/` and `.world/places/`. Each episode's situation lives in `.world/truth.json` under `episode`. When an episode closes, its record keeps the truth as it stood, and the next open builds the next episode beneath the same crew — who carry forward what they concluded about the character, from what they witnessed and nothing else.

Several TNG worlds can run side by side under `worlds/`, each its own ship.
