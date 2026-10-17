# Deeds — who knows what you did, and how they work it out

Everything notable anyone does aboard leaves traces: a rescue, a promise kept, a sharp word at the briefing table, a brilliant fix at 0300, a prank, a theft. How people come to know about it — by seeing it, hearing about it, finding the record, or **working it out** — is what moves friendships, enmities, reputations and suspicions. Covert play is just the case where someone tries to keep the traces small.

The GM never decides who finds out. The traces, the people's relationships and the people's reasoning do.

## Acts

When anyone does something notable (the player or a crew member), the GM writes it into `state/deeds.json` as an **act**, with its traces and its **constraints**, before narrating it.

```json
{"id": "A-012", "actor": "player", "what": "rerouted the plasma conduit on deck 31",
 "at": 41190.4, "where": "deck 31, junction 4", "visibility": "unwitnessed",
 "valence": "credit",
 "constraints": {
   "means": {"codes": ["engineering-override"], "skills": ["warp-systems"], "areas": [], "systems": []},
   "opportunity": {"where": "deck 31", "window": [41190.3, 41190.5]}},
 "traces": ["T-031", "T-032"]}
```

- `visibility`: `open` (done in front of people), `unwitnessed`, or `concealed` (deliberately hidden).
- `valence`: `credit`, `blame` or `neutral`, as the world would see it if it knew.
- `constraints.means`: what doing it required. `opportunity`: where and when it had to be done.

## Traces

| Trace type | What leaves it | Who can read it |
|---|---|---|
| `location` | [canon] "Computer, locate…" answers anyone, live. [assumed] By combadge; history by security query. A trace records `subject`, `where` and `window`. | Live: anyone. History: security, by query. |
| `computer_access` | [assumed] Queries, file access and commands, with the authorisation used | Security and the captain, by query. |
| `authorisation` | [assumed] Command codes, overrides, lockouts | Logged permanently. An override of a log is itself logged. |
| `transporter` | [assumed] Every transport: source, destination, operator | Transporter chief, security, the captain. |
| `replicator` | [assumed] Usage by station and user | Ops and security, by query. |
| `door` | [assumed] Entry to restricted areas (armoury, brig, engineering core, computer core) | Security, by query. |
| `sensor` | [canon] Internal sensors: life signs, energy discharge, weapons fire aboard | The bridge, live, if anything trips an alert; otherwise a targeted sweep. |
| `witness` | Anyone who saw, heard or noticed | That person, and whoever they tell. |
| `physical` | Objects, residue, damage, a missing component, a repaired one | Whoever looks in the right place. |
| `behavioural` | Absences, changes in routine, a story with holes in it | Anyone who knows the person well enough. |
| `empathic` | [canon] Strong concealed emotion near Counselor Troi. She can't read some species (the Ferengi), and is fully telepathic only with Betazoids and Lloyd (canon's Riker). | Troi only: a feeling with no facts attached. |

The [assumed] rows are the most lore-plausible reading of what a Galaxy-class computer records. A `// lore objection` can move any of them, and the ruling becomes a precedent.

[canon] One exception: a Code 47 message, the captain's-eyes-only emergency channel, leaves no computer record of the transmission. Only a captain can use it, and the sender and receiver are still witnesses.

Covering tracks is an act with its own traces, often more telling than the original: an `authorisation` trace on a log deletion is evidence of intent.

## How word spreads

At each world turn, someone who holds a fresh belief about an act may pass it on to the people they're close to (`relationships` in their soul), if it's the kind of thing they'd share and they've had the chance. The receiver's belief is marked `heard_from` and is weaker than a witness's. It can be garbled, and it can be wrong. Nothing spreads faster than the people carrying it could manage.

Regard moves on what each person **witnessed** at full weight, on what they **heard** less, and always through their own regard economy (`gives_freely`, `gives_rarely`).

## Deduction

People don't only learn things; they work them out. When someone has a reason to wonder who did something (an alarm, a complaint, curiosity about a fix nobody admitted to), they reason over **means, opportunity and motive** from what *they* know.

- **Access profiles.** Every soul has `access`: the `areas`, `systems`, `codes` and `skills` they have. The player's character has one too. Rank and billet decide most of it; the XO's codes open almost everything, which puts the XO in almost every pool.
- **The suspect pool** is computed, not guessed: `python3 tools/wk.py suspects worlds/<world> --act A-012 --as yar`. It takes the act's constraints, if any trace of the act is readable by the reasoner, and returns everyone whose access meets the means and who isn't placed elsewhere during the window by a location trace the reasoner can read. If only one person could have done it, they're the suspect, with no witness needed. The same machinery finds the person to *thank*.
- **Competence is the quality of each reasoner's instruments.** Each soul has `competence.deduction` (`high` / `medium` / `low`) and `roles` (which logs they can read). High: works the whole pool out and acts on it. Medium: works it out once two constraints are in front of them together. Low: acts only on witnesses and direct evidence. Everyone's `wrong_about` is a blind spot that survives the arithmetic.
- **Suspicion isn't proof.** Picard can act on a suspicion (cooler regard, fewer duties, a question in the ready room). A court-martial needs evidence (`justice.md`).
- **Framing is play.** Using someone else's codes or planting a trace widens or redirects a pool, and leaves traces of its own.

## Cases and isolated investigators

A case opens when someone has a reason to look, never because the GM thinks it's time. While a case is open, the investigator's reasoning runs as a **separate fresh-context agent** at each world turn that gives them time:

1. The GM assembles the investigator's **light cone**: their soul and memory, the case, the traces they can read or have queried, statements actually given to them, and the computed pool for the act from `wk suspects`. No truth, no ledger, no transcript.
2. The agent returns JSON: conclusions, confidence, suspects, next step, anything they'd report.
3. The GM records a run on the case (`{watch, turn, act, isolated: true, cited, pool, suspects}`) and lets the investigator act. The validator recomputes the pool for every new run and rejects a mismatch, and rejects any citation outside the case's `known` traces.

The evaluation's `pool_ignored` metric flags any run where a medium- or high-competence investigator had a pool of exactly one person and didn't suspect them. That's the GM protecting someone.

## Recruiting

Asking anyone into anything secret is an act with a witness: the person you asked. Each decides from their own soul: values, loyalties, regard, what they stand to lose. Most Starfleet officers report a mutiny. Some won't, for reasons of their own. Troi senses that something is wrong around anyone carrying a secret like that.
