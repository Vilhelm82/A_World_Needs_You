# Law — Star Trek: The Next Generation, USS Enterprise-D, 2364

The world's constitution. Thin on purpose: what it fixes is the era, the ship, how things work and what they cost. Everything else is decided in play and becomes binding as precedent (`state/precedents.json`).

Every line here is one of two kinds:
- **[canon]** — established on screen by this date. Not negotiable.
- **[assumed]** — not shown on screen, chosen because it is the most lore-plausible reading. Binding until a `// lore objection` overrules it; the ruling then goes to precedent.

## The lore base

This file is the constitution. The detail lives in `canon/cards.jsonl`: short, cited, layered reference cards that grow from verified checks and can't be edited, only superseded (`canon/README.md`). The GM checks lore against them at any time with `python3 tools/wk.py lore`, before relying on anything canon governs.

## The branch point

- [canon] History up to stardate 41153.7 — the Enterprise-D's first mission, to Farpoint Station — is the show's history, with one change, Will's ruling: **Commander Will Lloyd stands in William Riker's shoes.** He lived Riker's life, and there is no William Riker in this branch. Wherever canon before the branch says Riker, read Lloyd.
- **What stays invariant** is everything canon's continuity depends on, and those are Lloyd's now:
  - Starfleet Academy 2353–57, eighth in his class; Paul Rice a friend there.
  - Conn officer on the Pegasus under Captain Pressman, and the secret of what happened to her, kept since.
  - A posting on Betazed, where he and Deanna Troi became imzadi; the telepathic link between them.
  - Lieutenant in operations on the Potemkin; the Nervala IV rescue in 2361, after which a duplicate of him was left on the surface, unknown to anyone; promotion to lieutenant commander for that mission.
  - First officer of the Hood under Captain DeSoto; refusing to let DeSoto beam into danger at Altair III, the act that put his file in front of Picard.
  - Turning down command of the Drake, which went to Paul Rice.
  - His father, Starfleet's own Kyle (here a Lloyd), and the estrangement since he was fifteen.
- **What is Lloyd's own:** any detail that makes no material difference to canon's continuity. He was born and raised in Australia, not Alaska. Every other variation he states goes in `worlds/enterprise/sheet.md`; whatever he hasn't stated follows canon.
- [assumed] The Farpoint mission itself happened as the show had it, with Lloyd in Riker's place: the Hood ferried him to Deneb IV, he made the manual saucer docking, he led the away teams that found the station's secret, and Q took an interest in him. How he did it is Lloyd's to state. Play opens as the Enterprise leaves Farpoint. *(Will may overrule this and play Farpoint itself.)*
- After the branch, **no canon episode is scheduled.** Canon survives only as *forces* (`forces.md`): who wants what, what they can do, and their next step if nobody stops them. Where the Enterprise is decides whether a force meets her.

## The era, 2364

- [canon] Stardates 41xxx. Starfleet's flagship is new: the Enterprise-D, Galaxy class, recently commissioned.
- [canon] The Romulans have had no direct contact with the Federation since the Tomed Incident (2311). They have struck at the Klingons since (Khitomer, 2346). Everyone assumes they are watching.
- [canon] The Ferengi are a name and a reputation, with no Federation contact on record. Nobody yet knows that the ship which destroyed the Stargazer at Maxia (2355) was Ferengi.
- [canon] Starfleet has no record of the Borg. The name survives only as rumour among a few exobiologists (the Hansens, lost in 2350) and El-Aurian refugees.
- [canon] The Klingon Empire is an ally. Worf is the first Klingon in Starfleet (established later, in DS9). Not every Klingon accepts the alliance.
- [canon] The Federation–Cardassian war, running since the 2340s, is unfinished: a stalemate with skirmishes. Season one never mentions it; veterans aboard (O'Brien served at Setlik III) remember it.
- [canon] Data is the only known android of his kind. Nobody, Data included, has connected him to Noonien Soong. His status as a person has never been tested in law.

## The ship

- [canon] Galaxy class. About a thousand aboard, families and children included — a town, not a warship. The saucer can separate from the stardrive section; the battle bridge runs the stardrive alone.
- [canon] Holodecks. Replicators. Transporters need a lock and lowered shields.
- [canon] The computer answers by voice anywhere aboard. "Computer, locate [person]" returns where a crew member is, to anyone who asks. [assumed] It works by combadge.
- [canon] Internal sensors read life signs aboard and can be tuned to look for something specific; the operator says what they can and cannot resolve.
- [canon] Ten Forward exists (Picard's welcoming reception was held there), though nothing in season one shows it. No Guinan yet; she comes aboard in 2365.
- [canon] The chief engineer hadn't come aboard before Farpoint, and season one shows MacDougal, Argyle, Logan and Lynch in the billet at different times. [assumed] The world fixes who holds it now at build. Geordi La Forge is a flight controller, not chief engineer.
- [assumed] What the computer logs and who can read it is in `deeds.md`. That list is the boundary of what anyone can find in the records.

## What works and what it costs

- [canon] Warp drive. Live subspace calls work over moderate range; far out, a message takes a day or more each way, so the captain decides in the field and Starfleet's ruling arrives afterwards.
- [canon] Code 47: a captain's-eyes-only emergency channel that leaves no computer record of the transmission.
- [canon] Phasers have stun. A phaser drawn aboard ship is a decision someone will ask about.
- [canon] Sickbay heals most injuries. [assumed] (house rule) Death is rare and is the signed cost of a decision.
- [assumed] (house rule) Hard science as far as it reaches (`physics.md`): every technology keeps canon's capabilities and limits, explained by real physics plus four closed postulates, with only an engineering gap between it and us. A technical solution must derive from that, be set up beforehand, cost something, and come from the people, never from the GM. Canon unknowns (Q, the Traveler) stay unexplained.
- [assumed] (house rule) The universal translator works from samples and gets new languages wrong confidently at first.

## Starfleet

- [canon] The captain commands. The first officer runs the ship day to day, is expected to lead away teams and to object when the captain wants to go himself (Picard sometimes goes anyway), and to disagree with the captain in private and back him in public.
- [canon] Ranks, lowest up: ensign, lieutenant junior grade, lieutenant, lieutenant commander, commander, captain.
- [canon] Senior staff meet at the observation lounge table. Decisions are the captain's; the arguments are everybody's.
- [canon] The Prime Directive is argued at that table every time it applies.
- [assumed] Starfleet is not a navy and its officers say so. (Picard says it on screen in 2365.)
- Justice, discipline and investigation: `justice.md`.

## Themes

Moral dilemma over firefight. Contact as a problem of understanding. What a person is. Duty against conscience. The crew as people with lives the plot does not own.

## Discarded

Every canon episode after the branch, as an event. Its forces stay; its plot does not happen unless the world's own logic produces something like it, and even then it is never the same situation.
