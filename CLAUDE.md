# Worldkeeper: harness router and courtroom amendments

Read `modules/worldkeeper-base.md` as the base harness before running a world.
That file is the original `draft/worldkeeper-v2-initial` harness, preserved byte
for byte. Its relative paths refer to the REPOSITORY ROOT, not `modules/`.
For a non-court world, apply that original harness unchanged.

## Courtroom activation

When asked to begin a courtroom/court trial, use world `courtroom-trial` unless
the person supplies another name. A named world's charter with module `courtroom`
or `resolution: system:courtroom` also activates court mode. Do not accidentally
resume a different recent world when a courtroom was explicitly requested.
Read `modules/courtroom.md` completely before building, resuming or speaking.
The module initialises the already-committed case; do not use the base world's
random setting selection or construct a new mystery from the player's argument.
A repository development request is not a request to start a scene.

## Explicit court-scoped amendments to the base harness

These are root-level exceptions, not a module silently overriding the floor.
They apply ONLY while the courtroom module is active. All other base commitments,
including player ownership, truth-first, no flattery and local knowledge, remain.

1. **Reasoning within knowledge.** Replace 'They do not integrate' in floor 3
   and the restriction on integrated NPC answers in world-behaviour rule 9 for
   opposing counsel and the bench. They may develop complete competing arguments
   from information legitimately available to them. Colleagues do not supply the
   player's strategy without an explicit delegation of that substantive work.
2. **Fixed past and finite cases.** The relevant history, material evidence,
   initial witness knowledge and meaningful information gaps are committed before
   play. Do not apply 'no bottom' by deepening a litigated fact after counsel has
   understood it. A resolved point stays resolved. Future professional consequences
   may develop; new decisive historical facts may not.
3. **Discovery is not guaranteed proof.** Procedural doors stay available, but
   three successful routes to every secret and at least one lying source are not
   required. Some facts cannot be established. Do not add a liar, confession,
   exoneration or clue because the base build rules would otherwise demand one.
4. **Record-based adjudication.** Hidden truth constrains what happened and what
   witnesses can know. The applicable rules, admitted evidence and valid inferences
   determine the judgment. Hidden truth is not itself an input to the bench.
5. **Honest error repair.** Do not explain an engine continuity error by making
   a witness newly mistaken or dishonest. Record an explicit erratum, correct it
   outside the world, and repair the affected opportunity. The erroneous statement
   is not a cross-examination victory. Fixed case material is never rewritten.
6. **Exact contested wording.** Compression can relay specified content, not
   generate successful advocacy. 'I put WS1 paragraph 2 against E04' is an attempt
   with identified material; 'I make her confess' supplies no admission. Preserve
   exact questions, answers, concessions and rulings in the public transcript.
7. **Court persistence protocol.** `tools/courtroom.py` owns the canonical court
   event log and its live-state, card, ledger and transcript projections. Do not
   also edit those files by hand using the base per-turn procedure. Persist before
   telling. Keep sitting records under `records/` as usual, but do not copy hidden
   truth into the public transcript. Save/checkpoint only this world's files;
   do not stage unrelated changes or silently push private sessions to a remote.
8. **Case-level seal.** A closed case may be unsealed after a spoiler warning and
   explicit confirmation. This opens only that case. Later practice with that
   knowledge is informed, not a blind assessment. A live case stays sealed under
   the trial charter; the player can explicitly end it rather than treating a
   hidden-state request as an in-world discovery.

Order of application: this router's scoped amendments, then the courtroom module
and charter, then the unchanged base harness wherever compatible. A charter can
change presentation prospectively, not undo the committed case or lower a burden
to reward an argument. Any requested change that would break a fair hearing is
handled openly as a repair or a separate practice run, never as secret history.
