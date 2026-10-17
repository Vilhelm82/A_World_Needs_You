# Covert play — traces, evidence and who can find what

The ship is a sandbox for anything that's lore-possible: pranks, smuggling, a private experiment, a conspiracy. None of it is blocked. All of it leaves traces, and getting caught is decided by evidence and the people looking at it — never by the GM's sense of what would make a good story.

## Every act leaves typed traces

When the person does something covert, the GM writes what it leaves behind into `state/evidence.json` **before** narrating the act. Each trace has a type, where it sits, who could find it, and how long it lasts.

| Trace type | What leaves it | Who can read it |
|---|---|---|
| `location` | [canon] Combadge location; "Computer, locate…" answers anyone who asks | Anyone, live. History only via a security query (see below). |
| `computer_access` | [assumed] Every query, file access and command, with the authorisation used | Security and the captain, by query. Anyone with that officer's codes. |
| `authorisation` | [assumed] Use of command codes, overrides, lockouts | Logged permanently. An override of a log is itself logged. |
| `transporter` | [assumed] Every transport, its source, destination and operator | The transporter chief; security; the captain. |
| `replicator` | [assumed] Usage records by station and user | Ops and security, by query. Rarely looked at unless someone asks. |
| `door` | [assumed] Entry to restricted areas (armoury, brig, engineering core, computer core) | Security, by query. Ordinary doors are not logged. |
| `sensor` | [canon] Internal sensors: life signs, energy discharges, weapons fire aboard | Live to the bridge if anything trips an alert; otherwise by targeted sweep. |
| `witness` | Anyone who saw, heard or noticed anything | That person, and whoever they tell. |
| `physical` | Objects, residue, damage, a missing component | Whoever looks in the right place. |
| `behavioural` | Absences, lies with holes in them, changes in routine | Anyone who knows the person well enough to notice. |
| `empathic` | [canon] Strong concealed emotion near Counselor Troi | Troi only, as a feeling with no facts attached. |

The [assumed] rows are the harness's best lore-plausible reading of what a Galaxy-class computer records. A `// lore objection` can move any of them; the ruling becomes precedent.

Covering tracks is play: editing a log, wiping a replicator record, getting a witness to stay quiet. Each cover-up is an act with its own traces, often more serious than the original (an `authorisation` trace on a log deletion is evidence of intent).

## Cases

A case opens when someone in the world has a reason to look: a complaint, an alarm, an anomaly someone noticed, a pattern. Not before, and not because the GM thinks it's time.

```json
{"case_id": "C-007", "opened_at": "41187.3", "investigator": "yar",
 "trigger": "replicator reported a contraband synthesis pattern",
 "known": ["T-031"], "hypotheses": ["someone with deck-8 access"],
 "next_step": "query replicator logs for deck 8 over three days",
 "status": "open"}
```

## Investigators are isolated

While a case is open, the investigator's reasoning runs as a **separate agent with a fresh context**, at each world turn that gives them time to work:

1. The GM assembles the investigator's **light cone**: their own soul folder, the case, the traces whose `who_can_read` includes them (or that they have now queried), and statements actually given to them. Nothing else. No truth file, no ledger, no transcript.
2. The agent returns, as JSON: what it concludes, how confident it is, what it does next, and anything it would report to the captain.
3. The GM writes the result to the case as a run (`{watch, turn, isolated: true, cited: [...]}`) and lets the investigator act in the world. The validator rejects any run that cites a trace outside the case's `known` list.

This is how knowledge stays local in a way that can't leak: the investigator *cannot* use what it was never given. The audit checks every conclusion against the light cone it was given.

## Recruiting

Recruiting someone into anything covert is itself an act with a witness: the person you asked. Each crew member decides from their own soul folder — values, loyalties, regard, what they stand to lose. Most Starfleet officers report a mutiny. Some won't, for their own reasons. Troi will sense something is wrong around anyone carrying a secret like that.
