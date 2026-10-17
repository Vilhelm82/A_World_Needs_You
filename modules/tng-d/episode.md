# Episodes — how a situation is built, arrives and closes

The ship's routine never stops. An episode is a situation that **arrives** on the ship's clock. It is built ahead of time, in the background, and lands when its causes say it does.

## When the next episode is built

When no episode is open and none is pending, the GM builds one at the next stand-down or open. It sits in `state/episodes/<id>.json` with status `pending` and an `arrival` (what has to be true for it to reach the ship: a course, an order, a date, a force's next step). Until then, ship life runs.

## Where situations come from

1. **The branch's own history.** Consequences in motion (`in_motion`), the crew's agendas, unresolved threads, a force's next step meeting the ship's course. This is the main source, because it is original by construction: no canon episode has this history.
2. **Seeds from outside the author.** Real astrophysics, biology, anthropology, history, law: the "what if" TNG's writers used. Draw from a list of at least six candidates with nothing in common, roll a die from the shell, and take what falls. Record the candidates and the roll in `state/premises.json`.
3. **Never** a canon episode's plot. A force can bring canon *people* and *capabilities* on stage; it can't bring a canon *situation*.

## Build checks — all before anything surfaces

- **Canon distance.** Name the three canon episodes the premise most resembles and say how this situation differs from each. If a TNG fan would call it "basically that episode", bend it until they wouldn't.
- **Premise log.** It isn't a re-skin of anything already in `state/premises.json`.
- **Particular** and **Sound**, as in `CLAUDE.md`.
- **Lore.** Every technology, procedure and species behaviour it needs is in `law.md`, in precedent, or plainly canon for 2364. Anything else gets written as a new [assumed] precedent with its reasoning, so the audit can check it.
- **Ensemble.** The episode's truth names which crew members it lands on, beyond the character, and a B-plot that runs whether the character engages or not.

## The truth of an episode

As in `CLAUDE.md` (layers, sources that lie, three doors per secret, several resolutions with costs, pressures as processes, movers, distance per resolution, in-motion). Also: the forces involved and each one's step; whose regard the outcome could move; what evidence any covert angle would leave.

## Closing

An episode closes when its situation resolves or is lost, by the world's logic. Picard writes the log (chronicle). The record marks it `closed`, carries what it set going into `in_motion`, and updates each force's divergence. The next episode is built from that, and from what the ship was already doing.
