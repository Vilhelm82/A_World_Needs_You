# Courtroom v2: start here

A general court-roleplay module for Worldkeeper. Civil **and** criminal cases.
Bench **and** jury trials. Either side. New original scenarios or two ready examples.
Routine administration stays offstage; consequential advocacy stays yours.

## Start in a fresh file-backed agent session at this repository root

> Begin courtroom. Criminal jury trial, US-inspired. I am defence counsel. Keep the pace sharp.

For a new case the agent builds and commits the material before play. It is not
forced to reuse the old civil scenario. More examples of accepted setup requests:

> New criminal bench case. I am the prosecutor. NSW-inspired, without procedural busywork.

> A civil jury dispute about a disputed invention. I represent the claimant.

> Use the Last Light starter case as a criminal jury trial. I am defence counsel.

> Use the Second Signature starter as a civil bench case, NSW-inspired.

Case type, factfinder, side, style and pace are independent. An existing named world
resumes; a new case gets a new folder. Default is fictional US-inspired criminal
jury defence with drama pacing. The stock profiles are game adaptations, not full
US state/federal or NSW law. The case tells you the rules that matter.

## What play includes

Client conferences, actual evidence to inspect, distinct bounded witnesses, capable
opposing counsel, opening and closing addresses, fair objections, evidence rulings,
judge-decided findings or jury deliberation with possible mixed/hung outcomes. A
world continues through earned consequences instead of resetting everyone after a
hearing. That does not require simulating court scheduling or filling in forms.

In flow mode an opponent's question and one provisional answer can arrive together.
Object on your next turn; the objection counts before that answer. No need to type
"pass" after every ordinary question. Ask for strict mode to pause before answers.

`// procedure` gives the supplied rule, not the winning strategy. `// record` retrieves
exact material. `// prepare` is private. `// pause` or `stand down` saves. After closure,
`// debrief` reviews actual decisions without opening the hidden truth. `// unseal`
requires a spoiler warning and confirmation. Later replay is then informed practice.

## Tools and limits

Python 3.10+ and a file/shell-capable agent are required. Standard library only;
no API key, new service or model subscription is installed by the controller.

    python3 -m unittest discover -s tests -v

The case builder can create a draft scaffold (`--scenario new`) or prepare a complete
starter. It is not an autonomous LLM case generator; the host agent authors new case
content according to `modules/courtroom-v2/authoring.md`. Agent flow and exact command
contracts are in `modules/courtroom-v2.md` and its `events.md` companion.

Courtroom v2 is the sole court engine, using `tools/courtroom_v2.py` and its own
case/journal layout. The rejected v1 prototype has been removed. Non-court world
files and the original Worldkeeper base harness remain unchanged.

The program tests record mechanics, not whether a generated judge is legally sound
or a roleplay is engaging. Single-context role separation is not hard isolation;
separate-context helpers are used only where your agent actually supplies them.
There is no predetermined verdict, hidden talent score or guarantee of dramatic reversal.
Detailed jury damages, sentencing, jury selection and appeals are not separate v2
engines; they are optional abbreviated aftermath unless independently specified.

Read `docs/courtroom-reference-model.md` for the US/NSW entertainment rationale and
`docs/courtroom-v2-validation.md` for exactly what was executed.
