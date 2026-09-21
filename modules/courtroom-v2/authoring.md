# Authoring V2: a shared world, separately grounded people

New live cases require `schema: 2` and `authoring_version: 2`. The exact field
contract and validation sequence are in [the schema specification](../../docs/courtroom-authoring-v2-design.md).
The controller implementation is `tools/courtroom_authoring.py`; the seven fixed
witness templates live in `witness-templates.json` in this module.

## Author before play

Write a situation, not a predetermined victory. Commit the historical past before
seeing player strategy. Personal stakes and ambiguous evidence need not imply a
conspiracy, liar, confession or hidden exonerating clue. Nervousness and confidence
are not truth detectors. No preferred verdict belongs in the case.

Use a fresh author context. It must never become a courtroom identity context.
Each counsel, witness, judge context and individual juror uses its own persistent
session. The human player has no model session. The controller routes and validates;
it does not generate character reasoning or speech.

## Sealed substrate and identity views

Declare all four `substrate` stores: `space`, `time`, `records`, `flows`. Empty maps
are explicit. Name actors and offstage `entities`; declare the integer `time_scale`.
Locations specify adjacency, distances, sightlines, lighting and access. Time entries
contain visual, audible or actor-only facts. Records contain exact content, actual
receipts and sealed provenance/alterations. Flows link parties, events and records.

Role positions, access, perception channels, actual receipts and participation
compute the envelope. Receiving a record exposes its contents, never hidden
provenance or alterations. A visible transfer does not reveal private intentions.
Only projected facet references and text reach the identity; no raw substrate,
other identities' allocations or catalogue of hidden entries is delivered.

`perception_limits` narrow specific owned facets. The raw facet is withheld and its
bounded account is supplied instead. Outside-envelope ignorance is automatic: no
personal basis, not proof an event did not happen. It cannot justify invented
amnesia, a denial of qualifications, or missing authoring of the witness's own life.

Witness `template` selects lay eyewitness, party, expert, records custodian,
investigator, institutional representative or associate (underscore IDs in JSON).
Each fixes mandatory families, depth and routine domains; cases cannot reduce them.
Every identity has routine, deltas, account/divergences, pressures, manner and
fallibility. Routine describes actual usual procedure: steps, tools, sequence,
choices. Routine does not establish that a particular episode followed it. Deltas
must reference the identity's routine and perceived event.

An account difference needs a declared reason: lie, honest error, loyalty,
embarrassment, fear or unrelated concealment. A witness cannot use divergence as a
route to someone else's unperceived secret. Every identity needs an innocent
pressure; both sides need an affiliated witness capable of authored error or bias.
Manner expresses proximity to any pressure, not a truth/guilt switch. Shared-event
views derive from one entry; differences require a limit or explained divergence.
A contested issue's sole unshared anchor needs an explicit `single_source` reason.
Issue anchors are sealed and stripped from courtroom packets.

Use `compile_case` to generate the public exhibit and receipt caches, then
`validate_foundation`. V2 rejects freehand `knowledge`, old background/activity
fields, case-owned coverage templates and manual amendment consistency maps.
Bench and jurors start with empty historical envelopes. Civil/criminal, bench/jury,
either player side, US-inspired/NSW-inspired/custom presentation, multiple counts,
hung/mixed outcomes and deterministic verdict thresholds remain independent choices.
Supply actual simulation rule text and disclose simplifications; true-law scenarios
need verified sources. Exact transcripts are append-only. Keep routine paperwork
compressed; focus on conferences, theory, examinations, objections, closings and decisions.

## Every answer has a source

Vary wording and manner; never improvise historical colour. Every V2 witness answer
includes sealed `grounding: {refs: [...], boundaries: [...]}`. Sources are owned
substrate facets, perception limits, routine steps, deltas, divergences or events
actually heard. The controller verifies existence and ownership before recording
speech. Missing/invalid citations pause the simulation and preserve the rejected
response in its sealed audit. Existence is not proof that prose follows the source.

Use the five-way distinction: never knew; knew but cannot recall; recalls
approximately; knows but withholds within the committed account; never authored.
Only the last is an authoring gap. Uncertainty needs an owned perception or routine
citation. Absence is never a negative historical fact. Materiality is argued in
court; no witness decides whether an invented fact is safe.

A gap returns empty speech and `authoring_gap`. The public notice says the
simulation could not ground an answer. No in-world hesitation, evasion or credibility
cue accompanies it; no other identity hears the interruption. Bare repair is refused.
Resolution must cite entitled existing sources (delivery repair or supported
resolution), or follow the explicitly chosen amendment procedure.

## Coverage readiness gate

Run `tools/courtroom.py rehearse --case INPUT --out NEW_OUTPUT --config RUNTIME`.
It calls real isolated models, keeps reports sealed and refuses commitment on
failure. Structure alone is not readiness. Old or mock reports cannot authorise
new live play; changing authored content invalidates the report digest.

Every family has a root question and twice its template weight in natural informed
follow-ups. Follow-ups target visible routine steps and substrate facets. A separate
blind examiner sees only public setting and template and generates a probe for every
family. Author-declared deliberately unauthored positive-history probes are counted
separately (at least two per witness). Off-topic questions are diagnostic, never a
place to hide failed ordinary coverage.

Two independent graders see identical frozen answers and permitted sources, no
peer assessment or sealed world. Disagreements invoke a third independent grader;
classification and hearing plausibility each use majority. Three-way splits are
sealed patch targets for a fresh author and require a new rehearsal. Report raw
two-grader agreement, tiebreakers, splits, each family and each probe class. Raw
assessments remain preserved. Invalid witness citations are controller defects even
if graders approve the prose. Ordinary answers citing fewer than three distinct
source layers flag author review without changing the pass threshold.

The unchanged threshold is 100% grounded/authored uncertainty for ordinary answers,
zero ordinary gaps and zero inventions. Plausible blind-probe gaps fail. Deliberately
unauthored author probes must gap. Off-topic gaps are allowed only when grading
finds them outside plausible hearing coverage. Inventions fail in every group.
A passing finite exercise cannot prove complete coverage or infallible grading.
Human exceptions require both `--confirm-human-review` and
`--reviewer-will-not-play`; never ask a player to read sealed witness knowledge.

## Corrections and amendments

`// ground` checks a recorded answer; configured random sampling also checks confident
answers. The referee sees only that witness's permitted sources and public rules,
returns supported/supported uncertainty/missing coverage with refs, and invents no
replacement fact. Failure preserves the original record, corrects its status,
withdraws dependent context and rebuilds affected sessions. The referee is fallible,
not a substitute for authoring depth. The pause/check is a meta-signal the player
cannot unlearn; this is accepted and disclosed.

Strict fixed-case play never silently changes history. Explicit player choice of
`amend --topic TOPIC --accept-amended-case` uses only precommitted topic envelopes.
Author-declared envelopes and envelopes derived from accepted rehearsal probe gaps
are counted separately. Envelopes do not waive the readiness gate.

Targets include space, time, records, flows, or witness. Substrate additions
reproject all identities, including newly eligible recipients/observers. Witness
patches are restricted to routine, pressure points and manner. Account/divergence
changes must reference the amended substrate entry. Existing historical scalar
facts cannot be overwritten. Original commitment bytes remain unchanged.

Three independent fresh authors each receive identical blinded constraints and
source excerpts, never player side, theory, live question or desired outcome. The
checker receives the target and linked entries plus affected identities' committed
accounts, derived from shared references. This sealed, fresh technical session is
a documented exception to the no-sealed-truth rule. It supplies only pass/fail with
reasons and closes after the check. No courtroom identity receives those excerpts.

Any failed candidate rejects the whole set. Retries use new authors up to the
configured cap. The system selects uniformly among the accepted distinct candidates;
records attempts and sealed alternatives; links the amendment commitment; discloses
that the case changed; rebuilds affected contexts and reopens dependent decisions.
The amended draft must pass rehearsal. Candidate sets can still be skewed, and the
requested topic reveals the direction of inquiry despite blinded inputs.

## Migration

Never patch a committed old-format world to pass this gate. Last Light and Second
Signature remain blocked. A replacement draft is a new world with a new commitment.
Historical structural readers and labelled deterministic fixtures remain supported.
Separate provider sessions plus packet filtering provide application-level
isolation; provider infrastructure may still be shared beyond program control.
