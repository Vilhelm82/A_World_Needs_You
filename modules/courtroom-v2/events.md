# Courtroom v2 event contract

All examples below are structural, not facts to add to a case. Commands run at the
repo root. Event audiences contain role IDs from `case.roles`, not character names.
`engine`, `clerk`, and `foreperson` are actor aliases, not audience IDs.

## Common shape

    {"type":"exchange","actor":"opponent","text":"Exact displayed exchange.",
     "audience":["player","opponent","bench","W1","J01","J02"],
     "data":{"witness":"W1","question":"Did you sign it?","answer":"Yes."}}

Use the complete real jury, not just J01/J02 from this example. Exact question and
answer are authoritative. An omitted/null answer opens pre-answer mode. The helper
assigns T0001-style IDs and digest links; never invent or alter IDs. `--expected N`
rejects stale writers before a batch is committed. A rejected batch appends nothing.
Only `private_note` may contain a sealed controller annotation; do not put one in data.

## Ordinary play

- `dialogue`: private/in-world conference speech; actor is a role, audience is who
  actually hears. Not a substitute for sworn testimony or a court submission.
- `private`: player's or opponent's private planning; exactly one party in audience.
- `phase`: engine, `to`: conference -> preparation (optional) -> opening -> evidence
  -> closing -> decision -> closed. Phase changes cannot skip unresolved exchanges.
  Jurors enter at opening and retire at decision. Directions are needed before retirement.
- `exchange`: player, opponent or bench, with witness, question and answer/null.
  Both counsel, bench and witness hear; include all seated jurors, exclude an absent panel.
- `accept`: the side with the objection opportunity, no data. In flow mode the answer
  becomes usable only after all opportunities close. Moving to a next substantive
  step may supply an implicit acceptance under the disclosed game convention.
- `objection`: side with live opportunity, `rule`: supplied rule ID. Answer held or
  provisional. `reply`: counsel's short response, with rule. No magical incantations.
- `answer`: strict mode's questioned witness only; exact text, same original audience.
- `submission`: counsel, `refs`: list of {id,use}. Always argument, not evidence.
  Opening forecasts have no evidentiary references. A closing quote must refer to
  evidence available to its audience, including jury publication where applicable.
- `stipulation`: bench, `agreed_by:["player","opponent"]`; an actual recorded agreement.
  The program checks form; the model must not fabricate the player's agreement.

## Exhibits and rulings

`disclose` has document ID and `to` role. Recipient hears it. A role can only disclose
what it holds; controller disclosure must follow the fixed case's provenance. Direct
private disclosure to jurors is prohibited. A witness normally needs an explicit
disclosure if the document is not in its initial allocation.

`ruling` is by bench and includes a supplied `rule`:

- effect `objection`, result `sustained|overruled`.
- effect `document`, document ID, status `disclosed|admitted|limited|excluded`, uses
  drawn from `truth|credibility|notice|context`. Offered to the judge first; both sides
  must have it before admission. Disclosed/excluded have no permitted merits uses.
- effect `strike`, target exchange or stipulation ID, removes it from merits.
- effect `procedure`, exact public order in text.

`publish` has document ID. The item must already be admitted/limited, and must go to
the seated panel in jury mode. Admission in a sidebar does not itself publish it.
Changing admission status removes publication until the currently permitted version
is republished. The helper does not semantically rewrite quotes embedded in other
accepted testimony; flag and strike or correct any affected dependent material openly.

## Jury

- `jury_presence`: bench, `present:true|false`, no pending exchange.
- `directions`: bench, supplied rule, delivered to all jurors. Clears previous ballots.
- `jury_question`: foreperson, both counsel/bench/all jurors, optional record refs.
- `deliberation`: juror actor, audience exactly the whole jury, refs. Never public.
- `ballot`: juror actor, audience exactly that juror, `findings` keyed by every issue.
- `deadlock`: foreperson publicly identifies precisely the unresolved `counts`,
  after attempted deliberation and all ballots. A later ballot clears the report.
- `verdict`: foreperson, only `outcomes` by count. Program checks aggregation. A hung
  count requires the deadlock step; there is no forced convergence or default winner.

Each finding has `status:proved|not_proved`, concise fictional `reason`, and `refs`.
A proved finding requires references of form `{"id":"E01","use":"truth"}` or an
accepted exchange/stipulation ID. A merits packet does not turn argument into proof.
The helper validates availability/use, not that the cited words logically prove it.

## Bench decision and optional remedy

`verdict` by bench includes `findings` keyed by every issue and `outcomes` keyed by
count/claim. Criminal outcomes are guilty/not_guilty; civil liable/not_liable. A count
is positive only when all its elements are proved and no expressly allocated affirmative-
defence bar is proved. This preserves separate burdens; it is not a real-law compiler.

A civil bench verdict may include `awards:{"C1":1200}` when that claim defines a remedy
currency and maximum. No damages without liability. Jury damages are left to a supplied
narrative/stipulated aftermath, not silently selected by the foreperson in v2.

## Persistence, repair, pace

`checkpoint` is engine, optional `scene` object for exact resume details. `cadence`
is engine, `mode:flow|strict`, between resolved exchanges. No changed fact or burden.

`erratum` is engine, existing target ID and exact replacement; reaches original
recipients. Original stays in transcript but cannot be used as evidence. If correcting
a strict answer, its parent exchange is also invalidated. Dependent allegations or
submissions must be checked and corrected too; software cannot infer all dependencies.

`gap` is engine with detail; stops live play until resolved openly. `repair` reopens
evidence and clears directions/decisions; it is not permission to rewrite history.
Use it only after restoring the affected opportunity or agreeing an explicit practice
arrangement. Immutable case error means a disclosed restart, not editing a live seal.

`unseal` requires closure, player-only audience and `confirmed:true`. The user must
actually have confirmed after a spoiler warning. It exports only this case.
