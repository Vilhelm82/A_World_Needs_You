#!/usr/bin/env python3
"""General Worldkeeper courtroom controller, Python 3.10+, standard library only.

Continues the paused v2 draft (Git blob 2149253cee3714e386dd958a66059a8f6f4507fc).
An isolated session per identity supplies dialogue. This module controls records,
information allocations and decision structure, not the truth of legal inference.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

VERSION = "2.0.0"
AREA = Path(".world/court-v2")
PUBLIC = Path("chronicle/court")
CORE = {"player", "opponent", "bench"}
USES = {"truth", "credibility", "notice", "context"}
STYLES = {"us-drama", "nsw-drama", "custom"}
SIDES = {"criminal": {"prosecution", "defence"}, "civil": {"claimant", "respondent"}}
RESERVED = {"engine", "clerk", "foreperson", "jury"}
PHASES = {"conference", "preparation", "opening", "evidence", "closing", "decision", "closed"}
FIELDS = {
    "dialogue": set(), "private": set(), "submission": {"refs"},
    "phase": {"to"}, "exchange": {"witness", "question", "answer"},
    "answer": set(), "provisional_answer": set(), "accept": set(), "objection": {"rule"},
    "reply": {"rule"},
    "ruling": {"rule", "effect", "result", "document", "status", "uses", "target"},
    "disclose": {"document", "to"}, "publish": {"document"},
    "stipulation": {"agreed_by"}, "jury_presence": {"present"},
    "directions": {"rule"}, "jury_question": {"refs"},
    "deliberation": {"refs"}, "ballot": {"findings"},
    "deadlock": {"counts"}, "verdict": {"outcomes", "findings", "awards"},
    "erratum": {"target", "replacement"}, "gap": {"detail"},
    "repair": set(), "checkpoint": {"scene"}, "cadence": {"mode"},
    "unseal": {"confirmed"},
}


class CourtError(ValueError):
    """Rejected operations do not partially append to the authoritative journal."""


def require(test: Any, message: str) -> None:
    if not test:
        raise CourtError(message)


def encode(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", value))


def strings(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def unique(value: Any) -> bool:
    return strings(value) and len(set(value)) == len(value)


def members(case: dict, kind: str) -> set[str]:
    return {r for r, p in case["roles"].items() if p["kind"] == kind}


def jurors(case: dict) -> set[str]:
    return members(case, "juror")


def validate(case: dict) -> dict:
    """Validate a fully authored, jurisdiction-labelled simulation case, not its plausibility."""
    require(isinstance(case, dict) and type(case.get("schema")) is int and case["schema"] == 2,
            "Expected case schema 2.")
    require(identifier(case.get("case_id")), "Invalid case ID.")
    require(case.get("draft", False) is False, "Complete the case before commitment.")
    require(case.get("law_status") == "simulation", "Use disclosed simulation rules, not claims of legal fidelity.")
    cfg = case.get("config")
    require(isinstance(cfg, dict), "Missing case configuration.")
    kind, forum = cfg.get("case_type"), cfg.get("factfinder")
    require(isinstance(kind, str) and kind in SIDES and forum in {"bench", "jury"},
            "Choose civil/criminal and bench/jury independently.")
    require(cfg.get("player_side") in SIDES[kind], "Player side does not match the proceeding.")
    require(cfg.get("style") in STYLES and cfg.get("pace") in {"drama", "deliberate"}, "Unknown style or pace.")
    require(text(cfg.get("jurisdiction")), "Name the fictional or adapted jurisdiction explicitly.")
    for key in ("title", "public_summary", "brief", "procedure", "authorities", "truth", "opening"):
        require(text(case.get(key)), f"Missing {key}.")
    rules = case.get("rules")
    require(isinstance(rules, dict) and rules and all(identifier(k) and text(v) for k, v in rules.items()),
            "Supply rule IDs with their actual text.")
    roles, docs, issues, counts = (case.get(k) for k in ("roles", "documents", "issues", "counts"))
    require(isinstance(roles, dict) and CORE <= roles.keys(), "Supply counsel and bench packets.")
    require(all(identifier(r) and r not in RESERVED and isinstance(p, dict) for r, p in roles.items()), "Invalid role ID/packet.")
    require(isinstance(docs, dict) and isinstance(issues, dict) and issues and isinstance(counts, dict) and counts,
            "Supply documents, issues and counts/claims.")
    for r, p in roles.items():
        require(p.get("kind") in {"counsel", "bench", "witness", "juror", "support"}, "Unknown role kind.")
        require(text(p.get("name")) and strings(p.get("knowledge")), "Each role needs a name and knowledge allocation.")
        require(unique(p.get("documents")) and set(p["documents"]) <= docs.keys(), "Invalid role document allocation.")
        require(p.get("kind") != "bench" or r == "bench", "Only the bench role may act as judge.")
        require(p.get("kind") != "counsel" or r in {"player", "opponent"}, "Only the two allocated counsel roles litigate.")
        if r == "bench" or p["kind"] == "juror":
            require(not p["knowledge"] and not p["documents"], "Factfinders start without historical knowledge or private documents.")
        if p["kind"] == "witness":
            require(text(p.get("knowledge_basis")), "Specify the witness's knowledge sources and limits.")
    require(roles["bench"]["kind"] == "bench" and all(roles[r]["kind"] == "counsel" for r in ("player", "opponent")),
            "Invalid core role types.")
    require(bool(members(case, "witness")), "At least one material witness is required.")
    panel = jurors(case)
    n, threshold = cfg.get("jury_size", 0), cfg.get("verdict_threshold", 0)
    if forum == "jury":
        require(type(n) is int and 2 <= n <= 24 and n == len(panel), "Jury size must match 2..24 committed jurors.")
        require(type(threshold) is int and n / 2 < threshold <= n, "Declare an unambiguous agreement threshold.")
    else:
        require(not panel and type(n) is int and n == 0 and type(threshold) is int and threshold == 0,
                "A bench case has no active jury or jury threshold.")
    for k, d in docs.items():
        require(identifier(k) and not re.fullmatch(r"T\d+", k) and isinstance(d, dict), "Invalid/reserved document ID.")
        require(all(text(d.get(x)) for x in ("title", "text", "provenance")), "Documents need text, title and provenance.")
        require(d.get("status") in {"disclosed", "admitted", "limited", "excluded"}, "Invalid initial exhibit status.")
        require(unique(d.get("uses")) and set(d["uses"]) <= USES and bool(d["uses"]) == (d["status"] in {"admitted", "limited"}),
                "Permitted uses conflict with exhibit status.")
        if d["uses"]:
            require(all(k in roles[r]["documents"] for r in ("player", "opponent")), "Pre-admitted exhibits must reach both counsel.")
    for k, i in issues.items():
        require(identifier(k) and isinstance(i, dict) and text(i.get("text")), "Invalid material issue.")
        require(i.get("party") in SIDES[kind] and i.get("standard") in {"beyond_reasonable_doubt", "balance_of_probabilities"},
                "Each issue needs an explicit proof allocation.")
    used: set[str] = set()
    for k, count in counts.items():
        require(identifier(k) and isinstance(count, dict) and text(count.get("label")), "Invalid count/claim.")
        elements, bars = count.get("elements"), count.get("bars", [])
        require(unique(elements) and elements and unique(bars) and set(elements + bars) <= issues.keys()
                and len(set(elements + bars)) == len(elements + bars), "Specify distinct known elements and any affirmative-defence bars.")
        used.update(elements + bars)
        expect = "prosecution" if kind == "criminal" else "claimant"
        standard = "beyond_reasonable_doubt" if kind == "criminal" else "balance_of_probabilities"
        require(all(issues[x]["party"] == expect and issues[x]["standard"] == standard for x in elements),
                "Offence/claim elements retain the initiating party's burden.")
        other = next(iter(SIDES[kind] - {expect}))
        require(all(issues[x]["party"] == other for x in bars), "An affirmative-defence bar must name the responding party.")
        if "remedy" in count:
            remedy = count["remedy"]
            require(kind == "civil" and isinstance(remedy, dict) and type(remedy.get("maximum")) is int
                    and remedy["maximum"] >= 0 and text(remedy.get("currency")), "Civil remedies need currency and nonnegative integer cap.")
    require(used == set(issues), "Every material issue must belong to a count or claim.")
    return case


def safe_path(world: Path, rel: Path) -> Path:
    """Reject symlinks on managed paths; do not write through user-created indirection."""
    require(not rel.is_absolute() and ".." not in rel.parts, "Unsafe managed path.")
    current = world
    require(not current.is_symlink(), "World is a symlink.")
    for part in rel.parts:
        current = current / part
        require(not current.is_symlink(), f"Managed path is a symlink: {rel}")
    return current


def atomic(path: Path, data: bytes) -> None:
    require(not path.is_symlink(), "Refusing to overwrite a symlink.")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".court-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def world_path(root: Path, name: str) -> Path:
    require(isinstance(name, str) and bool(re.fullmatch(r"[a-z][a-z0-9-]{0,47}", name)), "Use a safe lowercase world name.")
    parent = root.resolve() / "worlds"
    require(not parent.is_symlink() and not (parent / name).is_symlink(), "World paths must not be symlinks.")
    return parent / name


@contextmanager
def locked(world: Path):
    path = safe_path(world, AREA / "writer.lock")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CourtError("Writer lock exists. Check for a live writer before removing a stale lock.") from exc
    try:
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)


WITNESS_BACKGROUND_FIELDS = ('life_history', 'occupation', 'training_and_qualifications',
                             'relationships', 'personal_stakes')
WITNESS_ACTIVITY_FIELDS = ('description', 'purpose', 'actions', 'tools_and_materials', 'authority', 'limits')


def validate_readiness(case: dict) -> dict:
    """New-play gate; legacy structural validation remains available for saved records.

Presence and placeholder checks cannot establish semantic completeness. Authors
must still review foundation questions against the witness's committed history.
"""
    validate(case)
    def authored(value):
        return (text(value) and value.strip().lower() not in
                {'todo', 'tbd', 'unknown', 'not specified', 'not provided', 'n/a', 'to be authored'}
                and not value.strip().lower().startswith(('replace:', 'todo:')))
    for who, role in case['roles'].items():
        if role['kind'] != 'witness':
            continue
        background = role.get('background')
        require(isinstance(background, dict) and set(background) == set(WITNESS_BACKGROUND_FIELDS)
                and all(authored(background[k]) for k in WITNESS_BACKGROUND_FIELDS),
                who + ': complete personal background before play (life, occupation, qualifications, relationships, stakes).')
        activities = role.get('relevant_activities')
        require(isinstance(activities, list) and activities and all(
                isinstance(row, dict) and set(row) == set(WITNESS_ACTIVITY_FIELDS)
                and all(authored(row[k]) for k in WITNESS_ACTIVITY_FIELDS) for row in activities),
                who + ': author concrete relevant_activities, including actions, tools/materials, authority and limits.')
        for key in ('knowledge_basis', 'memory', 'perception_limits', 'motives', 'manner'):
            require(authored(role.get(key)), who + ': author ' + key + ' before play.')
        require(role['knowledge'] and all(authored(item) for item in role['knowledge']),
                who + ': author personal knowledge before play.')
    return case


def initialise(root: Path, name: str, case: dict) -> Path:
    validate_readiness(case)
    world = world_path(root, name)
    require(not world.exists(), "World already exists. Resume it; do not replace its case.")
    world.parent.mkdir(parents=True, exist_ok=True)
    # mkdir is exclusive: a concurrent initialiser cannot overwrite an existing folder.
    world.mkdir()
    raw = encode(case)
    atomic(safe_path(world, AREA / "case.json"), raw)
    atomic(safe_path(world, AREA / "commitment.json"), encode({"schema": 2, "sha256": digest(raw)}))
    atomic(safe_path(world, AREA / "events.jsonl"), b"")
    atomic(safe_path(world, Path("charter.md")), ("# Courtroom charter\n\nModule: courtroom-v2\n\n"
           + "\n".join(f"- {k}: {v}" for k, v in case["config"].items())
           + "\n\nThe case and proof rules are fixed; telling and cadence may change.\n").encode())
    atomic(safe_path(world, Path(".world/truth.json")), encode({"courtroom_version": VERSION, "case_id": case["case_id"],
           "case_file": str(AREA / "case.json")}))
    render(world, case, [])
    return world


def read_case(world: Path) -> dict:
    raw = safe_path(world, AREA / "case.json").read_bytes()
    commitment = load(safe_path(world, AREA / "commitment.json"))
    require(commitment.get("schema") == 2 and digest(raw) == commitment.get("sha256"),
            "Committed case changed. Do not silently re-seal it.")
    return validate(json.loads(raw))


def read_events(world: Path) -> list[dict]:
    result, previous = [], "0" * 64
    for n, line in enumerate(safe_path(world, AREA / "events.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        e = json.loads(line)
        signature = e.pop("hash")
        require(e.get("id") == f"T{n:04d}" and e.get("previous") == previous and digest(encode(e)) == signature,
                "Event sequence or digest changed.")
        e["hash"] = signature
        previous = signature
        result.append(e)
    return result


def initial_state(case: dict) -> dict:
    return {"phase": "conference", "pending": None, "paused": False, "directions": False,
            "jury_present": False, "cadence": "flow" if case["config"]["pace"] == "drama" else "strict",
            "ballots": {}, "deadlocked": [], "verdict": None, "unsealed": False,
            "corrections": {}, "struck": [], "answers": {}, "published": [], "scene": {},
            "shown": {r: list(p["documents"]) for r, p in case["roles"].items()},
            "documents": {k: {"status": d["status"], "uses": list(d["uses"])} for k, d in case["documents"].items()}}


def evidence_invalid(key: str, state: dict) -> bool:
    return key in state["struck"] or key in state["corrections"] or bool(state["pending"] and state["pending"]["id"] == key)


def refcheck(refs: list, state: dict, events: list[dict], case: dict, role: str) -> None:
    require(isinstance(refs, list), "References must be a list.")
    indexed = {e["id"]: e for e in events}
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) == {"id", "use"} and isinstance(ref["id"], str)
                and ref["use"] in USES, "Reference requires ID and permitted use.")
        k, use = ref["id"], ref["use"]
        if k in state["documents"]:
            require(use in state["documents"][k]["uses"], f"Impermissible exhibit use: {k}/{use}")
            if role in jurors(case):
                require(k in state["published"], f"Exhibit {k} has not been placed before the jury.")
        else:
            e = indexed.get(k)
            require(e and e.get("purpose") != "admissibility" and e["type"] in {"exchange", "stipulation"} and role in e["audience"],
                    "Not evidence heard by this decision-maker.")
            require(not evidence_invalid(k, state), "Struck, corrected or provisional testimony cannot support a finding.")
            if e["type"] == "exchange":
                require(isinstance(e["data"].get("answer"), str) or k in state["answers"], "Unanswered questions are not evidence.")
            require(use in {"truth", "credibility"}, "Unsupported testimony use.")


def findings_check(findings: dict, state: dict, events: list[dict], case: dict, role: str) -> None:
    require(isinstance(findings, dict) and set(findings) == set(case["issues"]), "Address every supplied issue.")
    for f in findings.values():
        require(isinstance(f, dict) and set(f) == {"status", "reason", "refs"}
                and f["status"] in {"proved", "not_proved"} and text(f["reason"]), "Findings need status, reason and references.")
        require(f["status"] != "proved" or bool(f["refs"]), "A proved finding needs record evidence.")
        refcheck(f["refs"], state, events, case, role)


def result_for(case: dict, findings: dict) -> dict:
    positive, negative = ("guilty", "not_guilty") if case["config"]["case_type"] == "criminal" else ("liable", "not_liable")
    return {k: positive if all(findings[x]["status"] == "proved" for x in c["elements"])
            and not any(findings[x]["status"] == "proved" for x in c.get("bars", [])) else negative
            for k, c in case["counts"].items()}


def aggregate(case: dict, ballots: dict) -> dict:
    require(set(ballots) == jurors(case), "Every committed juror must return a ballot.")
    result = {}
    for count in case["counts"]:
        votes = Counter(result_for(case, f)[count] for f in ballots.values())
        winners = [v for v, n in votes.items() if n >= case["config"]["verdict_threshold"]]
        result[count] = winners[0] if winners else "hung"
    return result


def apply(state: dict, e: dict, earlier: list[dict], case: dict) -> None:
    kind, actor, audience, data = e["type"], e["actor"], e["audience"], e.get("data", {})
    roles, panel = case["roles"], jurors(case)
    require(isinstance(kind, str) and kind in FIELDS and isinstance(actor, str)
            and actor in set(roles) | RESERVED - {"jury"}, "Unknown event or actor.")
    require(isinstance(e["text"], str) and isinstance(data, dict) and data.keys() <= FIELDS[kind], "Invalid text/event data fields.")
    require(unique(audience) and set(audience) <= roles.keys(), "Invalid or repeated audience.")
    heard = set(audience)
    require(e.get("purpose", "merits") in {"merits", "admissibility"}, "Unknown event purpose.")
    require(e.get("purpose") != "admissibility" or not heard & panel, "Admissibility-only material cannot reach jurors.")
    court = {"exchange", "answer", "provisional_answer", "objection", "reply", "ruling", "stipulation", "submission", "publish", "directions", "jury_question", "verdict", "deadlock", "jury_presence"}
    if kind in court:
        require(CORE <= heard, "Court events must reach both counsel and bench.")
    if state["paused"]:
        require(kind in {"erratum", "gap", "repair", "checkpoint", "private"}, "Resolve the recorded simulation error before play continues.")
    if state["phase"] == "closed":
        require(kind in {"private", "dialogue", "checkpoint", "unseal", "erratum", "gap", "repair"}, "The case is closed.")
    if actor in panel:
        require(kind in {"ballot", "deliberation"}, "Jurors only speak in sealed deliberation; use the foreperson in court.")
    if actor == "foreperson":
        require(kind in {"jury_question", "verdict", "deadlock"}, "Foreperson cannot act as counsel or judge.")
    if kind == "ballot":
        require(actor in panel and heard == {actor}, "Each ballot is private to its juror.")
    elif kind == "deliberation":
        require(actor in panel and heard == panel, "Deliberation cannot include counsel or bench.")
    elif heard & panel:
        require(heard & panel == panel, "The seated panel must receive the same courtroom material.")
        require(kind not in {"private", "disclose", "dialogue", "checkpoint", "phase", "cadence", "unseal"}, "No uncontrolled/private contact with jurors.")
        require(state["jury_present"] or kind in {"jury_presence", "jury_question", "deadlock", "verdict", "erratum", "gap", "repair"}, "Jury is outside the courtroom.")
    if kind == "private":
        require(actor in {"player", "opponent", "engine"} and heard <= {"player", "opponent"} and len(heard) == 1,
                "Private strategy belongs to exactly one party.")
        require(actor == "engine" or actor in heard, "Private party cannot speak as the other side.")
    elif kind == "dialogue":
        require(actor not in RESERVED and actor not in panel, "Dialogue requires a real non-juror participant.")
        require(actor in heard or roles[actor]["kind"] == "support", "Speaker must participate in the conversation.")
        require(not CORE <= heard, "Material court speech needs its proper event type, not dialogue.")
    elif kind == "phase":
        require(actor == "engine" and state["pending"] is None and not state["paused"], "Cannot advance an unresolved exchange.")
        route = {"conference": {"opening", "preparation"}, "preparation": {"opening"}, "opening": {"evidence"},
                 "evidence": {"closing"}, "closing": {"decision"}, "decision": {"closed"}, "closed": set()}
        require(data.get("to") in route[state["phase"]], "Invalid phase transition.")
        require(data["to"] != "closed" or state["verdict"] is not None, "Close only after verdict, including an acknowledged hung result.")
        if data["to"] == "decision" and panel:
            require(state["directions"], "Give the jury its directions first.")
            state["jury_present"] = False
        if data["to"] == "opening" and panel:
            state["jury_present"] = True
        state["phase"] = data["to"]
    elif kind == "exchange":
        require(state["phase"] == "evidence" and state["pending"] is None, "An exchange needs an idle evidence phase.")
        witness = data.get("witness")
        require(actor in CORE and witness in members(case, "witness") and witness in heard, "Invalid examiner/witness.")
        require(text(data.get("question")), "Supply the exact question.")
        answer = data.get("answer")
        require(answer is None or isinstance(answer, str), "Answer is exact wording or null in pre-answer mode.")
        require(state["cadence"] != "strict" or answer is None, "Strict mode stops before the answer.")
        if panel and state["jury_present"]:
            require(panel <= heard, "The seated jury must hear the evidence exchange.")
        state["pending"] = {"id": e["id"], "witness": witness, "question": data["question"], "answer": answer,
                            "waiting": sorted({"player", "opponent"} - {actor}), "objected": False, "audience": audience}
    elif kind == "provisional_answer":
        p = state["pending"]
        require(state["cadence"] == "flow" and p and p["waiting"] and not p["objected"]
                and p["answer"] is None, "No flow-mode provisional answer opportunity.")
        require(actor == p["witness"] and heard == set(p["audience"]),
                "Only the questioned witness may answer to the same recipients.")
        p["answer"] = e["text"]
        state["answers"][p["id"]] = {"answer": e["text"], "turn": e["id"]}
    elif kind == "answer":
        p = state["pending"]
        require(p and not p["waiting"] and not p["objected"] and p["answer"] is None, "Question is not cleared for answer.")
        require(actor == p["witness"] and heard == set(p["audience"]), "Only that witness may answer to the same recipients.")
        state["answers"][p["id"]] = {"answer": e["text"], "turn": e["id"]}
        state["pending"] = None
    elif kind == "accept":
        p = state["pending"]
        require(p and not p["objected"] and actor in p["waiting"], "No objection opportunity for this actor.")
        require(CORE <= heard, "Record acceptance for both parties and bench.")
        p["waiting"].remove(actor)
        if not p["waiting"] and p["answer"] is not None:
            state["pending"] = None
    elif kind == "objection":
        p = state["pending"]
        require(p and not p["objected"] and actor in p["waiting"] and data.get("rule") in case["rules"], "Objection needs a live opportunity and supplied rule.")
        p["waiting"].remove(actor)
        p["objected"] = True
    elif kind == "reply":
        require(actor in {"player", "opponent"} and state["pending"] and state["pending"]["objected"]
                and data.get("rule") in case["rules"], "Reply requires a live objection.")
    elif kind == "ruling":
        require(actor == "bench" and data.get("rule") in case["rules"], "Ruling needs the judge and a disclosed rule.")
        effect = data.get("effect")
        if effect == "objection":
            p = state["pending"]
            require(p and p["objected"] and data.get("result") in {"sustained", "overruled"}, "No valid objection ruling.")
            if data["result"] == "sustained":
                state["struck"].append(p["id"])
                state["pending"] = None
            else:
                p["objected"] = False
                if not p["waiting"] and p["answer"] is not None:
                    state["pending"] = None
        elif effect == "document":
            require(state["phase"] in {"opening", "evidence"}, "Evidence is closed; reopen explicitly.")
            k, uses, status = data.get("document"), data.get("uses"), data.get("status")
            require(isinstance(k, str) and k in case["documents"] and status in {"disclosed", "admitted", "limited", "excluded"}, "Unknown document/status.")
            require(unique(uses) and set(uses) <= USES and bool(uses) == (status in {"admitted", "limited"}), "Invalid permitted uses.")
            require(k in state["shown"]["bench"], "Offer the exhibit to the judge before an admission ruling.")
            require(not uses or all(k in state["shown"][r] for r in ("player", "opponent")), "Disclose to both parties before admission.")
            state["documents"][k] = {"status": status, "uses": uses}
            if k in state["published"]:
                state["published"].remove(k)  # Changed admission needs republication with current limits.
        elif effect == "strike":
            require(state["phase"] in {"opening", "evidence"}, "Reopen before changing the evidentiary record.")
            target = next((x for x in earlier if x["id"] == data.get("target")), None)
            require(target and target["type"] in {"exchange", "stipulation"}, "Unknown testimony to strike.")
            state["struck"].append(target["id"])
        else:
            require(effect == "procedure", "Unknown ruling effect.")
    elif kind == "disclose":
        k, recipient = data.get("document"), data.get("to")
        require(isinstance(k, str) and k in case["documents"] and recipient in roles and recipient not in panel and recipient in heard, "Invalid disclosure.")
        require(actor == "engine" or (actor in roles and k in state["shown"][actor]), "Speaker does not possess that exhibit.")
        if k not in state["shown"][recipient]:
            state["shown"][recipient].append(k)
    elif kind == "publish":
        k = data.get("document")
        require(actor in CORE and state["phase"] in {"opening", "evidence"} and isinstance(k, str)
                and k in state["documents"] and bool(state["documents"][k]["uses"]), "Publish only admitted/limited evidence during hearing.")
        if panel:
            require(state["jury_present"] and panel <= heard, "Publish to the seated jury, not an absent panel.")
        if k not in state["published"]:
            state["published"].append(k)
    elif kind == "stipulation":
        require(state["phase"] in {"opening", "evidence"} and actor == "bench" and unique(data.get("agreed_by"))
                and set(data["agreed_by"]) == {"player", "opponent"}, "Stipulated facts require both parties and entry by the judge.")
        if panel and state["jury_present"]:
            require(panel <= heard, "The seated jury receives stipulated facts.")
    elif kind == "submission":
        require(actor in {"player", "opponent"} and state["phase"] in {"opening", "evidence", "closing", "decision"}, "Submission requires counsel and a live hearing.")
        # For openings, anticipated material can be outlined but not cited as proof.
        require(state["phase"] != "opening" or not data.get("refs"), "Opening is a forecast, not evidence citations.")
        refcheck(data.get("refs", []), state, earlier, case, "bench")
        if panel and state["jury_present"]:
            require(panel <= heard, "Addresses reach the seated jury.")
            for r in panel:
                refcheck(data.get("refs", []), state, earlier, case, r)
    elif kind == "jury_presence":
        require(actor == "bench" and panel and type(data.get("present")) is bool and state["pending"] is None,
                "Invalid jury presence change.")
        state["jury_present"] = data["present"]
    elif kind == "directions":
        require(actor == "bench" and panel and panel <= heard and data.get("rule") in case["rules"]
                and state["phase"] in {"closing", "decision"} and state["verdict"] is None, "Directions require the jury and disclosed rules.")
        state["directions"] = True
        state["ballots"] = {}
        state["deadlocked"] = []
    elif kind == "jury_question":
        require(actor == "foreperson" and panel and panel <= heard and state["phase"] == "decision" and state["verdict"] is None,
                "Jury questions go publicly through the judge.")
        for r in panel:
            refcheck(data.get("refs", []), state, earlier, case, r)
    elif kind == "deliberation":
        require(actor in panel and heard == panel and state["phase"] == "decision" and state["verdict"] is None,
                "Deliberation stays inside the jury, after evidence closes.")
        refcheck(data.get("refs", []), state, earlier, case, actor)
        state["deadlocked"] = []
    elif kind == "ballot":
        require(state["phase"] == "decision" and state["directions"] and state["verdict"] is None, "Jury not ready to decide.")
        findings_check(data.get("findings"), state, earlier, case, actor)
        state["ballots"][actor] = data["findings"]
        state["deadlocked"] = []
    elif kind == "deadlock":
        require(actor == "foreperson" and state["phase"] == "decision" and panel <= heard and state["verdict"] is None,
                "Deadlock report requires a deliberating jury.")
        results = aggregate(case, state["ballots"])
        require(unique(data.get("counts")) and data["counts"] and set(data["counts"]) == {k for k, v in results.items() if v == "hung"},
                "Report exactly the undecided counts after attempted deliberation, not a fabricated split.")
        require(any(x["type"] == "deliberation" for x in earlier), "A first split ballot alone is not an exhausted deliberation.")
        state["deadlocked"] = data["counts"]
    elif kind == "verdict":
        require(state["phase"] == "decision" and state["pending"] is None and state["verdict"] is None, "Not ready for verdict.")
        if panel:
            require(actor == "foreperson" and panel <= heard and set(data) == {"outcomes"}, "Jury result is returned by the foreperson, not selected by the bench.")
            result = aggregate(case, state["ballots"])
            require({k for k, v in result.items() if v == "hung"} <= set(state["deadlocked"]), "Unresolved counts need a genuine deadlock report.")
        else:
            require(actor == "bench" and set(data) <= {"findings", "outcomes", "awards"}, "Bench trial needs judicial findings.")
            findings_check(data.get("findings"), state, earlier, case, "bench")
            result = result_for(case, data["findings"])
            awards = data.get("awards", {})
            require(isinstance(awards, dict) and set(awards) <= case["counts"].keys(), "Unknown civil award.")
            for k, amount in awards.items():
                remedy = case["counts"][k].get("remedy")
                require(case["config"]["case_type"] == "civil" and remedy and type(amount) is int and 0 <= amount <= remedy["maximum"], "Invalid civil award.")
                require(amount == 0 or result[k] == "liable", "No damages without liability.")
        require(data.get("outcomes") == result, "Verdict must match findings and the committed agreement rule.")
        state["verdict"] = {"turn": e["id"], "outcomes": result, "text": e["text"], "awards": data.get("awards", {})}
    elif kind in {"erratum", "gap"}:
        require(actor == "engine", "Simulation faults are recorded by the controller.")
        if kind == "erratum":
            target = next((x for x in earlier if x["id"] == data.get("target")), None)
            require(target and isinstance(data.get("replacement"), str) and set(target["audience"]) <= heard,
                    "Correct a real turn openly to its original recipients.")
            state["corrections"][target["id"]] = e["id"]
            for qid, answer in state["answers"].items():
                if answer["turn"] == target["id"]:
                    state["corrections"][qid] = e["id"]
        else:
            require(text(data.get("detail")), "Record the material authoring gap.")
        state["paused"] = True
        state["pending"] = None
        state["ballots"] = {}
        state["deadlocked"] = []
        state["verdict"] = None
    elif kind == "repair":
        require(actor == "engine" and state["paused"], "No recorded fault to repair.")
        state["paused"] = False
        state["phase"] = "evidence"
        state["directions"] = False
    elif kind == "checkpoint":
        require(actor == "engine" and isinstance(data.get("scene", {}), dict), "Checkpoint requires scene metadata.")
        state["scene"] = data.get("scene", {})
    elif kind == "cadence":
        require(actor == "engine" and data.get("mode") in {"flow", "strict"} and state["pending"] is None, "Change cadence between exchanges.")
        state["cadence"] = data["mode"]
    elif kind == "unseal":
        require(actor == "engine" and state["phase"] == "closed" and data.get("confirmed") is True
                and heard == {"player"}, "Unsealing requires a closed case and explicit spoiler confirmation.")
        state["unsealed"] = True


def replay(case: dict, events: list[dict]) -> dict:
    state = initial_state(case)
    for i, e in enumerate(events):
        apply(state, e, events[:i], case)
    return state


def packet_from(case: dict, events: list[dict], role: str, merits: bool = False, state: dict | None = None) -> dict:
    require(role in case["roles"], "Unknown role.")
    state = replay(case, events) if state is None else state
    panel = jurors(case)
    factfinder = role == "bench" or role in panel
    merits = merits or role in panel
    allowed = {k for k, d in state["documents"].items() if d["uses"]} if factfinder else set(state["shown"][role])
    if role in panel:
        allowed &= set(state["published"])
    if factfinder:
        info = {k: case["roles"][role][k] for k in ("name", "kind")}
        if text(case["roles"][role].get("manner")):
            info["manner"] = case["roles"][role]["manner"]
    else:
        info = {k: deepcopy(v) for k, v in case["roles"][role].items() if k not in {"author_note", "truth"}}
    result = {"role_id": role, "role": info, "case_id": case["case_id"], "config": case["config"],
              "summary": case["public_summary"], "summary_is_evidence": False, "procedure": case["procedure"],
              "rules": case["rules"], "issues": case["issues"], "counts": case["counts"], "phase": state["phase"],
              "documents": {k: {"title": case["documents"][k]["title"], "text": case["documents"][k]["text"],
                                **state["documents"][k]} for k in sorted(allowed)}, "events": []}
    # A counsel brief is NOT the court's summary or evidence. Witnesses do not receive it either.
    if role in {"player", "opponent"}:
        result["brief"] = case["brief"]
    for e in events:
        if role not in e["audience"]:
            continue
        if merits and e.get("purpose") == "admissibility":
            continue
        invalid = evidence_invalid(e["id"], state)
        if merits and (invalid or e["type"] not in {"exchange", "stipulation", "submission", "directions", "jury_question", "deliberation"}):
            continue
        row = {k: deepcopy(e[k]) for k in ("id", "type", "actor", "text", "data")}
        if e["type"] == "exchange":
            answer = state["answers"].get(e["id"], {}).get("answer", e["data"].get("answer"))
            if merits and answer is None:
                continue
            row["data"]["answer"] = answer
            row["text"] = f"Question: {e['data']['question']}\nAnswer: {answer}"
        row["evidence"] = bool(not invalid and e["type"] in {"exchange", "stipulation"})
        if e["id"] in state["corrections"]:
            row["corrected_by"] = state["corrections"][e["id"]]
        result["events"].append(row)
    if role == "bench" and not merits:
        result["admissibility_only"] = {k: {"text": case["documents"][k]["text"], "evidence": False}
                                       for k in state["shown"]["bench"] if not state["documents"][k]["uses"]}
    if not factfinder:
        p = state["pending"]
        # Never leak an unheard witness's pending answer through a global state card.
        result["pending"] = deepcopy(p) if p and role in p["audience"] else None
    if role in panel:
        result["own_previous_ballot"] = deepcopy(state["ballots"].get(role))
    if role == "player" and state["unsealed"]:
        result["informed_replay"] = True
    return result


def packet(world: Path, role: str, merits: bool = False) -> dict:
    return packet_from(read_case(world), read_events(world), role, merits)


def projections(case: dict, events: list[dict]) -> dict[Path, bytes]:
    state = replay(case, events)
    player = packet_from(case, events, "player", state=state)
    def transcript(rows: list[dict], title: str) -> bytes:
        entries = []
        for e in rows:
            body = e["text"]
            if e["type"] == "exchange":
                body = f"Question: {e['data']['question']}\n\nAnswer: {e['data'].get('answer')}"
            entries.append(f"## {e['id']} | {e['actor']} | {e['type']}\n\n{body}\n\nRecord: {json.dumps(e['data'], ensure_ascii=False, sort_keys=True)}")
        return ("# " + title + "\n\n" + "\n\n".join(entries) + "\n").encode()
    public = [e for e in events if CORE <= set(e["audience"]) and e["type"] not in {"ballot", "deliberation"}]
    private = [e for e in events if "player" in e["audience"] and "bench" not in e["audience"]]
    out = {
        AREA / "live.json": encode(state),
        Path(".world/state.md"): (f"# Courtroom v2\n\n{case['title']}\nPhase: {state['phase']}\nCadence: {state['cadence']}\n"
             f"Pending: {json.dumps(state['pending'])}\nLast event: {events[-1]['id'] if events else 'none'}\nPaused: {state['paused']}\n"
             f"Scene: {json.dumps(state['scene'], ensure_ascii=False)}\nLoad role packets before speech. Never invent a missing material fact.\n").encode(),
        PUBLIC / "transcript.md": transcript(public, "Exact court record; corrections remain explicit"),
        PUBLIC / "private-record.md": transcript(private, "Counsel's private record, not evidence"),
        PUBLIC / "brief.md": case["brief"].encode(),
        Path("canon/procedure.md"): case["procedure"].encode(),
        Path("canon/authorities.md"): case["authorities"].encode(),
        PUBLIC / "exhibits.json": encode(player["documents"]),
        Path("canon/charge-sheet.json"): encode({"issues": case["issues"], "counts": case["counts"], "rules": case["rules"]}),
        PUBLIC / "client-packet.json": encode(player["role"]),
        PUBLIC / "verdict.json": encode(state["verdict"]),
        AREA / "errata.md": transcript([e for e in events if e["type"] in {"erratum", "gap", "repair"}], "Simulation errors, not witness lies"),
    }
    # Human-readable copies only for documents actually disclosed to the player.
    index = "# Received documents\n\nID | Title | Status | Permitted uses\n---|---|---|---\n"
    for key, doc in player["documents"].items():
        out[PUBLIC / "documents" / f"{key}.md"] = (f"# {key}: {doc['title']}\n\n" + doc["text"] + "\n").encode()
        index += f"{key} | {doc['title']} | {doc['status']} | {', '.join(doc['uses']) or 'none'}\n"
    out[PUBLIC / "exhibit-index.md"] = index.encode()
    if state["verdict"]:
        deciders = sorted(jurors(case)) or ["bench"]
        out[AREA / "decision-record.json"] = encode({"packets": {r: packet_from(case, events, r, True, state) for r in deciders},
                                                     "ballots": state["ballots"], "verdict": state["verdict"]})
    if state["unsealed"]:
        out[PUBLIC / "unsealed-case.json"] = encode(case)
    return out


OPTIONAL = (AREA / "decision-record.json", PUBLIC / "unsealed-case.json")


def render(world: Path, case: dict, events: list[dict]) -> None:
    output = projections(case, events)
    for path, content in output.items():
        atomic(safe_path(world, path), content)
    for path in OPTIONAL:
        if path not in output:
            safe_path(world, path).unlink(missing_ok=True)


def verify(world: Path, caches: bool = True) -> dict:
    case, events = read_case(world), read_events(world)
    state = replay(case, events)
    if caches:
        output = projections(case, events)
        for path, data in output.items():
            target = safe_path(world, path)
            require(target.is_file() and target.read_bytes() == data, f"Stale projection {path}; use resume, not reset.")
        for path in OPTIONAL:
            require(path in output or not safe_path(world, path).exists(), "Stale optional projection; use resume.")
    return {"status": "PASS", "case_id": case["case_id"], "case_type": case["config"]["case_type"],
            "factfinder": case["config"]["factfinder"], "phase": state["phase"], "events": len(events)}


def record(world: Path, inputs: dict | list[dict], expected: int | None = None, *, _ticket=None, _fixture=False) -> list[str]:
    with locked(world):
        if safe_path(world, AREA / 'runtime.json').exists():
            from courtroom_sessions import consume_ticket
            consume_ticket(world, inputs, expected, _ticket)
        else:
            require(_fixture is True, "Start an isolated-session backend before recording live contributions.")
        case, events = read_case(world), read_events(world)
        require(expected is None or (type(expected) is int and expected == len(events)), "Stale or invalid expected event count.")
        state = replay(case, events)
        batch = inputs if isinstance(inputs, list) else [inputs]
        require(bool(batch), "Empty event batch.")
        ids = []
        for raw in batch:
            require(isinstance(raw, dict) and {"type", "actor", "text", "audience"} <= raw.keys()
                    and raw.keys() <= {"type", "actor", "text", "audience", "data", "private_note", "purpose"}, "Invalid event fields.")
            e = deepcopy(raw)
            e.setdefault("data", {})
            e["id"] = f"T{len(events)+1:04d}"
            e["previous"] = events[-1]["hash"] if events else "0" * 64
            apply(state, e, events, case)
            e["hash"] = digest(encode(e))
            events.append(e)
            ids.append(e["id"])
        # Commit all or none of a batch; projections are recoverable if the process dies next.
        atomic(safe_path(world, AREA / "events.jsonl"), b"".join(json.dumps(e, ensure_ascii=False, sort_keys=True).encode() + b"\n" for e in events))
        render(world, case, events)
        return ids


def resume(world: Path) -> dict:
    with locked(world):
        case, events = read_case(world), read_events(world)
        render(world, case, events)
        return verify(world)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "init", "verify", "resume", "packet", "record", "unseal"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--world", default="courtroom")
    parser.add_argument("--case", type=Path)
    parser.add_argument("--role")
    parser.add_argument("--event", type=Path)
    parser.add_argument("--expected", type=int)
    parser.add_argument("--merits", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--confirm-spoilers", action="store_true")
    args = parser.parse_args()
    try:
        world = world_path(args.root, args.world)
        if args.command in {"validate", "init"}:
            require(args.case is not None, "Supply a fully authored case with --case. No single-case hidden default.")
            case = validate_readiness(load(args.case))
            if args.command == "validate":
                print("Case structure and witness foundation PASS; semantic authoring review remains required.")
            else:
                raise CourtError("Live startup requires an independent-session backend via tools/courtroom.py; init cannot start a shared-context court.")
        elif args.command == "packet":
            value = encode(packet(world, args.role, args.merits))
            require(args.out is not None, "Use --out to avoid printing sealed role packets.")
            dest, safe = args.out.resolve(), (world / ".world/packets").resolve()
            require(dest.is_relative_to(safe) and args.out.suffix == ".json", "Packet must be a JSON file under this world's .world/packets/.")
            safe_path(world, args.out.absolute().relative_to(world.absolute()))
            atomic(args.out, value)
            print(f"Packet written: {args.out}")
        elif args.command == "record":
            require(args.event is not None, "Supply --event JSON_FILE.")
            print("Recorded " + ", ".join(record(world, load(args.event), args.expected)))
        elif args.command == "unseal":
            record(world, {"type": "unseal", "actor": "engine", "text": "The player confirmed opening this closed case.",
                           "audience": ["player"], "data": {"confirmed": args.confirm_spoilers}})
            print(f"Unsealed: {world / PUBLIC / 'unsealed-case.json'}")
        else:
            print(json.dumps(resume(world) if args.command == "resume" else verify(world), sort_keys=True))
        return 0
    except (CourtError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"Courtroom error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
