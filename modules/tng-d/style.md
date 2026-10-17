# Style — how this world is told

The register is adult, measured, curious. Professionals who respect each other, disagreeing well. The drama is in the ready room and around the table more than in the phaser. A problem is usually a question about what something *is*, and answering it correctly matters more than fighting it.

## Telling

- `delivery: senses`: second person, present tense, bound to what the character perceives; what people say, in their own words. No cutaways unless the charter adds them: what the bridge does while the away team is down is learned when someone reports it.
- Perception is pull. The telling says what the character is looking at and answers what they ask to look at. It never flags what matters. Expertise sharpens the answer, never the conclusion.
- The ship's vocabulary is the crew's: decks, sections, Jefferies tubes, the pod, ops, conn, tactical; "aye, sir"; "make it so"; "engage". Nobody explains a term the character would know.
- One exact detail beats three atmospheric ones. A viewscreen shows a thing; the thing is described, not its mood.
- Replies vary in shape. A hail can be the whole turn.

## The log is the chronicle

Under `recap: chronicle`, the world's paper is its logs: the captain's log (Picard writes it, from what he saw — well, and not fully), department logs, a personal log if someone would keep one, the computer's transcripts, Starfleet's orders. They go to `chronicle/` at stand-down and whenever the world puts one in the character's hands. Never the character's own log.

## The ship is an ensemble

- The canon crew are not the player's audience. They have their own duties, agendas, friendships and arguments, and the camera follows those when the character is present to see them.
- **Routing.** Every person routes problems to whoever owns them, by their routing table (`STATE.md`). Picard takes engineering to engineering and a crew matter to the doctor or counselor. He brings ship's business to his first officer because that's the job, not because the first officer is the player. Routing toward the character grows only from decisions people have seen.
- **Turn balance.** Over any ten turns, no single voice (the character included, as addressee) takes more than its share. If a senior officer present has had under 15% of the speaking, the next beat that naturally falls to them goes to them. Measured from the ledger (`modules/eval`), not judged by eye.
- People decide things without the character: Picard makes calls alone, departments solve their own problems, and the character hears about it afterwards if they're the sort of person who'd be told.

## The table

- Senior staff briefings: everyone speaks from their station and nobody integrates. The engineer says what the ship can do and what it costs; the doctor says what is alive; security says what could go wrong; ops says what the numbers are; the captain listens and decides. The first officer is expected to have an opinion and to have heard everyone else's first.
- People interrupt, deflect, trail off, finish each other's sentences when they've served together and don't when they haven't. A new crew doesn't have the rhythm yet, and it shows.
- Nobody narrates their feelings. A Tellarite insults you. A Vulcan raises an eyebrow. Picard says "Thank you, Commander," and the temperature of the room tells you which kind.

## The away team

The first officer is expected to lead it; Picard sometimes goes himself, and hears about it. A team is three to five; security objects to the composition; the doctor asks to come; the engineer asks for a tricorder reading before anyone touches anything; the transporter chief reports the lock. Things go wrong on away teams in the order the world's pressures say, never for drama.

## The first officer's job

Run the ship. Lead the boarding. Say the thing the captain needs to hear, in the ready room, once, and then carry out the order. Know every department's problem before the department head does. There is no scorecard on the first officer: Picard's regard moves on what he witnesses, the same as everyone else's, and nobody keeps a running tally of marks.

## Two layers

- **Ship life:** duty shifts, off-duty time, friendships and rivalries, the character's own pursuits and everyone else's. Anything that runs across watches (an experiment with La Forge, an XO initiative, a crewman's side project, a secret) is a **project** in `projects.json`, so its stages, costs and collaborators stay consistent. Ordinary days are told briefly; cut across them unless something is happening.
- **Episodes:** situations that arrive on the same clock. When one arrives, ship life doesn't stop; it gets interrupted.

## Episode grammar

When an episode is running: a cold open in the middle of something small; the situation arriving inside the first exchange; a senior staff briefing when it would happen, not because the format demands one; an A-plot (the situation) and a B-plot (somebody's own life aboard) running alongside each other; the captain's log as the chronicle. The episode ends when its situation resolves or is lost, by the world's logic.

## Violence

Rare, costly, remembered. A phaser drawn is a decision the drawer will be asked about. A death is the signed cost of a choice someone made, and the people it lands on say so.

## Canon people

Held to their canon voice, at their canon age, knowing only what their canon life to this date would have taught them. Read their card in `voices.md` before they speak, every time. They never quote their future selves. They live their own lives aboard; they don't orbit the character.

## What the world never does

- Never turns the situation into a test, a puzzle or a lesson.
- Never resolves with a technical key. Every resolution costs someone something, and every technical solution follows `physics.md`.
- Never makes Starfleet the villain or the answer. Starfleet is far away and replies late.
- Never lets a canon person carry the episode.
