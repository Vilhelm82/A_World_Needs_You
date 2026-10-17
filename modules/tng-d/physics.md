# Physics — hard science as far as it reaches

Trek's technology keeps every capability and limit canon gave it. What changes is the explanation. Where the show waved its hands to keep the science behind the story, this world uses real physics plus a short, closed list of postulates, and the only reason the Federation can do what we can't is engineering. No magic.

## Three categories

Everything technical falls into exactly one:

1. **Real physics.** Orbital mechanics, relativity at sublight speed, thermodynamics, optics, biology, chemistry. Exactly as we know it.
2. **Technology canon technobabbled.** Warp drive, transporters, replicators, deflectors, phasers, sensors, inertial dampers, tractor beams, subspace radio. Each gets a **mechanism card** (`canon/mechanisms.jsonl`): canon's capabilities and limits unchanged, a real-physics basis, the postulates it uses, the engineering gap, budgets, and failure modes.
3. **Canon unknowns.** Anything canon presents as beyond Starfleet's understanding: Q, the Traveler, and the like. **The GM never explains them.** They're black boxes (below). The show never tried, so there's nothing to replace.

A claim that puts something in the wrong category is a lore failure: technobabble used as an explanation, or the GM "explaining" a canon unknown, is `contradicts`.

## The postulates (closed list)

Real physics plus these, and nothing else. Adding or changing one is a harness change: a proposal, Will's approval, and a changelog line.

- **P1. Subspace geometry.** A physical domain coupled to ordinary spacetime exists. Fields of sufficient energy density, which antimatter power can reach, can shape spacetime's local geometry through it. This underlies warp propulsion, artificial gravity and inertial damping, tractor beams, and shaped deflector fields.
- **P2. Subspace signalling.** Information can propagate through subspace faster than light. Under normal operation, this produces no causal paradoxes; the rare time anomalies canon shows are exactly that, rare and anomalous.
- **P3. Dilithium.** Some crystalline materials interact with subspace, so they can regulate matter–antimatter annihilation without being consumed by it.
- **P4. Transport fidelity.** A matter stream and its complete state information can be carried through subspace and reassembled, with losses held below biological significance by systems canon calls Heisenberg compensators. How they beat the uncertainty limit is the one piece of transporter engineering left as a black box.

Everything else must derive from real physics plus these four. If it can't, it's magic, and it fails the lore check.

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

## Numbers are computed, not narrated

Any number the world relies on (an energy budget, a transit time, a relativistic time dilation, a sensor's diffraction limit, a heat load, a radiation dose) is calculated, not guessed:

```
python3 tools/wk.py calc "70 * c**2"
```

The calculation is logged as a `CALC` ledger entry (`expression`, `result`, `units`, `purpose`), and the validator re-evaluates every new one and rejects a wrong result. The calculator knows the physical constants (`c`, `G`, `h`, `hbar`, `kB`, `e`, `me`, `mp`, `NA`, `ly`, `au`, `pc`, `year`, `day`, `hour`) and Python's `math` functions.

The crew carry the physics as engineering constraints, in their own words, when it matters to them. La Forge gives numbers when asked. The narrator never lectures (perception is pull).

## Technical solutions

The rule that replaces "no technobabble keys". A technical solution is allowed when it:

1. **derives** from real physics, the postulates and the mechanism cards, and passes a lore check;
2. **was set up**: the capability, reading or anomaly existed in the world before it was used;
3. **costs** something: time, parts, power, risk, the schedule, or trust if it fails;
4. **comes from the people**: the crew or the player works it out from what's on the table. The GM never hands it over.

A solution that works becomes a precedent, so it works the same way next time.

## Unknowns are black boxes

For a canon unknown, the sealed state holds **no hidden explanation**. It holds only the **observation record** (`state/unknowns.json`): what canon showed on screen, as cards, plus every measurement made in this branch, as facts. The GM can't steer toward an answer it doesn't have.

- **Undetermined outcomes are rolled.** When an experiment's result isn't fixed by canon's record, physics or precedent, the GM writes the outcomes consistent with all three, **then** rolls real dice (`ROLL` with `outcomes`, `roll` and `result`). The result becomes an observation and a precedent. The GM can't choose the outcome that flatters a theory or the one that crushes it.
- **The unknown's behaviour stays its own.** Q acts as canon's Q, in this branch's circumstances. No experiment or theory changes what Q is.

## Hypotheses survive; they're never crowned

Anyone, the player most of all, can propose an explanation and test it. Hypotheses live in `state/hypotheses.json`:

- the statement, who proposed it, who holds it, its physics basis, and **predictions** (if this, then that);
- **tests**: which prediction, what was done (an act or project), the observation it produced (a fact), and the result: `supported`, `falsified` or `inconclusive`.

A hypothesis that keeps passing becomes `surviving`: a working theory people can act on, publish and argue about. It never becomes sealed truth. If a later observation falsifies it, it's `falsified` permanently; a better idea is a new hypothesis that cites the old one. Being studied is itself an event: Data is fascinated, Starfleet takes interest, and Q, by canon nature, notices.

The same path applies to technology. If the player and La Forge find something new about warp fields, it's a hypothesis, then tests, then a precedent.
