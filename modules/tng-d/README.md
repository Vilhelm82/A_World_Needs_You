# TNG-D — a living Enterprise (evaluation prototype)

Star Trek: The Next Generation as a ship you live on. The Enterprise-D in 2364, the season-one crew, and you in Riker's shoes: his history, with your own variations wherever they make no difference to canon. The timeline branches at Farpoint and is yours from there: canon survives as forces with intentions, never as scheduled episodes.

Two layers run on one clock:
- **Ship life**: duty, off-duty, your own projects, covert or not. The ship goes on whether you're in the chair or in your quarters.
- **Episodes**: situations that arrive on that clock, like the show, and land on whoever they land on.

This preset is an **evaluation prototype**. Every watch is scored against the end goals in `modules/eval/GOALS.md`, and the harness gets changed between watches, with your approval, to close the gaps. It isn't meant to be right on day one; it's meant to know where it's wrong.

## Files

| File | What it is |
|---|---|
| `law.md` | The constitution: era, ship, branch point, Starfleet. Every line marked [canon] or [assumed]. |
| `forces.md` | Canon as intentions: Q, the Romulans, the Borg, the infiltration, Lore, and the rest. |
| `voices.md` | The season-one crew's voices. |
| `style.md` | How it's told; the ensemble rules that override `modules/tng/style.md`. |
| `episode.md` | How episodes are built, checked, arrive and close. |
| `justice.md` | Discipline, the ladder, courts-martial, main versus forks. |
| `deeds.md` | Every notable act's traces, how word spreads, deduction (means, opportunity, motive, computed suspect pools), cases and isolated investigators. |
| `physics.md` | Hard science: real physics plus five closed postulates; mechanism cards; computed numbers; canon unknowns as black boxes; hypotheses that survive but are never crowned. |
| `STATE.md` | The JSON world, the ledger, timelines. |
| `canon/` | The live lore base: cited lore cards and hard-science mechanism cards, and how to check lore at any time, branch-aware. |
| `charter.template.md` | The charter to copy. |

## Starting

The world runs from your own disk; GitHub is its remote copy. The Enterprise world's charter is already at `worlds/enterprise/charter.md`, and your character sheet at `worlds/enterprise/sheet.md`. Open a local Claude session at the root of your clone and say "Enterprise". The first open builds the world (clean hands), then play begins.

Run once per clone so every commit is validated and then pushed to GitHub:

```
python3 tools/wk.py install-hooks
```

## Outside the world

All the usual `//` commands, plus `// save <name>`, `// fork <name>`, `// holodeck`, `// return`, `// lore objection <what's wrong>`, `// note <anything about how it's running>`, and at stand-down, if you want, `// rate`.
