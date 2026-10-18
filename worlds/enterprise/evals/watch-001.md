# Watch 001 — evaluation

World: enterprise · harness `ad8cf32` · turns: 90

| Goal | Verdict | Metrics (target) | Audit | Player |
|---|---|---|---|---|
| G1 | met | objections_upheld 0 (<=0); lore_checked_rate 1.0 (>=1.0) | 3 | — |
| G2 | missed | — | 2 | — |
| G3 | missed | — | 2 | — |
| G4 | missed | player_address_share 0.785 (<=0.35); neglected_windows 45 (<=0) | 1 | — |
| G5 | missed | autonomy 0.542 (>=0.5); npc_initiative 0.578 (>=0.3); decided_without_player 3 (>=1) | 2 | — |
| G6 | missed | — | 2 | — |
| G7 | met | cases_isolated None (>=1.0); pool_ignored None (<=0) | 3 | — |
| G8 | met | canon_distance_checked 1.0 (>=1.0) | 3 | — |
| G9 | met | — | 4 | — |
| G10 | missed | parity 1.0 (>=1.0); dirty_at_eval 0 (<=0) | 2 | — |
| G11 | met | fork_bleed 0 (<=0) | no data | — |

Other: attempts {'cost': 1, 'denied': 0, 'done': 3} · objections {'consistent': 0, 'contradicts': 0, 'diverged': 0, 'unsupported': 0} · precedents added 19 · validator rejections 0 · hook installed True
Neglected in at least one 10-turn window: crusher, data, laforge, macdougal, troi, yar

## Self-report check
Checked 11 TURN entries against the transcript: 10 disagreements.

## Findings
- **G1** minor (turn 29): Picard is described leaving the observation lounge by a door that opens straight onto the ready room ('the door already open on the ready room', 'the ready room doors close behind him'). The Enterprise-D's lounge has no such door. The account given outside (he crossed the bridge) doesn't fit the text as told.
- **G1** minor (turn 90): La Forge, a lieutenant junior grade in 2364 (voices.md), is written as 'Lt. La Forge' in Yar's formal protocol and as 'Lieutenant La Forge' in Picard's log. Yar's own incident log uses 'Lt. (j.g.)' for others.
- **G1** minor (turn 8): La Forge says he had been aboard 'about an hour' at the Deneb IV appearances. That is looser than canon, which has him boarding at Farpoint well before them. The GM flagged it in its own audit but logged no LORECHECK or precedent for the idiom.
- **G1** minor (turn 7): The three ROLL entries on U-001 record outcomes, roll and result, but not the shell command or raw output, so nobody can check that real dice were rolled. All three landed on one of the more striking outcomes.
- **G2** major (turn 70): The clock contradicts its own rate. The watch opens at SD 41174.8, 08:10, with a CALC'd rate of 2.738 per day (L23). On that rate, 15:28 is 41175.63, but the player was told 'Fifteen twenty-eight. Stardate 41175.56'. The drift grows over the afternoon: clock.json closes at 41175.92 at 20:58, where the rate gives about 41176.26. The validator never checked TURN stardates against ship time, and the next watch inherits the bad clock.
- **G2** minor (turn 65): Crusher says a message to Hesker IV is 'another hour and a half each way'. The world had fixed it at about forty minutes each way and shortening (T23, P-012), and the reply did come back about 97 minutes after sending, round trip (T76).
- **G2** minor (turn 9): The GM's record says the validator rejected SAID entries at T5 and T9. The validator log shows 98 runs and 0 rejections, so either those runs went unlogged or the claim is wrong, and validator_rejections undercounts the catches either way.
- **G3** major (turn 28): Picard, a rare giver of praise and warmth, tells his first officer on day one, nearly smiling, that he is 'founding a few' traditions and that conceding the point 'will cost you nothing with them. Rather the reverse.' That is a regard verdict, against his card. His log that night adds 'the question was the most useful thing said today', a second rare praise in the same day.
- **G4** major (turn 1): Both G4 metrics miss badly: player_address_share is 0.785 against a target of 0.35 or less, and neglected_windows is 45 against 0, with all six present canon officers neglected at least once. Some of this is measurement noise (see self_report; 'present' mixes people in the room with voices on a channel), but the transcript confirms the shape: outside T6-T12, the T21-T27 briefing and T33-T35, nearly every line is spoken to Lloyd.
- **G4** minor (turn 56): Data reports, unasked, how many messages the counselor's office has had since the XO's note ('I assume that was intended'). The beat exists to show the player his decision landing, and it has Data monitoring the counselor's mail.
- **G5** major (turn 13): MOVED cause labels flatter autonomy. Moves the player asked for are logged as npc:* (Picard booking the slot, Yar writing and sending the protocol, Data sending the Q file, MacDougal sending the recipe). Relabelled, autonomy is 0.44 against the 0.5 target, not the reported 0.542, and TURN 'initiated' lists are padded the same way (T89).
- **G5** minor (turn 72): Off-screen movement is real but thin. The two WORLDTURNs advance Hesker IV (cases, Juuso's council motion and replies) and shipboard logistics, but no crew member's personal agenda advances on its own over the 13 hours, and no force other than Starfleet Command moves.
- **G6** major (turn 46): The GM treated a ship-wide note the player hadn't written as finished, and Troi read it, critiqued it and praised it ('It's good, Will'). The world gave regard for content the GM authored on the character's behalf. Its text (F-070) was supplied by the player only after the telling.
- **G6** minor (turn 81): In the Ten Forward and baking run (T75-T89) every beat lands in the character's favour: the room eases at his answer, an ensign raises a glass, the steward says 'That's not replicated', Troi says 'That's not fair', MacDougal says 'Not flat'. Nothing costs anything. This leans toward the mirror.
- **G6** minor (turn 25): The world's strictness was barely tested. Of 4 ATTEMPTs, 3 are trivially 'done' (baking, sending a file already sent, holding cells) and none is denied. Yar's rebuke at T25 is the watch's only cost to the character.
- **G7** minor (turn 86): The Worf and tribbles exchange, witnessed only by beta-shift bridge crew on duty, reaches Troi in Ten Forward within three hours with no named carrier. The spread is logged only as crowd:bridge-crew, and deeds.json records no act or witness trace.
- **G7** minor (turn 81): deeds.json is empty for the whole watch, though there were notable acts with witnesses and deductions: the unsigned scone box left at MacDougal's console with an ensign watching, and MacDougal working out who left it. The who-finds-out machinery was never exercised.
- **G8** minor (turn 75): An ordinary evening is told at length, with the character's technique written for him ('pat it out an inch thick and cut straight down, no twisting'). Style says ordinary days are told briefly, and the character's actions are the player's.
- **G8** minor (turn 40): Some crowd characters are generic (Petrakis, Haskell, Vasquez, Okonjo), next to a colony whose names and terms (siida, Ealat, Somby, Nango) are properly particular.
- **G10** major (turn 46): Troi read and commented on the text of a document that didn't exist on disk when the turn was told. F-070 was written afterwards from the player's out-of-world text, so the world told first and wrote second.
- **G10** minor (turn 74): There is no turn 74 in the transcript, the ledger or the git history (the commits go from turn 73 to turn 75), and no NOTE explains the gap. Parity holds only because both sides skip it.
- 4 finding(s) withheld: they would reveal sealed truth.
