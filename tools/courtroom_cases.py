#!/usr/bin/env python3
"""Build starter or new-case scaffolds BEFORE play; never alter a live world's case.

No language model is called here. A scaffold remains draft until a host agent has
written a complete new situation. Starter scenarios are fixed, spoiler-bearing
examples, not the only cases the courtroom engine supports.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import courtroom_v2 as court

RULES = {
    "R1": "Simulation: criminal offence elements are for the prosecution to prove beyond reasonable doubt. Silence, declining to testify and failure to prove innocence do not establish guilt. Civil claim elements are for the claimant on the balance of probabilities. A supplied affirmative defence states its own burden; never invent one.",
    "R2": "Simulation: decide only the material elements of each charge/claim. Distinguish an observation from its proposed interpretation. Consider circumstantial evidence together without double-counting correlated observations. Neither a smoking gun nor a confession is required.",
    "R3": "Simulation: relevance and a disclosed foundation are required. Witnesses may describe what they perceived, their genuine memory limits, and identified records. Counsel's questions, opening forecasts and submissions are not themselves evidence.",
    "R4": "Simulation: leading questions are normally allowed in cross-examination. The judge may disallow compound, misleading, repetitious, abusive or unsupported-premise questions. Plain-English objections work. A witness may qualify an answer that would otherwise be misleading.",
    "R5": "Simulation: documents may be admitted for truth or a stated limited purpose (notice, context, credibility). Marking, disclosure or publication alone cannot prove a proposition. Authentication not actually disputed may be compressed. Genuinely contested foundation is played.",
    "R6": "Simulation: a prior inconsistent statement can challenge credibility once fairly put to its maker. Hearsay offered for truth needs a disclosed case-specific exception or agreement; otherwise limit its use. This deliberately short rulebook is not a complete real evidence code.",
    "R7": "Simulation: openings forecast; closing addresses argue from the established record. Both sides may make concise submissions and reasonable replies at the judge's invitation. No new facts appear because a party needs a rescue.",
    "R8": "Simulation: bench mode gives the judge the facts decision. Jury mode gives the judge law/admissibility and gives the jury the facts decision under written directions. The seated jury receives only evidence placed before it, not private strategy or sidebar material.",
    "R9": "Simulation: the case's jury size and agreement threshold are fixed before hearing. Jurors deliberate separately from counsel, may ask questions through the judge, and may genuinely deadlock. Apply agreement separately to each charge/claim. A split first ballot is not automatically a completed deadlock.",
    "R10": "Simulation: timely objection in flow mode may be made on the next player turn and is treated as made before the provisional answer. A sustained objection strikes that answer from decision packets. Strict mode pauses before the answer. Neither mechanism supplies the player's strategy.",
    "R11": "Simulation: routine scheduling, filing, jury empanelment, uncontested foundation and waiting are offstage. Play a procedural question when it changes evidence, rights or the next strategic choice. No clerical tax for entertainment.",
    "R12": "Simulation: an engine mistake is corrected openly, never turned into a witness lie. A material authoring gap pauses the affected issue. Do not invent decisive historical facts during play. Disclose any real-law research additions equally and before reliance.",
}


def profile(style: str, kind: str, forum: str, size: int, threshold: int) -> tuple[str, str]:
    label = {"us-drama": "State of Bellwether (fictional US-inspired court)",
             "nsw-drama": "Harbour District (fictional NSW-inspired court)",
             "custom": "Fictional common-law court"}[style]
    title = "District Attorney" if style == "us-drama" else "Crown prosecutor" if style == "nsw-drama" else "Prosecutor"
    proof = "prosecution must establish each offence element beyond reasonable doubt" if kind == "criminal" else "claimant must establish each claim element on the balance of probabilities"
    decision = f"A panel of {size} jurors decides the facts; {threshold} agreeing votes are required for each charge/claim's outcome. This agreement arrangement is an explicit game stipulation, not a universal rule of any jurisdiction." if forum == "jury" else "The judge decides the facts and gives concise, record-grounded reasons. No jury is simulated."
    procedure = f"# Supplied court procedure\n\n{label}. This is a fictionalised roleplay profile, not actual state/federal/NSW procedure.\n\nAddress the judge as Your Honour or Your Honor. The criminal initiating advocate is called {title}; civil parties remain claimant and respondent. {proof.capitalize()}. Do not translate a burden into a made-up probability percentage.\n\n{decision}\n\nStart with the client conference or go directly to opening when the player requests it. The bundle is exchanged; ordinary paperwork and empanelment happened offstage. Use opening, examination and cross-examination, contested rulings, closing, directions if a jury, and decision. Recesses compress waiting. Do not require formulaic passes or greetings. The player may ask to slow down.\n\n"
    procedure += "\n\n".join(f"## {k}\n\n{v}" for k, v in RULES.items())
    authorities = "# Authority and design sources\n\nEvery operative R rule and every starter offence/claim in this case is a SIMULATION SIMPLIFICATION or CASE STIPULATION. No invented section number or case citation is asserted. Actual sources were checked 21 September 2026 for the comparative architecture, not as an assertion that these short rules implement real law.\n\n- U.S. District Court, Southern District of New York, The Eight Stages of Trial: https://nysd.uscourts.gov/jurors/the-eight-stages-of-trial\n- U.S. Courts, Differences Between Opening Statements and Closing Arguments: https://www.uscourts.gov/about-federal-courts/educational-resources/about-educational-outreach/activity-resources/differences-between-opening-statements-closing-arguments\n- NSW Courts and Tribunals, Criminal hearings and trials: https://courts.nsw.gov.au/resources/criminal-hearings-and-trials.html\n- Judicial Commission of NSW, The Jury: https://www.judcom.nsw.gov.au/publications/benchbks/criminal/the_jury.html\n\nThe choice of US-inspired presentation as the entertainment default is a design choice, not a finding that NSW lacks cross-examination, jury addresses, bench criminal trials or dramatic stakes. See docs/courtroom-reference-model.md.\n"
    return procedure, authorities


def configure(source: dict, style: str = "us-drama", forum: str = "jury", side: str | None = None,
              pace: str = "drama", size: int | None = None, threshold: int | None = None) -> dict:
    case = deepcopy(source)
    kind = case["config"]["case_type"]
    side = side or ("defence" if kind == "criminal" else "respondent")
    court.require(style in court.STYLES and forum in {"bench", "jury"} and side in court.SIDES[kind], "Invalid profile/side/forum.")
    court.require(pace in {"drama", "deliberate"}, "Invalid pace.")
    case["roles"] = {r: p for r, p in case["roles"].items() if p["kind"] != "juror"}
    old_side = case["config"]["player_side"]
    if side != old_side:
        case["roles"]["player"], case["roles"]["opponent"] = case["roles"]["opponent"], case["roles"]["player"]
        case["opening"] = "Your instructing lawyer lays the exchanged bundle on the table. 'Before we go in, what do you need from me?'"
    case["roles"]["player"]["name"] = "Will (counsel)"
    case["roles"]["opponent"]["name"] = "Alex Vale (opposing counsel)"
    if forum == "jury":
        size = 12 if size is None else size
        threshold = size if threshold is None else threshold
        court.require(type(size) is int and 2 <= size <= 24 and type(threshold) is int and size / 2 < threshold <= size, "Invalid jury size/threshold.")
        manners = ["Separates what was seen from what was inferred; can revise when the record warrants it.",
                   "Attends carefully to chronology; treats confident delivery as no substitute for a source.",
                   "Asks which facts are common ground; considers cumulative evidence rather than isolated fragments.",
                   "Checks whether an alternative explains the whole record, without inventing missing facts."]
        for n in range(1, size + 1):
            case["roles"][f"J{n:02d}"] = {"name": f"Juror {n}", "kind": "juror", "knowledge": [], "documents": [], "manner": manners[(n-1) % len(manners)]}
    else:
        size, threshold = 0, 0
    case["config"].update({"style": style, "jurisdiction": {"us-drama": "Fictional Bellwether, US-inspired", "nsw-drama": "Fictional Harbour District, NSW-inspired", "custom": "Fictional custom jurisdiction"}[style],
                           "factfinder": forum, "player_side": side, "pace": pace, "jury_size": size, "verdict_threshold": threshold})
    case["procedure"], case["authorities"] = profile(style, kind, forum, size, threshold)
    case["rules"] = deepcopy(RULES)
    return case


def witness_scaffold(name: str) -> dict:
    """Author-owned placeholders, never manufactured biography or case facts."""
    return {'name': name, 'kind': 'witness', 'documents': [],
            'knowledge': ['REPLACE: fixed personal observations and knowledge, independent of documents.'],
            'knowledge_basis': 'REPLACE: sources of knowledge and their limits.',
            'background': {key: 'REPLACE: ' + key for key in court.WITNESS_BACKGROUND_FIELDS},
            'relevant_activities': [{key: 'REPLACE: ' + key for key in court.WITNESS_ACTIVITY_FIELDS}],
            **{key: 'REPLACE: ' + key for key in ('memory', 'perception_limits', 'motives', 'manner')}}


def skeleton(kind: str) -> dict:
    """Intentionally unplayable until a host authors the material; no false case generator."""
    case = {"schema": 2, "draft": True, "case_id": "new-case", "law_status": "simulation", "title": "AUTHOR A DISTINCT CASE",
            "config": {"case_type": kind, "player_side": "defence" if kind == "criminal" else "respondent"},
            "public_summary": "REPLACE: neutral allegations, no secret truth or preferred inference.",
            "brief": "REPLACE: shared procedural brief; put confidential advice only in allocated role packets.",
            "truth": "REPLACE: fixed material past, provenance, alternative causes and genuinely missing information; no preferred verdict.",
            "opening": "REPLACE: concrete first line from the client's instructing lawyer.",
            "procedure": "Filled by profile.", "authorities": "Filled by profile.", "rules": deepcopy(RULES),
            "roles": {"player": {"name": "Will", "kind": "counsel", "knowledge": [], "documents": []},
                      "opponent": {"name": "Other counsel", "kind": "counsel", "knowledge": [], "documents": []},
                      "bench": {"name": "Judge", "kind": "bench", "knowledge": [], "documents": []},
                      "W1": witness_scaffold('AUTHOR WITNESS NAME')},
            "documents": {}, "issues": {}, "counts": {}}
    return case


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", choices=["last-light", "second-signature", "new"], default="new")
    p.add_argument("--case-type", choices=["civil", "criminal"], default="criminal")
    p.add_argument("--factfinder", choices=["bench", "jury"], default="jury")
    p.add_argument("--style", choices=sorted(court.STYLES), default="us-drama")
    p.add_argument("--player-side", choices=["prosecution", "defence", "claimant", "respondent"])
    p.add_argument("--pace", choices=["drama", "deliberate"], default="drama")
    p.add_argument("--jury-size", type=int)
    p.add_argument("--threshold", type=int)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        court.require(not args.out.exists() and not args.out.is_symlink(), "Output exists; no overwrite.")
        if args.scenario == "new":
            source = skeleton(args.case_type)
        else:
            root = Path(__file__).resolve().parents[1]
            source = court.load(root / "modules/courtroom-v2/.sealed" / f"{args.scenario}.json")
        case = configure(source, args.style, args.factfinder, args.player_side, args.pace, args.jury_size, args.threshold)
        if not case.get("draft"):
            court.validate_readiness(case)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as f:
            json.dump(case, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("Draft scaffold: host must finish authoring before init." if case.get("draft") else "Starter case prepared; initialise once before play.")
        return 0
    except (court.CourtError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Case build error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
