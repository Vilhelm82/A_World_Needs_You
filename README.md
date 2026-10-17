# Worldkeeper

Point a session at this folder and say anything. Something will start.

- Say what you want — a setting, a character, a mood, a rule — or say nothing and be surprised.
- `// like this` steps outside the world. Change how it works, ask who someone was, `// rewind`, `// pause`, `// skip`. Nobody in there will hear it.
- `*I tell them what happened*` — compress anything the world already knows. It counts as said, in full.
- `stand down` ends the watch. The world is saved where its own logic left it.
- `worlds/<name>/charter.md` is yours: what you asked for, in your words. Edit it whenever you like.
- `worlds/<name>/chronicle/` is yours too: whatever the world has put in your character's hands. It may be wrong.
- `modules/<preset>/` holds a reusable shape: a setting's law, its style, and how its stories begin and end. To start a world from one, copy its `charter.template.md` to `worlds/<name>/charter.md` and say anything. `modules/tng/` is Star Trek: The Next Generation — a ship, a standing crew, an episode at a time.
- `modules/tng-d/` is a living Enterprise-D in 2364: you in Riker's shoes, a timeline that branches at Farpoint, ship life and episodes on one clock, and its state kept as validated JSON. Its world is `worlds/enterprise/`. It runs from your own disk in a local Claude session; GitHub is the remote copy. Run `python3 tools/wk.py install-hooks` once per clone so every commit is validated and pushed.
- Structured worlds add `// save <name>`, `// fork <name>`, `// holodeck` (that last stretch never happened on main; it's kept on a fork) and `// return`. Also `// lore objection <what's wrong>`, `// note <anything>`, and `// rate`.
- Every watch of a world with `evaluation: modules/eval` is scored against `modules/eval/GOALS.md`. Read `worlds/<name>/evals/` for scorecards and the trend; they never spoil. `// proposals` and `// approve P-NNN` change the harness between watches.
- Do not open `.world/` or `records/`. That is the agreement. A world is only worth standing in if it could be other than you'd like.
