# Authoring a new courtroom world

## Fixed before play

Write a situation, not a predetermined victory or puzzle answer. It should have
personal stakes, a small number of consequential disputed propositions, credible
participants and more than one defensible reading of some evidence. There need not
be a conspiracy, a liar, a confession, an innocent client, or a hidden exonerating clue.
Do not imitate the animation argument from the development conversation.

The case-authoring context must never become a courtroom identity context. Author
before reading player strategy. Start all independent identities in separate persistent
backend sessions after commitment. Never claim an independent audit you did not run.

A focused case often needs 3-6 material witnesses and 6-12 useful documents, but these
are authoring suggestions, not code limits. Avoid multiplying exhibits that repeat one
fact or adding a cast for spectacle. Every important document needs exact usable text.

For witnesses settle: actual access, observations versus inference, known records,
ordinary memory limits, any pre-existing mistaken or false account and its limits,
interests, distinctive voice and plausible scope of cooperation. Evasiveness is not a
truth detector. A question can expose a discrepancy; it cannot create a new memory.

## Witnesses are people, not document readers

Before commitment, every witness must have a `background` object containing
nonempty authored text for `life_history`, `occupation`, `training_and_qualifications`,
`relationships`, and `personal_stakes`. Define concrete experience and abilities;
explicitly state no qualifications or no relationship where appropriate. These are
facts the person knows about themselves, whether or not any exhibit records them.

Supply one or more `relevant_activities`, each with `description`, `purpose`,
`actions`, `tools_and_materials`, `authority`, and `limits`. Describe what the person
actually did or perceived, in usable detail. "Performed an authorised service check"
does not specify any work. Identify the equipment or subsystem, the steps performed,
the person's competence and authorisation, and what they did not inspect or know.
For a bystander, describe their observation and its circumstances; do not invent a
trade or require irrelevant technical credentials. A lack of equipment or special
authority is a concrete answer, not an empty field.

Also author `memory`, `perception_limits`, `motives`, and `manner`, alongside the
existing `knowledge` and `knowledge_basis`. Preserve genuine uncertainty and any
committed false account or evasive motive. These fields never encode global author
truth or facts learned only by another identity. Private background belongs solely
to its witness until communicated through a recorded event. No output-length limit
may narrow the substance or scope of testimony.

Rehearse ordinary foundation questions against each isolated packet before calling
the case ready: what do you do; what training or licence do you hold; what exactly
did you do here; with which tools or materials; why and under whose authority; how
do you know; what can you not remember or perceive? Check likely follow-ups as well.
Answers must follow from committed personal facts, not from the absence of words
in an exhibit. Reconcile activities, qualifications, chronology and documents with
the fixed past, without engineering a preferred verdict. Do this before seeing
the player's theory. Do not count a completed form as a semantic review.

`witness_scaffold()` supplies placeholders for these fields. Placeholders do not
pass readiness. `validate`, case building, startup and backend-check enforce their
presence. Commitment additionally requires the coverage rehearsal below; historical record verification still accepts the older structural schema.
The original Last Light and Second Signature examples lack these foundations and
are reference material only, not launch-ready scenarios. Never patch an existing
world's committed case to make it pass the new gate.

If the knowledge needed to answer was never authored, the witness returns
`{"text":"","data":{},"authoring_gap":"description of missing fact"}`. The
controller pauses and records a neutral engine notice, never testimony. The
description remains sealed; it must not reveal a private witness fact to the player.
The host must not portray this as evasiveness, hesitation, deceit, lack of credentials
or faulty memory. In strict play resolve only from already committed material. An explicitly chosen
amended continuation follows the separate workflow below; otherwise abandon/rebuild.
A bare `repair` cannot bypass missing knowledge.

For documents settle: author, date, intended audience, provenance, any alteration,
relationship to other sources, who has received it, and initial evidentiary status.
Do not place truth annotations, hidden provenance conclusions or private instructions
in text that will be given to counsel, judge or jury. Store those in `truth` or bounded
role knowledge, not the neutral summary. A common-source anomaly is not independent
corroboration just because five documents reproduce it.

Predefine timeline, relevant physical constraints and what cannot be established.
For an unanticipated question, answer explicit fixed facts or necessary consequences.
There is no permission to invent historical colour. Vary phrasing and manner, never
add clothing, habits, qualifications, relationships or physical actions. Materiality
is argued in court, never decided by the witness at answer time. Record a gap when
knowledge is missing; absence never means "I do not have one". Unknown is not proof of a favoured explanation.

## Schema 2 fields

`schema:2`, `draft:false`, `case_id`, `title`, `law_status:"simulation"`.

`config` holds independent `case_type:civil|criminal`, `factfinder:bench|jury`,
`player_side`, `style:us-drama|nsw-drama|custom`, `jurisdiction` (explicit fictional
or adapted setting), `pace:drama|deliberate`, `jury_size`, `verdict_threshold`.
For bench use zero/zero; for jury, 2-24 allocated jurors and a threshold above half
and at most the panel size. Defaults are presentation decisions, not universal law.
The profile builder supplies compatible initial values; a fully authored custom case
can pair a style with a separately described fictional jurisdiction/rule packet.

`public_summary`: neutral allegations and issues. Every role sees it; never secret
fact or author judgment. `brief`: counsel's shared procedural brief. Confidential
instructions belong only to that counsel role. `truth`: author-only complete material
past. `opening`: setup situation for the coordinator, not live character speech. The first
spoken line must come from the appropriate independent identity session.

`procedure`: plain-English governing game procedure. `authorities`: source provenance
and explicit simplifications. `rules`: actual rule text keyed by IDs. No nonexistent
statutes, cases or quotations. The stock R1-R12 rules are explicitly game rules.
A requested true-law scenario needs verified sources and disclosed limits; do not
claim the generic profile is current legal advice.

`roles`: arbitrary safe IDs, with player/opponent/bench required. Each has name,
kind (counsel, bench, witness, juror, support), knowledge list and document ID list.
Witnesses need `knowledge_basis`. Bench/jurors start with no case knowledge or private
documents. Their public manner can differ; never predetermine votes, set "secretly
favours Will", or map protected demographics to guilt judgments. Jurors belong to one
jury, not a gallery of people to individually flatter. The player remains counsel.

`documents`: safe IDs such as E01/WS1, each with title, text, provenance, status and
uses. T-number IDs are reserved for events. Disclosed/excluded items have no merits
uses; admitted/limited items specify truth/notice/context/credibility. Pre-admitted
items must already be known to both parties and still need jury publication.

`issues`: safe IDs with text, party carrying the burden, and standard. `counts`:
each charge/claim has label, required `elements` (issue IDs), optional `bars` and an
optional civil `remedy:{currency,maximum}`. Multiple counts may share elements; do
not count the same observation as independent support. Each count's required issues
must use the initiating party's standard. A bar is an explicitly specified responding-
party affirmative defence, not an automatic shift of the criminal burden. Model
prosecution-negated justification as a prosecution element instead. Disjunctive legal
routes can be described inside an issue, but the packet must make them clear.

## Review before commitment

Check witness knowledge against access; quotations against document text; timestamps
against clock/timezone assumptions; alternatives against the actual record; both
parties' information allocations; every issue against the correct supplied burden;
juror membership/threshold; and whether a player can make a meaningful decision soon.
Read the case from each side, not just the author truth. Ensure a loss can occur without
invented rescue and a strong question can succeed without artificial resistance.
No target verdict field, hidden success condition or score threshold belongs in a case.

`validate` checks structure and witness foundation fields, not factual coherence or
semantic completeness. After author review, the storage initialiser fixes the case bytes and
creates a clean world; the required isolated-session orchestrator then starts play. Keep the original commitment hash in a separate record/commit
when practical; a same-disk checksum detects drift but is not tamper-proof security.
Existing worlds, fixtures and sessions are never overwritten to produce a new scenario.

## Mandatory coverage rehearsal before commitment

Run `tools/courtroom.py rehearse --case INPUT --out NEW_OUTPUT --config RUNTIME`.
The output contains the sealed case-bound report; never place it in a public bundle.
Use the output case for backend-check/start. Any change to authored content invalidates
its rehearsal. Existing historical examples remain blocked.

Every witness answers the seven foundation areas plus perception, episode sequence,
the basis of each claimed fact, bias/motive, relationships, prior statements and
document exposure. A fifteenth family deliberately asks off-topic questions. Every
family has a root question. The informed examiner generates natural follow-ups;
it receives only this witness's permitted sources and root answers.

`coverage_templates` maps neutral role-template names to all fifteen family IDs from
`tools/courtroom_rehearsal.py`. Each family has `mandatory` (boolean) and `weight`
(integer 0–3). A witness selects its template with `coverage_template`; the default
`balanced` gives every family weight 1, with only off-topic nonmandatory. Mandatory
families need weight at least 1, and the seven foundations remain mandatory. The
required follow-ups per family are twice its weight; optional families may use 0.
All exercised ordinary questions must pass even in a nonmandatory family.

Two independent grader sessions assess every frozen answer using identical permitted
sources, public rules and public setting. Neither receives the other's assessment,
global truth or another witness's packet. Classification and hearing-plausibility
must agree. Disagreements go to a third independent session with exactly the same
frozen input and no access to the first two assessments. Classification and
hearing-plausibility are each decided by majority. To preserve identical context,
the third grader receives the same whole witness answer batch; only primary
disagreements use its vote.

A three-way classification split is an authoring defect. The sealed report returns
`patch_targets` with the exact disputed question, answer and assessments, and
`author_patch_packet(case, witness)` builds the permitted-source handoff for a fresh
pre-play author. That author patches or clarifies a new draft, which must undergo
the complete rehearsal again. No split is silently passed, converted into uncertainty
or resolved by the player reading spoilers. The gate returns the defect for authoring;
it does not automatically run an unbounded author/rehearsal loop.

Reports retain the original two-grader agreement rate and show tiebreaker counts and
three-way splits per witness. Raw assessments remain unchanged. Practice sessions
close and are never reused for play.

Pass threshold remains 100% grounded or authored uncertainty for ordinary answers,
with zero gaps and zero unsupported inventions. Probe classes are separate:

- At least two author-declared `coverage_probes` per witness deliberately target
  unauthored details. These must produce gaps.
- A separate blind examiner generates six plausible probes spanning at least three
  families. It sees only the neutral role-template name/weights and public setting,
  never authored witness fields, documents, answers or the informed examiner's work.
  A hearing-plausible gap is a case defect and blocks commitment.
- Off-topic questions remain a separate diagnostic group. A gap is acceptable only
  when agreed grading or a third-grader majority classifies the question as outside
  plausible hearing coverage. Unsupported invention blocks commitment in every group.

Default depth is 42 ordinary answers, 3 off-topic answers, at least 2 author probes
and 6 blind examiner probes per witness. Reports contain counts by family and probe
class, raw agreement rate, disputes, exact questions/answers, both assessments and
references, and five distinct session handles per witness, with a sixth when a
tiebreaker is needed. Digests bind the complete
case, permitted packets, templates and human rulings. Partial checkpoints survive
backend failures but never pass the gate. Earlier single-grader reports cannot pass.

This is an observed rehearsal threshold, not proof of exhaustive coverage or an
infallible model assessment. Authored facts and report files are trusted local
inputs, not cryptographically attested provider statements. Mock rehearsals are
labelled and cannot authorise live commitment/startup. A failed live exercise is
retained for authoring review and blocks commitment; deepen the original draft
and rehearse it again before any player theory exists.

Human review is an exceptional path for a reviewer who will not play the case. It
uses `coverage-rule --case REPORT_CASE --rulings HUMAN_JSON --out NEW_CASE
--confirm-human-review --reviewer-will-not-play`; no model is called. Each ruling names `witness`, `answer_id`,
`bin`, `refs`, `hearing_plausible`, `reviewer` and `reason`. The new sealed output is
retained even if other disputes or defects still block commitment. Never fabricate
a human ruling or ask a player to inspect sealed witness knowledge. The reviewer
declaration is recorded and digest-bound; the program cannot verify a person's
future intention to play.

## Authored uncertainty is not missing authoring

Each witness declares `uncertainty`, an object keyed by local boundary ID. Each
entry has exactly `owner` (that witness ID), `kind`, `scope`, and `account`.
Kinds are `never_knew`, `cannot_recall`, `approximate`, and `withholds`. The scope
specifies the topic and limits; the account commits what is unavailable, approximate,
or withheld (including any bounded false account). An empty object is an explicit
choice, not permission to improvise uncertainty. `never_authored` is the fifth state:
it produces a gap, not an authored boundary or a witness answer.

When a witness relies on a boundary it supplies sealed `grounding` metadata with
`refs` (permitted source IDs) and `boundaries` (its own boundary IDs). The controller
checks ownership and existence. This is not proof that the prose respects its scope;
coverage assessments and grounding checks inspect that semantic question.
A document's silence is never a personal lack of qualifications, knowledge or memory.

The pause says only that the simulation could not ground an answer. It is a technical
notice to the player, not an in-world hesitation, evasion or credibility cue. Other
courtroom identities receive no interruption event. The human still learns where a
coverage check failed; that unavoidable meta-signal is accepted, never disguised.

## Explicit amended continuation

Strict fixed-case play never silently accepts new historical detail. A player may
explicitly leave that mode using `amend --topic TOPIC --accept-amended-case` while
paused. Without that explicit choice the controller refuses. The original case
bytes/commitment remain unchanged; the event stream records the revised continuation
and a linked revision hash. It is labelled amended, not an unchanged original case.

Optional author-declared `amendment_envelopes` remain supported. Rehearsal also derives
an envelope for every accepted blind-examiner probe gap, without a separate model
call: the exact pre-play probe supplies its topic; its affected witness supplies the
layer/entry and permitted family/boundary source anchors; fixed preservation rules
supply constraints. Generated envelopes and probe provenance are sealed in the report.
Counts distinguish author and rehearsal sources. A patched probe drops out of the
generated set on re-rehearsal. Three-way splits first need authoring repair; they are
not mislabelled as accepted gaps.

An envelope is not a readiness waiver: hearing-plausible gaps still block commitment.
Only diagnostic gaps already allowed by the readiness policy can remain at commitment.
Every usable envelope must be fixed before play. Each topic ID maps to exactly
`target_layer`, `entry`, `topic` (neutral missing-detail scope), `constraints` (nonempty string
list), and `refs` (initial permitted source IDs). These envelopes must contain all
constraints needed to keep a completion consistent with the fixed history. They
must not encode a preferred verdict. Missing envelopes fail closed: the program
does not turn a player's live argument into an author prompt.

Currently `target_layer: "witness"` is supported and `entry` names the witness.
Other layers fail closed until substrate/projector support exists. The selection,
commitment and disclosure pipeline addresses layer/entry; it does not prescribe
how a future substrate layer will project changes to identities.

Three fresh independent author sessions receive identical chosen precommitted topics,
constraints, target layer/entry and referenced sources. The controller does not forward
the live question, gap explanation, transcript, player side, strategy or outcome
preference. Each author supplies one completion and sees no other candidate or earlier
failed attempt. A fresh checker assesses consistency and knowledge allocation for
every candidate, returning pass/fail with reasons only. Any failed candidate rejects
the whole set. Duplicate completions also reject the set. Rejected sets retry with
fresh authors up to runtime `amendments.max_attempts` (default 3, configurable 1–5).
Exhaustion leaves play paused. The controller chooses uniformly using system randomness
only after a whole set passes. Attempt counts, handles, candidates and sealed reasons
are recorded; failed attempts remain in the sealed runtime even without an amendment.
It cannot accept a caller-selected candidate or filter for a desirable outcome.

Before commitment, `amendment_consistency[topic_id]` must explicitly map every witness
ID to the permitted source IDs relevant to that topic. Empty lists mean an explicit
author determination that the witness has no relevant committed account. The target
entry must include every source anchor in the envelope. Missing owners or invalid
references block commitment and amendment; the controller does not pretend that text
search can establish semantic relevance. A generated envelope therefore stays blocked
until its cross-witness scope is authored and the changed draft is re-rehearsed.

The checker receives only those topic-scoped committed accounts and public rules.
This fresh, closed-after-use technical session is the documented exception allowing
cross-witness sealed knowledge. Authors, witnesses, judges, jurors, counsel and player
receive none of these additional excerpts or checker reasons. The global author-truth
field, unrelated private knowledge, live strategy and transcript remain excluded.
The scope's completeness is an authoring responsibility and remains fallible in this
free-text case format; the future shared substrate can replace this manual index.

Only the selected addition enters the named witness's knowledge. All candidates
and selection/check evidence remain in sealed runtime/journal state; public notices
show revision linkage, not their content. The revised case undergoes the full
coverage rehearsal again before application. Failed rehearsal leaves play paused.
Affected contexts rebuild; pending decisions, ballots and verdicts are reopened.
Old transcript wording is preserved, never rewritten as if the amended case had
always been the original.

Residual limitations: a candidate set can still be skewed. Selecting a topic reveals
the direction of inquiry even without the live question. Consistency and coverage
checkers are fallible. An insufficient constraint envelope is an authoring defect,
not proof of outcome neutrality. This workflow does not claim to make mid-case
historical changes equivalent to an originally complete fixed case.
