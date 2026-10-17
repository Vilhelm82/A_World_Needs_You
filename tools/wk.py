#!/usr/bin/env python3
"""wk: the Worldkeeper tool for structured worlds.

Validates world state, computes evaluation metrics, writes scorecards, and
manages timelines (save, fork, holodeck, return). Standard library only.

  python3 tools/wk.py validate worlds/enterprise
  python3 tools/wk.py validate --all              (what the pre-commit hook runs)
  python3 tools/wk.py next-id worlds/enterprise fact
  python3 tools/wk.py metrics worlds/enterprise --watch 3 --write
  python3 tools/wk.py report worlds/enterprise --watch 3
  python3 tools/wk.py stamp
  python3 tools/wk.py save worlds/enterprise before-the-party
  python3 tools/wk.py fork worlds/enterprise romulan-ale
  python3 tools/wk.py holodeck worlds/enterprise
  python3 tools/wk.py return worlds/enterprise
  python3 tools/wk.py install-hooks

A world is "structured" when it has .world/state/. Other worlds are ignored.
Spec: modules/tng-d/STATE.md. Goals and targets: modules/eval/GOALS.md.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- constants

ALERTS = {"normal", "yellow", "red"}
TIERS = {"canon", "recurring"}
HORIZONS = {"shift", "week", "career"}
REGARD_KINDS = {"praise", "trust", "candour", "warmth", "anger", "desire"}
PRECEDENT_KINDS = {"lore", "procedure", "tech", "person"}
FORCE_STATUS = {"on_track", "delayed", "averted", "altered", "done"}
TRACE_TYPES = {"location", "computer_access", "authorisation", "transporter", "replicator",
               "door", "sensor", "witness", "physical", "behavioural", "empathic"}
ROLES = {"security", "captain", "ops", "medical", "engineering", "anyone"}
CASE_STATUS = {"open", "closed", "cold"}
EPISODE_STATUS = {"pending", "open", "closed"}
PIN_OPS = {"==", "!=", "in"}
VERDICTS = {"consistent", "unsupported", "contradicts"}
OUTCOMES = {"done", "denied", "cost"}

LEDGER_FIELDS = {
    "TURN": ["stardate", "present", "speakers", "addressed", "initiated", "transcript"],
    "DID": ["decision", "changed"],
    "SAID": ["by", "claim", "truth"],
    "TOLD": ["to", "fact"],
    "HAS": ["item", "change"],
    "MOVED": ["by", "what", "cause"],
    "DECIDED": ["by", "what", "without_player"],
    "ATTEMPT": ["what", "outcome", "reason"],
    "CHANGED": ["who", "field", "cause"],
    "PRECEDENT": ["id"],
    "OBJECTION": ["claim", "verdict", "ruling"],
    "WORLDTURN": ["steps"],
    "NOTE": ["text"],
    "RATE": ["scores"],
    "LAW": [], "ROLL": [], "REWOUND": [], "SAVE": [], "FORK": [], "RETURN": [], "HOLODECK": [],
    "WATCH": [],
}

ID_PREFIX = {"fact": "F", "precedent": "P", "trace": "T", "case": "C", "episode": "E", "premise": "R"}

# Targets from modules/eval/GOALS.md. (metric, goal, op, value)
TARGETS = [
    ("objections_upheld", "G1", "<=", 0),
    ("player_address_share", "G4", "<=", 0.35),
    ("neglected_windows", "G4", "<=", 0),
    ("autonomy", "G5", ">=", 0.5),
    ("npc_initiative", "G5", ">=", 0.3),
    ("decided_without_player", "G5", ">=", 1),
    ("cases_isolated", "G7", ">=", 1.0),
    ("canon_distance_checked", "G8", ">=", 1.0),
    ("parity", "G10", ">=", 1.0),
    ("dirty_at_eval", "G10", "<=", 0),
    ("fork_bleed", "G11", "<=", 0),
]
GOAL_IDS = [f"G{i}" for i in range(1, 12)]


# ---------------------------------------------------------------- git helpers

def git(*args, check=True, cwd=None):
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


def repo_root():
    return Path(git("rev-parse", "--show-toplevel").strip())


def head_text(relpath, ref="HEAD"):
    """File content at ref, or None if it does not exist there."""
    r = subprocess.run(["git", "show", f"{ref}:{relpath}"], capture_output=True, text=True,
                       cwd=repo_root())
    return r.stdout if r.returncode == 0 else None


def head_json(relpath, ref="HEAD"):
    t = head_text(relpath, ref)
    if t is None:
        return None
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


def current_branch():
    return git("rev-parse", "--abbrev-ref", "HEAD").strip()


def tree_clean():
    return git("status", "--porcelain").strip() == ""


# ---------------------------------------------------------------- world model

class World:
    def __init__(self, path):
        self.root = repo_root()
        p = Path(path)
        self.path = (p if p.is_absolute() else Path.cwd() / p).resolve()
        self.rel = self.path.relative_to(self.root).as_posix()
        self.name = self.path.name
        self.dot = self.path / ".world"
        self.state = self.dot / "state"

    def relp(self, p):
        return Path(p).resolve().relative_to(self.root).as_posix()

    def is_structured(self):
        return self.state.is_dir()

    def crew_ids(self):
        d = self.state / "crew"
        return {c.name for c in d.iterdir() if c.is_dir()} if d.is_dir() else set()

    def ledger_path(self):
        return self.dot / "ledger.jsonl"

    def ledger(self):
        p = self.ledger_path()
        if not p.exists():
            return []
        out = []
        for line in p.read_text().splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    out.append({"type": "_BAD", "raw": line})
        return out

    def timeline(self):
        p = self.dot / "timeline.json"
        return json.loads(p.read_text()) if p.exists() else {}


def all_structured_worlds():
    root = repo_root()
    wdir = root / "worlds"
    return [World(p) for p in sorted(wdir.iterdir()) if (p / ".world" / "state").is_dir()] \
        if wdir.is_dir() else []


# ---------------------------------------------------------------- validation

class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def load(path, rep, required=True):
    if not path.exists():
        if required:
            rep.err(path.name, "missing")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        rep.err(path.name, f"invalid JSON ({e})")
        return None


def need(obj, keys, where, rep):
    if not isinstance(obj, dict):
        rep.err(where, "must be an object")
        return False
    missing = [k for k in keys if k not in obj]
    for k in missing:
        rep.err(where, f"missing field '{k}'")
    return not missing


def valid_ref(x, crew, extra=()):
    return x in crew or x in extra or (isinstance(x, str) and x.startswith("crowd:"))


def new_ledger_entries(w):
    """Ledger entries appended since HEAD."""
    old = head_text(f"{w.rel}/.world/ledger.jsonl") or ""
    cur = w.ledger_path().read_text() if w.ledger_path().exists() else ""
    if not cur.startswith(old):
        return []
    out = []
    for line in cur[len(old):].splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def validate_world(w):
    rep = Report()
    s = w.state
    crew = w.crew_ids()
    added = new_ledger_entries(w)

    # timeline.json
    tl = load(w.dot / "timeline.json", rep)
    if tl is not None and "main" not in tl:
        rep.err("timeline.json", "missing 'main'")

    # clock
    clock = load(s / "clock.json", rep)
    if clock is not None and need(clock, ["stardate", "ship_time", "day", "alert", "location",
                                          "episode_open", "timeline"], "clock.json", rep):
        if not isinstance(clock["stardate"], (int, float)):
            rep.err("clock.json", "stardate must be a number")
        if clock["alert"] not in ALERTS:
            rep.err("clock.json", f"alert must be one of {sorted(ALERTS)}")
        if not re.fullmatch(r"\d\d:\d\d", str(clock["ship_time"])):
            rep.err("clock.json", "ship_time must be HH:MM")
        old = head_json(f"{w.rel}/.world/state/clock.json")
        if old and isinstance(old.get("stardate"), (int, float)) \
                and isinstance(clock["stardate"], (int, float)) \
                and old.get("timeline") == clock.get("timeline") \
                and clock["stardate"] < old["stardate"]:
            rep.err("clock.json", f"stardate went backwards ({old['stardate']} -> {clock['stardate']})")

    load(s / "ship.json", rep)

    # crew
    changed = {(e.get("who"), str(e.get("field", "")).split(".")[0]) for e in added
               if e.get("type") == "CHANGED"}
    for cid in sorted(crew):
        where = f"crew/{cid}/soul.json"
        soul = load(s / "crew" / cid / "soul.json", rep)
        if soul is None:
            continue
        if not need(soul, ["id", "name", "rank", "post", "tier", "created_at", "persona", "regard",
                           "routing", "agenda", "relationships", "schedule", "location"], where, rep):
            continue
        if soul["id"] != cid:
            rep.err(where, f"id '{soul['id']}' does not match folder '{cid}'")
        if soul["tier"] not in TIERS:
            rep.err(where, f"tier must be one of {sorted(TIERS)}")
        need(soul["persona"], ["values", "traits", "tired_of", "wrong_about", "cares_about"],
             where + " persona", rep)
        reg = soul["regard"]
        if need(reg, ["gives_freely", "gives_rarely"], where + " regard", rep):
            for k in reg["gives_freely"] + reg["gives_rarely"]:
                if k not in REGARD_KINDS:
                    rep.err(where, f"regard kind '{k}' not in {sorted(REGARD_KINDS)}")
            for t in (reg.get("toward") or {}):
                if not valid_ref(t, crew, {"player"}):
                    rep.err(where, f"regard.toward names unknown '{t}'")
        if isinstance(soul["routing"], dict):
            for topic, ids in soul["routing"].items():
                for x in ids if isinstance(ids, list) else [ids]:
                    if not valid_ref(x, crew, {"player"}):
                        rep.err(where, f"routing '{topic}' names unknown '{x}'")
        else:
            rep.err(where, "routing must be an object")
        for i, a in enumerate(soul["agenda"] if isinstance(soul["agenda"], list) else []):
            if need(a, ["goal", "next_step", "horizon"], f"{where} agenda[{i}]", rep) \
                    and a["horizon"] not in HORIZONS:
                rep.err(where, f"agenda[{i}] horizon must be one of {sorted(HORIZONS)}")
        for r in (soul["relationships"] or {}):
            if not valid_ref(r, crew, {"player"}):
                rep.err(where, f"relationship with unknown '{r}'")
        if "voice" in soul and not (w.root / soul["voice"].split("#")[0]).exists() \
                and not (s / "crew" / cid / soul["voice"]).exists():
            rep.err(where, f"voice card '{soul['voice']}' not found")
        old = head_json(f"{w.rel}/.world/state/crew/{cid}/soul.json")
        if old and old.get("persona") != soul.get("persona") and (cid, "persona") not in changed:
            rep.err(where, "persona changed without a CHANGED ledger entry naming this person and "
                           "field 'persona'")
        mem = load(s / "crew" / cid / "memory.json", rep)
        if mem is not None:
            need(mem, ["learned", "beliefs", "recent"], f"crew/{cid}/memory.json", rep)

    # facts
    facts = load(s / "facts.json", rep)
    fact_ids = set()
    if facts is not None and need(facts, ["facts"], "facts.json", rep):
        for i, f in enumerate(facts["facts"]):
            where = f"facts.json[{i}]"
            if not need(f, ["id", "statement", "known_by", "surfaced_at", "source", "created_at"],
                        where, rep):
                continue
            if f["id"] in fact_ids:
                rep.err(where, f"duplicate id {f['id']}")
            fact_ids.add(f["id"])
            for k in f["known_by"]:
                if not valid_ref(k, crew, {"player", "all"}):
                    rep.err(where, f"known_by names unknown '{k}'")
        old = head_json(f"{w.rel}/.world/state/facts.json") or {}
        cur = {f.get("id"): f for f in facts["facts"] if isinstance(f, dict)}
        for of in old.get("facts", []):
            if of.get("surfaced_at") is None:
                continue
            nf = cur.get(of["id"])
            if nf is None:
                rep.err("facts.json", f"surfaced fact {of['id']} was removed")
                continue
            for k in ("statement", "surfaced_at", "source", "created_at"):
                if nf.get(k) != of.get(k):
                    rep.err("facts.json", f"surfaced fact {of['id']} changed field '{k}'")
            if not set(of.get("known_by", [])) <= set(nf.get("known_by", [])):
                rep.err("facts.json", f"surfaced fact {of['id']} lost a knower (known_by only grows)")

    # precedents
    prec = load(s / "precedents.json", rep)
    if prec is not None and need(prec, ["precedents"], "precedents.json", rep):
        seen = set()
        for i, p in enumerate(prec["precedents"]):
            where = f"precedents.json[{i}]"
            if need(p, ["id", "ruling", "kind", "reason", "source", "created_at"], where, rep):
                if p["id"] in seen:
                    rep.err(where, f"duplicate id {p['id']}")
                seen.add(p["id"])
                if p["kind"] not in PRECEDENT_KINDS:
                    rep.err(where, f"kind must be one of {sorted(PRECEDENT_KINDS)}")
        old = head_json(f"{w.rel}/.world/state/precedents.json") or {}
        cur = {p.get("id"): p for p in prec["precedents"] if isinstance(p, dict)}
        for op in old.get("precedents", []):
            if cur.get(op.get("id")) != op:
                rep.err("precedents.json", f"precedent {op.get('id')} was edited or removed "
                                           "(precedents are append-only; refine with a new one)")

    # forces
    forces = load(s / "forces.json", rep)
    if forces is not None and need(forces, ["forces"], "forces.json", rep):
        for i, fo in enumerate(forces["forces"]):
            where = f"forces.json[{i}]"
            if not need(fo, ["id", "state", "wants", "capabilities", "trajectory"], where, rep):
                continue
            for j, st in enumerate(fo["trajectory"]):
                if need(st, ["step", "preconditions", "status"], f"{where} trajectory[{j}]", rep):
                    if st["status"] not in FORCE_STATUS:
                        rep.err(where, f"trajectory[{j}] status must be one of {sorted(FORCE_STATUS)}")
                    elif st["status"] != "on_track" and not st.get("cause"):
                        rep.err(where, f"trajectory[{j}] is '{st['status']}' with no cause")

    # evidence
    ev = load(s / "evidence.json", rep)
    trace_ids = set()
    if ev is not None and need(ev, ["traces", "cases"], "evidence.json", rep):
        for i, t in enumerate(ev["traces"]):
            where = f"evidence.json traces[{i}]"
            if not need(t, ["id", "type", "where", "who_can_read", "lasts", "created_at"], where, rep):
                continue
            trace_ids.add(t["id"])
            if t["type"] not in TRACE_TYPES:
                rep.err(where, f"type must be one of {sorted(TRACE_TYPES)}")
            for x in t["who_can_read"]:
                if not valid_ref(x, crew, ROLES):
                    rep.err(where, f"who_can_read names unknown '{x}'")
        for i, c in enumerate(ev["cases"]):
            where = f"evidence.json cases[{i}]"
            if not need(c, ["case_id", "investigator", "trigger", "known", "next_step", "status"],
                        where, rep):
                continue
            if c["investigator"] not in crew:
                rep.err(where, f"investigator '{c['investigator']}' has no soul folder")
            if c["status"] not in CASE_STATUS:
                rep.err(where, f"status must be one of {sorted(CASE_STATUS)}")
            for k in c["known"]:
                if k not in trace_ids:
                    rep.err(where, f"known trace '{k}' does not exist")
            for r in c.get("runs", []):
                for k in r.get("cited", []):
                    if k not in c["known"]:
                        rep.err(where, f"run at turn {r.get('turn')} cites '{k}', outside the "
                                       "investigator's light cone")

    # episodes
    epd = s / "episodes"
    if epd.is_dir():
        for p in sorted(epd.glob("*.json")):
            ep = load(p, rep)
            where = f"episodes/{p.name}"
            if ep is None or not need(ep, ["id", "status", "arrival", "premise", "lands_on",
                                           "b_plot", "forces", "truth"], where, rep):
                continue
            if ep["id"] != p.stem:
                rep.err(where, f"id '{ep['id']}' does not match filename")
            if ep["status"] not in EPISODE_STATUS:
                rep.err(where, f"status must be one of {sorted(EPISODE_STATUS)}")
            for x in ep["lands_on"]:
                if not valid_ref(x, crew, {"player"}):
                    rep.err(where, f"lands_on names unknown '{x}'")

    prem = load(s / "premises.json", rep)
    if prem is not None and need(prem, ["premises"], "premises.json", rep):
        for i, pr in enumerate(prem["premises"]):
            need(pr, ["id", "candidates", "roll", "chosen", "canon_distance"],
                 f"premises.json[{i}]", rep)

    pins = load(s / "pins.json", rep)
    if pins is not None and need(pins, ["pins"], "pins.json", rep):
        for i, pn in enumerate(pins["pins"]):
            where = f"pins.json[{i}]"
            if need(pn, ["when", "attach"], where, rep):
                if need(pn["when"], ["path", "op", "value"], where + " when", rep) \
                        and pn["when"]["op"] not in PIN_OPS:
                    rep.err(where, f"op must be one of {sorted(PIN_OPS)}")
                if not (w.root / pn["attach"]).exists():
                    rep.err(where, f"attach path '{pn['attach']}' not found")

    # ledger: append-only, typed, referentially sound
    lp = w.ledger_path()
    old = head_text(f"{w.rel}/.world/ledger.jsonl")
    cur = lp.read_text() if lp.exists() else None
    if cur is None:
        rep.err("ledger.jsonl", "missing")
    else:
        if old is not None and not cur.startswith(old):
            rep.err("ledger.jsonl", "is not append-only: earlier lines were changed or removed")
        for n, line in enumerate(cur.splitlines(), 1):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                rep.err("ledger.jsonl", f"line {n} is not valid JSON")
                continue
            where = f"ledger.jsonl line {n}"
            if not need(e, ["watch", "turn", "type"], where, rep):
                continue
            t = e["type"]
            if t not in LEDGER_FIELDS:
                rep.err(where, f"unknown type '{t}'")
                continue
            need(e, LEDGER_FIELDS[t], f"{where} ({t})", rep)
            if t == "TURN":
                for k in ("present", "speakers", "initiated"):
                    for x in e.get(k, []):
                        if not valid_ref(x, crew, {"player"}):
                            rep.err(where, f"TURN {k} names unknown '{x}'")
                for x in (e.get("addressed") or {}):
                    if not valid_ref(x, crew, {"player"}):
                        rep.err(where, f"TURN addressed names unknown '{x}'")
            elif t == "OBJECTION" and e.get("verdict") not in VERDICTS:
                rep.err(where, f"verdict must be one of {sorted(VERDICTS)}")
            elif t == "ATTEMPT" and e.get("outcome") not in OUTCOMES:
                rep.err(where, f"outcome must be one of {sorted(OUTCOMES)}")
            elif t == "TOLD" and fact_ids and e.get("fact") not in fact_ids:
                rep.err(where, f"TOLD fact '{e.get('fact')}' does not exist")
            elif t == "PRECEDENT" and prec and e.get("id") not in {p.get("id") for p in prec.get("precedents", [])}:
                rep.err(where, f"PRECEDENT '{e.get('id')}' does not exist")

    # transcripts: append-only
    tdir = w.dot / "transcript"
    if tdir.is_dir():
        for p in sorted(tdir.glob("*.md")):
            old = head_text(f"{w.rel}/.world/transcript/{p.name}")
            if old is not None and not p.read_text().startswith(old):
                rep.err(f"transcript/{p.name}", "is not append-only")
    for line in (git("ls-tree", "-r", "--name-only", "HEAD", "--", f"{w.rel}/.world/transcript",
                     check=False) or "").splitlines():
        if not (w.root / line).exists():
            rep.err("transcript", f"{Path(line).name} was deleted")

    return rep


def cmd_validate(a):
    worlds = all_structured_worlds() if a.all else [World(a.world)]
    bad = 0
    for w in worlds:
        if not w.is_structured():
            print(f"{w.rel}: not a structured world (no .world/state/); nothing to validate")
            continue
        rep = validate_world(w)
        for m in rep.warnings:
            print(f"warning  {w.rel}: {m}")
        for m in rep.errors:
            print(f"ERROR    {w.rel}: {m}")
        if a.hook:
            log_validation(w, rep)
        if rep.errors:
            bad += 1
        elif not a.hook:
            print(f"{w.rel}: valid")
    if bad:
        print("\nState is invalid. Fix it, then commit. Nothing is told until it commits.")
        sys.exit(1)


def log_validation(w, rep):
    d = Path(git("rev-parse", "--git-dir").strip())
    d = (d if d.is_absolute() else repo_root() / d) / "wk"
    d.mkdir(exist_ok=True)
    with open(d / "validator-log.jsonl", "a") as f:
        f.write(json.dumps({"time": dt.datetime.now().isoformat(timespec="seconds"), "world": w.name,
                            "ok": not rep.errors, "errors": rep.errors[:20]}) + "\n")


# ---------------------------------------------------------------- next-id

def cmd_next_id(a):
    w = World(a.world)
    prefix = ID_PREFIX[a.kind]
    text = ""
    for p in w.state.rglob("*.json"):
        text += p.read_text()
    nums = [int(m) for m in re.findall(rf'"{prefix}-(\d+)"', text)]
    print(f"{prefix}-{(max(nums) + 1 if nums else 1):03d}")


# ---------------------------------------------------------------- metrics

def ratio(n, d):
    return round(n / d, 3) if d else None


def compute_metrics(w, watch=None):
    led = w.ledger()
    entries = [e for e in led if watch is None or e.get("watch") == watch]
    turns = [e for e in entries if e.get("type") == "TURN"]
    m = {"world": w.name, "watch": watch, "harness": stamp(), "turns": len(turns)}

    # G4: address share when at least two crew are present
    num = den = 0
    for t in turns:
        present = [x for x in t.get("present", []) if x != "player"]
        if len(present) >= 2:
            ad = t.get("addressed") or {}
            num += ad.get("player", 0)
            den += sum(ad.values())
    m["player_address_share"] = ratio(num, den)

    # G4: neglected senior officers, in sliding windows of 10 turns (Talemate's threshold)
    canon = set()
    for cid in w.crew_ids():
        try:
            if json.loads((w.state / "crew" / cid / "soul.json").read_text()).get("tier") == "canon":
                canon.add(cid)
        except (OSError, json.JSONDecodeError):
            pass
    neglected_windows, neglected_ids = 0, set()
    for end in range(10, len(turns) + 1):
        win = turns[end - 10:end]
        lines = sum(len(t.get("speakers", [])) for t in win)
        flagged = False
        for cid in canon:
            if sum(cid in t.get("present", []) for t in win) >= 5:
                share = sum(cid in t.get("speakers", []) for t in win) / lines if lines else 0
                if share < 0.15:
                    flagged = True
                    neglected_ids.add(cid)
        neglected_windows += flagged
    m["neglected_windows"] = neglected_windows if len(turns) >= 10 else None
    m["neglected_ids"] = sorted(neglected_ids)

    # G5
    moved = [e for e in entries if e.get("type") == "MOVED"]
    m["autonomy"] = ratio(sum(e.get("cause") != "player" for e in moved), len(moved))
    m["npc_initiative"] = ratio(sum(any(x != "player" for x in t.get("initiated", [])) for t in turns),
                                len(turns))
    m["decided_without_player"] = sum(1 for e in entries if e.get("type") == "DECIDED"
                                      and e.get("without_player"))

    # G6
    att = [e for e in entries if e.get("type") == "ATTEMPT"]
    m["attempts"] = {k: sum(e.get("outcome") == k for e in att) for k in sorted(OUTCOMES)}

    # G1
    obj = [e for e in entries if e.get("type") == "OBJECTION"]
    m["objections"] = {k: sum(e.get("verdict") == k for e in obj) for k in sorted(VERDICTS)}
    m["objections_upheld"] = m["objections"]["contradicts"]
    m["precedents_added"] = sum(e.get("type") == "PRECEDENT" for e in entries)

    # G7
    runs = total = 0
    ev = w.state / "evidence.json"
    if ev.exists():
        for c in json.loads(ev.read_text()).get("cases", []):
            for r in c.get("runs", []):
                if watch is None or r.get("watch") == watch:
                    total += 1
                    runs += bool(r.get("isolated"))
    m["cases_isolated"] = ratio(runs, total)

    # G8
    eps = list((w.state / "episodes").glob("*.json")) if (w.state / "episodes").is_dir() else []
    prem_path = w.state / "premises.json"
    checked = 0
    if prem_path.exists() and eps:
        prem = {p.get("id"): p for p in json.loads(prem_path.read_text()).get("premises", [])}
        for e in eps:
            pid = json.loads(e.read_text()).get("premise")
            checked += bool(prem.get(pid, {}).get("canon_distance"))
    m["canon_distance_checked"] = ratio(checked, len(eps))

    # G10
    tp = w.dot / "transcript" / f"watch-{watch:03d}.md" if watch is not None else None
    if tp and tp.exists():
        tturns = len(re.findall(r"^## turn \d+", tp.read_text(), flags=re.M))
        m["transcript_turns"] = tturns
        m["parity"] = ratio(min(tturns, len(turns)), max(tturns, len(turns)))
    else:
        m["parity"] = None
    m["dirty_at_eval"] = len([l for l in git("status", "--porcelain", "--", w.rel).splitlines()
                              if "/evals/" not in l])

    # G2: validator activity
    logp = repo_root() / ".git" / "wk" / "validator-log.jsonl"
    if logp.exists():
        rows = [json.loads(l) for l in logp.read_text().splitlines() if l.strip()]
        rows = [r for r in rows if r.get("world") == w.name]
        m["validator_runs"] = len(rows)
        m["validator_rejections"] = sum(not r.get("ok") for r in rows)
    m["hook_installed"] = (repo_root() / ".git" / "hooks" / "pre-commit").exists()

    # G11
    m["fork_bleed"] = fork_bleed(w)

    # player input
    m["notes"] = [e.get("text") for e in entries if e.get("type") == "NOTE"]
    rates = [e.get("scores") for e in entries if e.get("type") == "RATE"]
    m["player_rating"] = rates[-1] if rates else None
    return m


def fork_bleed(w):
    tl = w.timeline()
    main = tl.get("main")
    if not main:
        return None
    refs = git("for-each-ref", "--format=%(refname:short)", f"refs/heads/fork/{w.name}/",
               check=False).split()
    if not refs:
        return 0

    def statements(ref):
        out = set()
        for f in ("facts", "precedents"):
            d = head_json(f"{w.rel}/.world/state/{f}.json", ref) or {}
            for x in d.get(f, []):
                out.add(x.get("statement") or x.get("ruling"))
        return out - {None}

    main_s = statements(main)
    bleed = 0
    for ref in refs:
        base = git("merge-base", main, ref, check=False).strip()
        if not base:
            continue
        bleed += len((statements(ref) - statements(base)) & main_s)
    return bleed


def cmd_metrics(a):
    w = World(a.world)
    m = compute_metrics(w, a.watch)
    out = json.dumps(m, indent=2)
    if a.write:
        if a.watch is None:
            raise SystemExit("--write needs --watch")
        d = w.dot / "evals"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"watch-{a.watch:03d}.metrics.json").write_text(out + "\n")
    print(out)


# ---------------------------------------------------------------- report

def meets(v, op, target):
    if v is None:
        return None
    return v <= target if op == "<=" else v >= target


def goal_verdicts(m, audit):
    v = {}
    for g in GOAL_IDS:
        checks = [meets(m.get(k), op, t) for k, gg, op, t in TARGETS if gg == g]
        checks = [c for c in checks if c is not None]
        score = ((audit or {}).get("goals", {}).get(g) or {}).get("score")
        if isinstance(score, (int, float)):
            checks.append(score >= 3)
        v[g] = "no data" if not checks else ("met" if all(checks) else "missed")
    return v


def cmd_report(a):
    w = World(a.world)
    n = a.watch
    sealed = w.dot / "evals"
    mp = sealed / f"watch-{n:03d}.metrics.json"
    m = json.loads(mp.read_text()) if mp.exists() else compute_metrics(w, n)
    ap = sealed / f"watch-{n:03d}.audit.json"
    audit = json.loads(ap.read_text()) if ap.exists() else None
    verdicts = goal_verdicts(m, audit)
    rating = m.get("player_rating") or {}

    lines = [f"# Watch {n:03d} — evaluation", "",
             f"World: {w.name} · harness `{m.get('harness')}` · turns: {m.get('turns')}"
             + ("" if audit else " · **no audit yet**"), "",
             "| Goal | Verdict | Metrics (target) | Audit | Player |", "|---|---|---|---|---|"]
    for g in GOAL_IDS:
        mets = [f"{k} {m.get(k)} ({op}{t})" for k, gg, op, t in TARGETS if gg == g]
        ag = ((audit or {}).get("goals", {}).get(g) or {})
        sc = ag.get("score", "—")
        lines.append(f"| {g} | {verdicts[g]} | {'; '.join(mets) or '—'} | {sc} | {rating.get(g, '—')} |")
    lines += ["", f"Other: attempts {m.get('attempts')} · objections {m.get('objections')} · "
                  f"precedents added {m.get('precedents_added')} · validator rejections "
                  f"{m.get('validator_rejections', 'n/a')} · hook installed {m.get('hook_installed')}"]
    if m.get("neglected_ids"):
        lines.append(f"Neglected in at least one 10-turn window: {', '.join(m['neglected_ids'])}")
    if audit:
        sr = audit.get("self_report", {})
        lines += ["", "## Self-report check",
                  f"Checked {sr.get('checked', 0)} TURN entries against the transcript: "
                  f"{len(sr.get('disagreements', []))} disagreements."]
        lines += ["", "## Findings"]
        hidden = 0
        for g in GOAL_IDS:
            for f in (audit.get("goals", {}).get(g) or {}).get("findings", []):
                if f.get("spoiler"):
                    hidden += 1
                    continue
                lines.append(f"- **{g}** {f.get('severity')} (turn {f.get('turn')}): {f.get('what')}")
        if hidden:
            lines.append(f"- {hidden} finding(s) withheld: they would reveal sealed truth.")
    if m.get("notes"):
        lines += ["", "## Your notes this watch"] + [f"- {t}" for t in m["notes"]]
    pub = w.path / "evals"
    pub.mkdir(exist_ok=True)
    (pub / f"watch-{n:03d}.md").write_text("\n".join(lines) + "\n")
    write_trend(w)
    print(f"wrote {w.rel}/evals/watch-{n:03d}.md and {w.rel}/evals/TREND.md")


def write_trend(w):
    sealed = w.dot / "evals"
    rows = []
    for mp in sorted(sealed.glob("watch-*.metrics.json")):
        m = json.loads(mp.read_text())
        ap = sealed / mp.name.replace(".metrics.", ".audit.")
        audit = json.loads(ap.read_text()) if ap.exists() else None
        v = goal_verdicts(m, audit)
        sym = {"met": "✓", "missed": "✗", "no data": "·"}
        rows.append(f"| {m.get('watch'):03d} | `{m.get('harness')}` | "
                    + " | ".join(sym[v[g]] for g in GOAL_IDS)
                    + f" | {m.get('player_address_share')} | {m.get('autonomy')} |")
    head = ["# Trend", "",
            "One row per watch. ✓ met · ✗ missed · · no data. A harness change shows up as a new "
            "version in the row after it (HARNESS_CHANGELOG.md).", "",
            "| Watch | Harness | " + " | ".join(GOAL_IDS) + " | player share | autonomy |",
            "|---|---|" + "---|" * len(GOAL_IDS) + "---|---|"]
    (w.path / "evals" / "TREND.md").write_text("\n".join(head + rows) + "\n")


# ---------------------------------------------------------------- stamp

def stamp():
    return git("log", "-1", "--format=%h", "--", "CLAUDE.md", "modules", "tools", check=False).strip() \
        or "unversioned"


def cmd_stamp(a):
    print(stamp())


# ---------------------------------------------------------------- timelines

def last_position(w):
    led = w.ledger()
    return (led[-1].get("watch", 0), led[-1].get("turn", 0)) if led else (0, 0)


def append_ledger(w, entry):
    with open(w.ledger_path(), "a") as f:
        f.write(json.dumps(entry) + "\n")


def require_clean():
    if not tree_clean():
        raise SystemExit("The working tree has uncommitted changes. Checkpoint first, then retry.")


def commit(msg):
    git("add", "-A")
    r = subprocess.run(["git", "commit", "-q", "-m", msg], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"commit failed:\n{r.stdout}{r.stderr}")


BLEED = ("\nEnd this session and open a fresh one. The conversation still remembers what the "
         "files no longer contain.")


def set_timeline(w, name):
    p = w.state / "clock.json"
    c = json.loads(p.read_text())
    c["timeline"] = name
    p.write_text(json.dumps(c, indent=2) + "\n")


def cmd_save(a):
    w = World(a.world)
    require_clean()
    tag = f"save/{w.name}/{a.name}"
    if git("tag", "--list", tag).strip():
        raise SystemExit(f"{tag} already exists; pick another name")
    wa, tu = last_position(w)
    append_ledger(w, {"watch": wa, "turn": tu, "type": "SAVE", "name": a.name})
    commit(f"{w.name}: save {a.name}")
    git("tag", tag)
    print(f"saved: {tag}")


def cmd_fork(a):
    w = World(a.world)
    require_clean()
    br = f"fork/{w.name}/{a.name}"
    git("checkout", "-q", "-b", br)
    set_timeline(w, a.name)
    wa, tu = last_position(w)
    append_ledger(w, {"watch": wa, "turn": tu, "type": "FORK", "name": a.name})
    commit(f"{w.name}: fork {a.name}")
    print(f"on fork {br}; main is untouched." + BLEED)


def cmd_holodeck(a):
    w = World(a.world)
    require_clean()
    main = w.timeline().get("main")
    if current_branch() != main:
        raise SystemExit(f"holodeck works from the main timeline ({main}); you are on {current_branch()}")
    tags = git("tag", "--list", f"save/{w.name}/*", "--merged", "HEAD",
               "--sort=-creatordate").split()
    if not tags:
        raise SystemExit("no save on this timeline to return to")
    stamp_ = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    br = f"fork/{w.name}/holodeck-{stamp_}"
    git("branch", br)
    git("reset", "-q", "--hard", tags[0])
    wa, tu = last_position(w)
    append_ledger(w, {"watch": wa, "turn": tu, "type": "HOLODECK", "fork": br, "from_save": tags[0]})
    commit(f"{w.name}: holodeck run moved to {br}")
    print(f"main reset to {tags[0]}; the run is kept on {br}." + BLEED)


def cmd_return(a):
    w = World(a.world)
    require_clean()
    main = w.timeline().get("main")
    if not main:
        raise SystemExit("timeline.json has no 'main'")
    git("checkout", "-q", main)
    print(f"back on main ({main})." + BLEED)


# ---------------------------------------------------------------- hooks

HOOK = """#!/bin/sh
# Installed by tools/wk.py install-hooks. Validates every structured world before a commit.
exec python3 "$(git rev-parse --show-toplevel)/tools/wk.py" validate --all --hook
"""


def cmd_install_hooks(a):
    d = Path(git("rev-parse", "--git-dir").strip())
    d = (d if d.is_absolute() else repo_root() / d) / "hooks"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "pre-commit"
    p.write_text(HOOK)
    os.chmod(p, 0o755)
    print(f"installed {p}")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(prog="wk", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate"); p.add_argument("world", nargs="?")
    p.add_argument("--all", action="store_true"); p.add_argument("--hook", action="store_true")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("next-id"); p.add_argument("world"); p.add_argument("kind", choices=ID_PREFIX)
    p.set_defaults(fn=cmd_next_id)

    p = sub.add_parser("metrics"); p.add_argument("world"); p.add_argument("--watch", type=int)
    p.add_argument("--write", action="store_true"); p.set_defaults(fn=cmd_metrics)

    p = sub.add_parser("report"); p.add_argument("world"); p.add_argument("--watch", type=int, required=True)
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("stamp"); p.set_defaults(fn=cmd_stamp)

    for name, fn in (("save", cmd_save), ("fork", cmd_fork)):
        p = sub.add_parser(name); p.add_argument("world"); p.add_argument("name"); p.set_defaults(fn=fn)
    for name, fn in (("holodeck", cmd_holodeck), ("return", cmd_return)):
        p = sub.add_parser(name); p.add_argument("world"); p.set_defaults(fn=fn)

    p = sub.add_parser("install-hooks"); p.set_defaults(fn=cmd_install_hooks)

    a = ap.parse_args()
    if a.cmd == "validate" and not a.all and not a.world:
        ap.error("validate needs a world path or --all")
    a.fn(a)


if __name__ == "__main__":
    main()
