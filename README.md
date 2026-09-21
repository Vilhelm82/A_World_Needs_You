# Worldkeeper

Point a session at this folder and say anything. Something will start.

- Say what you want — a setting, a character, a mood, a rule — or say nothing and be surprised.
- `// like this` steps outside the world. Change how it works, ask who someone was, `// rewind`, `// pause`, `// skip`. Nobody in there will hear it.
- `*I tell them what happened*` — compress anything the world already knows. It counts as said, in full.
- `stand down` ends the watch. The world is saved where its own logic left it.
- `worlds/<name>/charter.md` is yours: what you asked for, in your words. Edit it whenever you like.
- `worlds/<name>/chronicle/` is yours too: whatever the world has put in your character's hands. It may be wrong.
- Do not open `.world/` or `records/`. That is the agreement. A world is only worth standing in if it could be other than you'd like.

## Courtroom trial branch

Say **Begin the courtroom trial. I am counsel for the defendant.** in a fresh
file-backed agent session at the repository root. See [COURTROOM.md](COURTROOM.md)
for startup, controls and validation limits. Python 3.10+ is required for this module.

The original harness is preserved in `modules/worldkeeper-base.md`; `CLAUDE.md`
routes non-court worlds to it unchanged. The court has explicit scoped amendments,
a committed first case and deterministic record checks. Existing worlds are untouched.
