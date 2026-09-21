# Courtroom v2: executed checks and limits

Build date: 21 September 2026.
Base for installation: trial/courtroom-v1 at 8455080a5fc8eda5c3ad360fa1f5e10b32b7a0ca.
Paused controller recovered from Git blob 2149253cee3714e386dd958a66059a8f6f4507fc.

## Actually executed in this build

Python 3.13.5 on Linux; standard library only.

`python3 -m unittest discover -s tests -v` in the isolated v2 build:
**96 v2 test methods passed.** One method exercises 48 civil/criminal, bench/jury,
style, party and pacing combinations. Another exercises both complete starters in
both forums, on either side, under both standard styles. Those are matrix checks,
not 48 independent live-model trials or extra test methods added to the count.

Executed CLI checks include validation, initialisation, verification, packet export,
new-case scaffolding and restart recovery. Regression probes cover timely flow
objections, strict pre-answer gates, no reference to an unanswered question,
private counsel strategy, juror ballots and deliberation privacy, unpublished and
excluded exhibits, limited uses, absent-jury testimony, exact wording, atomic event
batch rejection, stale writer/lock rejection, tampering, explicit error repair,
case-only unsealing, per-count mixed/hung results, and record-only decision snapshots.

The saved draft was corrected to avoid leaking the counsel brief to jurors,
unpublished exhibits to jurors, and pending answers to absent witnesses. Jury
ballots cannot be returned by counsel or the judge. A first split ballot cannot
silently become a completed deadlock. Admission and publication are distinct.

## Installer verification

**11 installer tests passed** in disposable local repositories. These include a
successful application that really ran all 96 v2 tests and made a local Git commit,
rollback after an intentionally failing test, no-tests rejection, dirty/wrong-base/
wrong-branch refusal, symlink protection, payload checksums, source extraction and
refusal to push to an unexpected origin. This was not the user's actual checkout;
no real remote push was performed in these installer tests.

## Not executed or claimed

The supplied archive was installed locally at commit 06bfee8. At that point all
143 tests passed (96 v2 and 47 v1). The user confirmed that v1 had never been played
and was a rejected prototype, so the v1 controller, fixtures, tests and routing
have since been removed. The maintained suite now contains 96 v2 tests.

No full live-model hearing, independent multi-agent trial, human legal review,
calibrated jury simulation or entertainment user test has been completed. The
controller validates packet structure and references, not the semantic truth of a
quotation or inference. A shared context is not hard access separation. It cannot
prevent an operator with full write access from altering files and all their hashes.

New cases are authored by the host agent, not by an embedded network service. The
two starters are complete examples; a new-case scaffold intentionally fails
validation until authored. Real-world court-system fidelity is not asserted.

## Local-first delivery

The archive was applied to the user's local checkout, committed there, and pushed
using existing Git authentication. Subsequent changes follow the same workflow.
`BUILD-MANIFEST.json` describes the current maintained payload; the original source
archive retains the original build checksums. Non-court worlds are unchanged.
