# Trial branch: Courtroom v1

A playable first hearing for Worldkeeper. This branch adds a court module and a
small standard-library controller; it does not replace your existing worlds.
The original harness is preserved unchanged at `modules/worldkeeper-base.md`.

## Start

In your local clone, fetch and switch to `trial/courtroom-v1`, using a clean
working tree or safely saving your current work first. Start a fresh agent session
at the repository root and say:

**Begin the courtroom trial. I am counsel for the defendant.**

The root harness routes that request, initialises the committed first case under
`worlds/courtroom-trial/`, and opens before the hearing so you can prepare.
No manual unpacking, account, API key or new service is required by the controller.
You still need the file-backed agent you normally use for Worldkeeper.
Python 3.10+ must be available as `python3` (or use `python` on your system).

To initialise/check manually, from the repository root:

```sh
python3 tools/courtroom.py init
python3 tools/courtroom.py verify
```

Initialisation never resets a hearing. An interrupted session resumes from its
files. To recover stale projections after a crash, use `python3 tools/courtroom.py
resume`; this does not rewrite the fixed past. Do not delete a live world to repair it.

## What you are trying

An entirely fictional, NSW-style civil hearing with a client, opposing counsel,
one judge, four material witnesses, ten exhibits and four exchanged statements.
The case and applicable simulation rules are supplied. There is no prescribed
verdict, guaranteed confession or hidden instruction to admire your argument.
Start with the brief and client conference; the documents stay available to read.

Speak normally. `// procedure` requests procedural orientation; `// record`
retrieves what you have seen; `// prepare` stays private. `// pause` or `stand down`
saves the current position. After judgment, `// debrief` reviews the transcript.
A closed case can be unsealed after a spoiler warning and confirmation.

Do not browse `modules/courtroom/.sealed/`, the world's `.world/` or `records/`
during a blind run. Packed material only reduces accidental spoilers; this is not
encryption. Player-readable material is the charter, canon and chronicle, including
your confidential client instructions. A fresh world name replays the SAME first
case, not a new mystery; knowledge of a previous run changes the nature of practice.

## What is implemented and what remains experimental

Implemented: pinned case material, role-specific packets, exact event/transcript
records, objection opportunities, exhibit-use status, record-reference checks,
explicit engine-error handling, restart recovery and case-only unsealing.
The Python tests validate these mechanics. They do not validate generated advocacy,
witness psychology, legal judgment or the model's resistance to persuasion.

The agent still supplies dialogue and rulings. One shared model context is not a
hard information barrier. Fresh-context helpers can consume filtered packets when
your runtime supplies them; this branch does not install a multi-agent service.
All governing first-case rules are disclosed simulation simplifications. This is
not a complete or accredited implementation of NSW law.

## Developer checks

```sh
python3 -m unittest discover -s tests -v
```

Read `tests/courtroom-behaviour.md` for live-model checks and
`docs/courtroom-implementation.md` for implementation notes. Keep acceptance tests
and their artificial transcripts outside your actual hearing. Do not infer a
legal-aptitude score from a win, loss or a passing Python test suite.
