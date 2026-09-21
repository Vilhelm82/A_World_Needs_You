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

`validate` checks schema only. After author review, the storage initialiser fixes the case bytes and
creates a clean world; the required isolated-session orchestrator then starts play. Keep the original commitment hash in a separate record/commit
when practical; a same-disk checksum detects drift but is not tamper-proof security.
Existing worlds, fixtures and sessions are never overwritten to produce a new scenario.
