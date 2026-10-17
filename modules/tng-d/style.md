# Style — how this world is told

Read `modules/tng/style.md` for the register, the table, the log and the away team. It all applies here **except** where this file overrides it. The overrides fix the flaw found in the Cassini world: the crew orbiting the player.

## The ship is an ensemble

- The canon crew are not the player's audience. They have their own duties, agendas, friendships and arguments, and the camera follows those when the character is present to see them. *(Overrides "they react, decide their part, and watch the character".)*
- **Routing.** Every person routes problems to whoever owns them, by their routing table (`STATE.md`). Picard takes engineering to engineering and a crew matter to the doctor or counselor. He brings ship's business to his first officer because that's the job, not because the first officer is the player. Routing toward the character grows only from decisions people have seen.
- **Turn balance.** Over any ten turns, no single voice (the character included, as addressee) takes more than its share. If a senior officer present has had under 15% of the speaking, the next beat that naturally falls to them goes to them. Measured from the ledger (`modules/eval`), not judged by eye.
- People decide things without the character: Picard makes calls alone, departments solve their own problems, and the character hears about it afterwards if they're the sort of person who'd be told.

## No standing evaluation

No captain's scorecard on the character. *(Overrides "Evaluate the officers and be evaluated" in the XO's job.)* Picard's regard moves on what he witnesses, the same as everyone else's, and nobody keeps a running tally of marks.

## Two layers

- **Ship life:** duty shifts, off-duty time, friendships and rivalries, the character's own pursuits and everyone else's. Anything that runs across watches (an experiment with La Forge, an XO initiative, a crewman's side project, a secret) is a **project** in `projects.json`, so its stages, costs and collaborators stay consistent. Ordinary days are told briefly; cut across them unless something is happening.
- **Episodes:** situations that arrive on the same clock. When one arrives, ship life doesn't stop; it gets interrupted.

## Episode grammar

When an episode is running: a cold open in the middle of something small; the situation arriving inside the first exchange; a senior staff briefing when it would happen, not because the format demands one; an A-plot (the situation) and a B-plot (somebody's own life aboard) running alongside each other; the captain's log as the chronicle. The episode ends when its situation resolves or is lost, by the world's logic.
