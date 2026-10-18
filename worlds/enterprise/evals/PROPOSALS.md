# Proposals

Pending changes to the harness, from evaluation. Rule on each between watches with `// approve P-NNN`, `// reject P-NNN` or `// approve P-NNN with <changes>`. These numbers are not the world's precedent ids, which also start with P-.

## From the watch 001 audit

| ID | Status | Targets | Change | Files | Baseline |
|---|---|---|---|---|---|
| P-001 | pending | G4/player_address_share (measurement), G10 self-report | `addressed` gets exactly one entry per utterance in `speakers` (an id, `room` or `nobody`), so the two always total the same; the validator rejects a mismatch; address share is counted over crew-addressed utterances only. | tools/wk.py, modules/tng-d/STATE.md | 0.785 reported; 10 of 11 sampled TURNs disagreed with the transcript |
| P-002 | pending | G4/neglected_windows down | Split TURN `present` into `present` (in the room) and `on_channel` (combadge or message voices), and compute neglect only over `present`. Add `wk.py balance`, which prints each present officer's speaking share over the last 9 turns; run it in the Ground step whenever two or more crew are present. | tools/wk.py, modules/tng-d/style.md | 45 windows |
| P-003 | pending | G4 ensemble, G5/npc_initiative | In any 10 turns with two or more crew present, at least one exchange between crew about their own agenda, not addressed to the character, where the scene allows. Logged as TURN `agenda_beats`. | modules/tng-d/style.md | none |
| P-004 | pending | G5/autonomy (reliability) | A MOVED with cause `npc:<id>` must cite an agenda item or a world cause. A move the player asked for is cause `player`, with `requested_at` pointing to the request. The validator rejects an npc cause with no agenda reference. | tools/wk.py, modules/tng-d/STATE.md | 0.542 reported; about 0.44 when relabelled |
| P-005 | pending | G3 regard economies | A REGARD ledger entry whenever someone gives from their gives_rarely list, naming the witnessed cause. A `rare_regard_spend` metric per person per watch. The Check step warns on a second rare spend in one watch with no CHANGED entry. | modules/tng-d/STATE.md, tools/wk.py, modules/eval/GOALS.md | Picard and MacDougal, multiple rare spends on day one |
| P-006 | pending | G6, G10 (disk before page) | Compression rule: when the player compresses a written artefact, its content is only what the player stated. Before anyone in the world reads, quotes or judges it, the GM asks in one `//` line for the text or its gist, and writes it as a fact before the telling. | CLAUDE.md (Compression), modules/tng-d/style.md | T46 |
| P-007 | pending | G2 escapes down | Record `ship_time` on every TURN. The validator checks each TURN's stardate against the watch's opening stardate and time at the clock rate (1000/365.25 a day), within a tolerance, and clock.json at checkpoint. It also recomputes any message delay told against the comms precedent. | tools/wk.py | the clock drifted about 0.34 units by 20:58 |

## From the lore re-audit (due: 19 precedents)

| ID | Status | Targets | Change | Files | Baseline |
|---|---|---|---|---|---|
| P-008 | pending | G1 | Superseding M-002: driver coils recast in M-011's terms (a P1 geometry gradient the hull falls along), with momentum and energy bookkeeping stated. Drops the claim that dampers reduce inertia. | modules/tng-d/canon/mechanisms.jsonl | M-002 conflicts with M-011 (shared P1) |
| P-009 | pending | G1 | Refining world precedent P-011: there is no yeoman billet in 2364. The computer keeps the captain's appointments, and requests go to him directly or through the first officer. The crewman who answered at T13 becomes a bridge support crewman. | worlds/enterprise state (precedent) | P-011 imports a TOS billet |
| P-010 | pending | G1 | Superseding M-016: the dose budgets divide by water's density (1000), not 70. That gives about 3.4e-3 Gy and 84 Gy, and "about one CT scan's worth". | canon/mechanisms.jsonl | both doses overstated about 14x |
| P-011 | pending | G1 | Superseding M-017: cite "saucer sublight only" to later canon, and record the Farpoint saucer reaching Deneb IV after a separation at warp as a canon contradiction, with a physics reading (a decaying residual field) or a noted choice. | canon/mechanisms.jsonl | uncited contradiction |
| P-012 | pending | G1 | Superseding M-001: the on-screen figures (9.3 red line, 9.5 reached, 9.8 at extreme risk), with 9.6 for 12 hours marked as manual-only. | canon/mechanisms.jsonl | misattribution |
| P-013 | pending | G1 | law.md: "the chief engineer hadn't come aboard before Farpoint" becomes [assumed]. Superseding K-032: no chief engineer appears at Farpoint; season one shows several, more than one at a time. | modules/tng-d/law.md, canon/cards.jsonl | tagged [canon] without an episode |
| P-014 | pending | G1 | Superseding K-043 and refining world precedent P-003: Pulaski said the Enterprise's sickbay was fully capable of the 2365 surgery, and Picard chose a starbase for his own image. | canon/cards.jsonl, world precedent | reason drifts from canon |
| P-015 | pending | G1 | law.md "four closed postulates" becomes "the closed postulates in physics.md" (five). | modules/tng-d/law.md | law.md and physics.md disagree |

## From the GM's own run of the loop

| ID | Status | Targets | Change | Files | Baseline |
|---|---|---|---|---|---|
| P-016 | pending | G10 (the loop must run) | wk.py reads and writes every text file as UTF-8 explicitly (`encoding="utf-8"`). On this Windows machine `report` crashed on cp1252 and had to be run with PYTHONUTF8=1. | tools/wk.py | report crash |
| P-017 | pending | G1 (rolls auditable) | A ROLL records the shell command and its raw output, so anyone can check that real dice were rolled. | modules/tng-d/STATE.md, tools/wk.py | 3 rolls with no provenance |
| P-018 | pending | G3, G6 (Will's notes) | style.md "What the world never does": no character undersells canon technology to create a problem (Data doubting the computer can tell a padd from a person), and characters attribute decisions to whoever made them (MacDougal's "you asked for forty"). | modules/tng-d/style.md | Will's notes, watch 001 |
