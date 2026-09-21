# Authoring V2: schema proposal and validator plan

Status: implemented schema. The proposal and validator plan were delivered before runtime changes.

## Representation

Keep controller `schema: 2`; add mandatory `authoring_version: 2` for new live
commitments. Historical readers remain available; old cases are not migrated in
place. The four sealed `substrate` maps are always declared, with `{}` meaning
empty. Entry IDs are stable. Times are integer ticks in a case-declared `time_scale`.
This is an explicit observation model, not a geometric or legal simulation.

- `space[id]`: `name`, `adjacent` (location IDs), `distances` (location to distance),
  `sightlines` (visible location IDs), `lighting` (`clear`, `dim`, `dark`), `access`
  (identity IDs). Positions must be authorised. A visible event needs a sightline
  and non-dark lighting; an audible event needs the declared distance to be within
  its `audible_range`. Same-location distance is zero. Dim light can be narrowed
  further by a perception limit.
- `time[id]`: `at`, `location`, `actors`, `audible_range`, `facts`. Each fact has a
  local ID and `{text, channel}`, where channel is `visual`, `audible`, or `actor`.
  Actor facts cover the actor's own conduct or personal history, not automatic
  knowledge of everything anyone else did. Historical positions are intervals
  `{location, start, end}` on each identity, with no conflicting overlap.
- `records[id]`: `title`, exact `text`, `author`, `date`, `recipients`, `received_by`,
  sealed `provenance`, sealed `alterations`, public `display_provenance`, initial
  `status` and `uses`. Actual receipt, not intended delivery alone, grants content.
  Provenance/alteration knowledge must separately be earned through time facts;
  receiving a record never reveals these sealed fields. `documents` is a checked,
  generated compatibility view of the public exhibit fields, not a second source.
- `flows[id]`: `kind` (money/goods/data/custody), `from`, `to`, `at` (time entry ID),
  `records` (record IDs), `description`. Parties know their transfer; observers
  learn only what the linked event's visible/audible facts disclose. Receipt of a
  referenced document does not automatically grant the truth of a transfer.

References address permitted facets, e.g. `time:E1:loading`, `records:R1:content`,
`space:S1:layout`, `flows:F1:transfer`. An envelope contains these references and
their projected text, never the complete sealed entries or a catalogue of hidden
entries. Every role has positions and the authored layers below. Bench/jurors have
empty historical projections; their knowledge arrives through courtroom routing.

## Identity layers

- `template`: one of the seven module-owned witness templates; cases cannot change
  template weights. All fifteen question families remain represented. The template
  also fixes required routine domains.
- `routine`: local step ID to `{domain, description, tools, sequence, usual_choices}`.
  Domains include occupation, qualifications, observation, authority, reporting,
  relationships, custody and analysis. Explicit absence is authored in the text;
  missing fields never mean absence. Routine is usual practice, not proof that an
  episode step happened. `deltas`: local ID to `{step, event, description}` records
  departures and must cite an owned routine step and perceived event.
- `perception_limits`: local ID to `{refs, kind, account}`. References must belong to
  the computed envelope; kinds retain never-knew, cannot-recall, approximate and
  withholding distinctions. Limited raw facets are removed from the delivered
  knowledge. The retained account and boundary are citable instead.
- `account`: facet reference to intended statement. Matching derived text needs no
  exception. Each difference requires `divergences[ref] = {reason, account}`, using
  the six specified reasons. A divergence cannot grant an unperceived secret.
- `pressure_points`: local ID to `{description, case_linked}`. At least one innocent
  point per identity; each side must include an affiliated witness with an authored
  `fallibility` (`error` or `bias`, plus scope). This does not force a lie or verdict.
  `manner` describes expression of pressure without truth-based switches.
- `affiliation`: a configured party or `neutral`. Fairness uses this declared role
  relationship, never the player's preferred result.

Outside-envelope ignorance is one controller-generated, owned perception boundary.
It means no personal basis in this projection. It cannot justify denial of an
event, missing qualifications, or failure to remember the person's own authored
activities. A missing ordinary foundation still fails rehearsal. No list of hidden
facts is delivered with this boundary.

## Grounding and readiness

Every V2 witness answer supplies sealed `grounding.refs` and `grounding.boundaries`.
Refs must resolve to a delivered substrate facet, perception limit, routine step,
delta, divergence, or heard event. Boundary refs are owned by that witness.
Unsupported citations are recorded as a grounding fault, never spoken testimony.
Rehearsal retains invalid citations as an invention defect even if model graders
are lenient. Authored uncertainty needs a perception-limit or routine citation.

Two graders see identical frozen input and permitted sources; disagreement invokes
the independent third grader. Existing thresholds, split handling, nonplaying
human exception, digest binding and mock/live distinction remain. Blind probes now
cover every template family. Informed follow-ups explicitly target visible facets
and routine steps. Ordinary answers drawing on fewer than three source layers
produce a sealed author-review flag; this diagnostic does not change the threshold.

Issues declare `substrate_refs` and optionally a reasoned `single_source` exception.
A sole unshared anchor fails without that declaration. The packet strips these
sealed anchors. Shared-event agreement is structural: all views derive from the
same facet; any different account requires a limit or reasoned divergence. Models
and authors can still misunderstand text; deterministic validation does not prove
semantic truth or prevent every inference from public clues.

## Amendments

Keep precommitted envelopes, independent authors, whole-set rejection, bounded
retries, random selection, linked commitments and reopened decisions. Add substrate
targets `space`, `time`, `records`, `flows`. A candidate is an additive entry patch;
it cannot overwrite an existing historical field. Account/divergence updates are
allowed only when explicitly bound to the amended entry. Witness-only patches are
restricted to routine, pressure points and manner, never freehand knowledge.

The checker scope is derived from shared entry references and all affected
projections, replacing the hand-authored consistency map. It receives the targeted
sealed entry and topic-linked accounts as the documented technical exception. The
author receives only precommitted constraints and source excerpts. Recompute all
projections after a patch, including newly eligible or newly excluded identities;
changed session packets rebuild independently. Rehearse the resulting draft again.

## Validator and test order

1. Schema and references: all stores declared, safe IDs, actors/positions/access,
   record delivery, flow links, valid clocks and routine domains. Reject freehand
   `knowledge` and legacy authoring fields in V2. Verify generated exhibit caches.
2. Projector canaries: separate observers, dark rooms, distant sounds, undelivered
   records, hidden alterations, private flows, narrowed memories and judge/juror
   emptiness. Raw substrate and sealed issue anchors must never appear in packets.
3. Identity/fairness: owned limits and citations, routine vs episode distinction,
   explained divergences, innocent pressures, both-side fallibility, shared anchors.
4. Runtime/rehearsal: mandatory citations, invalid-citation defect despite grader
   votes, uncertainty ownership, per-template probes, layer counts, majority and
   splits, restart and packet invalidation. Preserve all existing controller tests.
5. Amendment tests: every layer, cross-identity scope, no historical overwrite,
   forbidden witness knowledge patch, fresh contexts, linked receipts and rebuilds.
6. Full deterministic suite, full diff/security review, protected-case hashes.
7. Fresh-context author receives only this schema/specification, case configuration
   and the existing public setting. It writes a new V2 draft, not an in-place repair.
   Run a real isolated rehearsal, retain failed exercises, and report counts without
   exposing the case. The old five inventions remain historical failures, never
   relabelled as passing results. Their coverage failure modes are exercised anew;
   old private answers are not passed to the fresh author.

The pause/check meta-signal remains disclosed. Referees and graders are fallible;
the principal defence is authored depth plus separate contexts and checked routing.
