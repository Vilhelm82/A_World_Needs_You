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
presence; historical record verification still accepts the older structural schema.
The original Last Light and Second Signature examples lack these foundations and
are reference material only, not launch-ready scenarios. Never patch an existing
world's committed case to make it pass the new gate.

If an unanticipated material fact was not authored, the witness returns
`{"text":"","data":{},"authoring_gap":"description of missing fact"}`. The
controller pauses and records a neutral engine notice, never testimony. The
description remains sealed; it must not reveal a private witness fact to the player.
The host must not portray this as evasiveness, hesitation, deceit, lack of credentials
or faulty memory. Resolve only from already committed material, or abandon/rebuild
the case explicitly. Do not use a bare `repair` merely to bypass the missing fact.

For documents settle: author, date, intended audience, provenance, any alteration,
relationship to other sources, who has received it, and initial evidentiary status.
Do not place truth annotations, hidden provenance conclusions or private instructions
in text that will be given to counsel, judge or jury. Store those in `truth` or bounded
role knowledge, not the neutral summary. A common-source anomaly is not independent
corroboration just because five documents reproduce it.

Predefine timeline, relevant physical constraints and what cannot be established.
For an unanticipated question, answer explicit fixed facts or necessary consequences.
Immaterial colour may be invented only if it cannot alter credibility, access, timing
or a contested issue. Otherwise record a gap; do not choose a decisive answer in
response to the player's theory. Unknown is not proof of a favoured explanation.

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
