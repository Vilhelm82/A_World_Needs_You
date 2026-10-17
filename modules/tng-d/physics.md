# Physics — hard science as far as it reaches

Trek's technology keeps every capability and limit canon gave it. What changes is the explanation. Where the show waved its hands to keep the science behind the story, this world uses real physics plus a short, closed list of postulates, and the only reason the Federation can do what we can't is engineering. No magic.

## Three categories

Everything technical falls into exactly one:

1. **Real physics.** Orbital mechanics, relativity at sublight speed, thermodynamics, optics, biology, chemistry. Exactly as we know it.
2. **Technology canon technobabbled.** Warp drive, transporters, replicators, deflectors, phasers, sensors, inertial dampers, tractor beams, subspace radio. Each has a **mechanism card** (`canon/mechanisms.jsonl`), or gets one the first time the world relies on its physics: canon's capabilities and limits unchanged, a real-physics basis, the postulates it uses, the engineering gap, budgets, and failure modes.
3. **Canon unknowns.** Anything canon presents as beyond Starfleet's understanding: Q, the Traveler, and the like. **The GM never explains them.** They're black boxes (below). The show never tried, so there's nothing to replace.

A claim that puts something in the wrong category is a lore failure: technobabble used as an explanation, or the GM "explaining" a canon unknown, is `contradicts`.

## The postulates (closed list)

Real physics plus these, and nothing else. Adding or changing one is a harness change: a proposal, Will's approval, and a changelog line.

- **P1. Subspace geometry.** A physical domain coupled to ordinary spacetime exists. Fields of sufficient energy density, which antimatter power can reach, can shape spacetime's local geometry through it. This underlies warp propulsion, artificial gravity and inertial damping, tractor beams, and shaped deflector fields.
- **P2. Subspace causality.** Anything carried through subspace or inside a subspace-shaped geometry (signals, ships, fields) can travel faster than light. All of it shares one preferred causal frame, so under normal operation none of it produces a causal paradox, and a ship keeps control of its own warp field across the field's wall. The rare time anomalies canon shows are exactly that, rare and anomalous.
- **P3. Dilithium.** Some crystalline materials interact with subspace, so they can regulate matter–antimatter annihilation without being consumed by it.
- **P4. Transport fidelity.** A matter stream and its complete state information can be carried through subspace and reassembled, with losses held below biological significance by systems canon calls Heisenberg compensators. How they beat the uncertainty limit is the one piece of transporter engineering left as a black box.
- **P5. Neutrino conversion.** A driven interaction converts ordinary matter into neutrinos and antineutrinos, conserving energy, momentum, charge and B−L. It runs only while driven and never sustains itself. This is phaser disintegration: the target's own mass-energy leaves as neutrinos, which pass through ordinary matter almost untouched. Every known way of destroying baryons ends mostly in photons and pions; this channel is the one thing real physics allows but doesn't provide.

Everything else must derive from real physics plus these five. If it can't, it's magic, and it fails the lore check.

## Mechanism cards

One JSON object per line in `canon/mechanisms.jsonl`, append-only like the other cards:

```json
{"id": "M-003", "tech": "transporter",
 "canon_capabilities": ["beams personnel and cargo over tens of thousands of km"],
 "canon_limits": ["can't beam through raised deflector shields", "needs a lock"],
 "physics_basis": "Destructive measurement and reconstruction of quantum state, as in quantum teleportation; the no-cloning theorem forbids copying the original, which is why it's destroyed...",
 "postulates": ["P2", "P4"],
 "engineering_gap": "Measuring and transmitting the full state of ~10^28 atoms in seconds...",
 "budgets": [{"quantity": "rest-mass energy of a 70 kg person", "value": "6.3e18 J",
              "basis": "CALC: 70 * c**2"}],
 "failure_modes": ["lock loss mid-transport", "pattern degradation in the buffer"],
 "sources": ["https://memory-alpha.fandom.com/wiki/Transporter", "https://en.wikipedia.org/wiki/Quantum_teleportation"],
 "verified_at": "2026-10-18", "supersedes": null}
```

Canon capabilities and limits are cited to canon. The physics basis is cited to real physics. Budgets are computed, never estimated (below).

**Written case by case.** The starter cards cover the ship's core systems. Any other technology gets its card the first time the world relies on its physics: a number worked out from it, a technical solution built on it, an experiment, a failure, or a `// lore objection`. Using a technology on screen (beaming down, going to warp) needs only canon's capabilities and limits, which the lore cards hold. When a turn's lore check finds no card, the lore agent writes one in physics mode, consistent with every existing mechanism card: cards that share a postulate share physics, so a tractor-beam card written in watch 9 must agree with the warp card from watch 2.

**Nobody speaks physics past a card's edge.** When a conversation goes deeper than a card covers, the lore agent extends the card first (a superseding card), and only then does anyone answer. Physics is written before it's said, the same as facts.

**The edge of known physics is in-universe too.** Every card's engineering gap and every black box is something the crew know is unsolved. Asked about one, La Forge or Data say it's an open problem, in their own words, and it can become a hypothesis or a project. Each knows their own field: La Forge knows budgets and how things fail, Data the theory and the literature, and "I don't know, but we could find out" is in character for both. A hole the player finds is a research question, never a technobabble patch.

**Where canon contradicts itself,** the card takes the reading physics supports, explains the others by conditions where it can (power, range, interference, regime), and records the choice. Most of canon's contradictions come from hand-waving, so the physics usually settles them.

## Numbers are computed, not narrated

Any number the world relies on (an energy budget, a transit time, a relativistic time dilation, a sensor's diffraction limit, a heat load, a radiation dose) is calculated, not guessed:

```
python3 tools/wk.py calc "70 * c**2"
```

The calculation is logged as a `CALC` ledger entry (`expression`, `result`, `units`, `purpose`), and the validator re-evaluates every new one and rejects a wrong result. The calculator knows the physical constants (`c`, `G`, `h`, `hbar`, `kB`, `e`, `me`, `mp`, `NA`, `ly`, `au`, `pc`, `year`, `day`, `hour`) and Python's `math` functions.

The crew carry the physics as engineering constraints, in their own words, when it matters to them. La Forge gives numbers when asked. The narrator never lectures (perception is pull).

**The vocabulary stays Trek's.** Mechanism cards are sealed background, never dialogue. On screen it's still warp fields, EPS conduits, the annular confinement beam and Heisenberg compensators; each term now names something specific on a card, so what one scene says about it binds the next. Ordinary physics keeps its ordinary words where a 24th-century engineer would use them (neutrino, relativistic, radiation dose), as canon does. Nobody name-drops 21st-century theory.

## Technical solutions

The rule that replaces "no technobabble keys". A technical solution is allowed when it:

1. **derives** from real physics, the postulates and the mechanism cards, and passes a lore check;
2. **was set up**: the capability, reading or anomaly existed in the world before it was used;
3. **costs** something: time, parts, power, risk, the schedule, or trust if it fails;
4. **comes from the people**: the crew or the player works it out from what's on the table. The GM never hands it over.

A solution that works becomes a precedent, so it works the same way next time.

## Unknowns are black boxes

For a canon unknown, the sealed state holds **no hidden explanation**. It holds only the **observation record** (`state/unknowns.json`): what canon showed on screen, as cards, plus every measurement made in this branch, as facts. The GM can't steer toward an answer it doesn't have.

- **Undetermined outcomes are rolled.** This is the world's only use of chance, an exception to `resolution: causal` that Will has ruled on. When an experiment's result isn't fixed by canon's record, physics or precedent, the GM writes the outcomes consistent with all three, **then** rolls real dice (`ROLL` with `outcomes`, `roll` and `result`). The GM can't choose the outcome that flatters a theory or the one that crushes it.
- **A roll never becomes a liability to later science.** Three guards:
  1. The outcomes must fit everything canon ever showed of that unknown, across every series, not only what's known by 2364. Later canon can't contradict an outcome canon never ruled out.
  2. The result is a scoped observation fact, never a precedent or a law: what was probed, with which instrument, at what resolution and margin, under which conditions. "The pallet registered a 4 millicochrane spike during the manifestation, at the edge of its resolution", not "Q is made of subspace energy".
  3. Later evidence that conflicts with it reinterprets it and never rewrites it: the explanation (an instrument artifact, different conditions, a limit of resolution) goes in as a new fact with `reinterprets` naming the old one.
- **The unknown's behaviour stays its own.** Q acts as canon's Q, in this branch's circumstances. No experiment or theory changes what Q is.

## Hypotheses survive; they're never crowned

Anyone, the player most of all, can propose an explanation and test it. Hypotheses live in `state/hypotheses.json`:

- the statement, who proposed it, who holds it, its physics basis, and **predictions** (if this, then that);
- **tests**: which prediction, what was done (an act or project), the observation it produced (a fact), and the result: `supported`, `falsified` or `inconclusive`.

A hypothesis that keeps passing becomes `surviving`: a working theory people can act on, publish and argue about. It never becomes sealed truth. If a later observation falsifies it, it's `falsified` permanently; a better idea is a new hypothesis that cites the old one. A new hypothesis may also revive a falsified one (`revives`), but only through a fact that reinterprets an observation that falsified it, and the validator checks that chain. Being studied is itself an event: Data is fascinated, Starfleet takes interest, and Q, by canon nature, notices.

The same path applies to technology. If the player and La Forge find something new about warp fields, it's a hypothesis, then tests, then a precedent.
