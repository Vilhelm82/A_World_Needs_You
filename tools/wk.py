#!/usr/bin/env python3
"""wk: the Worldkeeper tool for structured worlds.

Validates world state, computes evaluation metrics, writes scorecards, and
manages timelines (save, fork, holodeck, return). Standard library only.

  python3 tools/wk.py validate worlds/enterprise
  python3 tools/wk.py validate --all              (what the pre-commit hook runs)
  python3 tools/wk.py next-id worlds/enterprise fact
  python3 tools/wk.py suspects worlds/enterprise --act A-012 --as yar
  python3 tools/wk.py lore worlds/enterprise "transporters can't beam through shields"
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
import ast
import math
import operator
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
VERDICTS = {"consistent", "diverged", "unsupported", "contradicts"}
OUTCOMES = {"done", "denied", "cost"}
VISIBILITY = {"open", "unwitnessed", "concealed"}
VALENCE = {"credit", "blame", "neutral"}
COMPETENCE = {"high", "medium", "low"}
PROJECT_KINDS = {"duty", "experiment", "personal", "covert", "other"}
STAGE_STATUS = {"todo", "doing", "done", "failed"}
PROJECT_STATUS = {"active", "paused", "done", "abandoned"}
LAYERS = {"rules", "history-pre", "history-post"}
ACCESS_KEYS = ("areas", "systems", "codes", "skills")
ROLE_SET = {"security", "captain", "ops", "medical", "engineering"}
POSTULATES = {"P1", "P2", "P3", "P4", "P5"}
HYP_STATUS = {"open", "surviving", "falsified"}
TEST_RESULTS = {"supported", "falsified", "inconclusive"}

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
    "LORECHECK": ["claim", "layer", "verdict", "cards", "divergence", "agent"],
    "REAUDIT": ["scope", "findings"],
    "CALC": ["expression", "result", "units", "purpose"],
    "WORLDTURN": ["steps"],
    "NOTE": ["text"],
    "RATE": ["scores"],
    "LAW": [], "ROLL": [], "REWOUND": [], "SAVE": [], "FORK": [], "RETURN": [], "HOLODECK": [],
    "WATCH": [],
}

ID_PREFIX = {"fact": "F", "precedent": "P", "trace": "T", "case": "C", "episode": "E", "premise": "R",
             "act": "A", "divergence": "D", "project": "J", "card": "K", "mechanism": "M",
             "hypothesis": "H"}

# Targets from modules/eval/GOALS.md. (metric, goal, op, value)
TARGETS = [
    ("objections_upheld", "G1", "<=", 0),
    ("lore_checked_rate", "G1", ">=", 1.0),
    ("player_address_share", "G4", "<=", 0.35),
    ("neglected_windows", "G4", "<=", 0),
    ("autonomy", "G5", ">=", 0.5),
    ("npc_initiative", "G5", ">=", 0.3),
    ("decided_without_player", "G5", ">=", 1),
    ("cases_isolated", "G7", ">=", 1.0),
    ("pool_ignored", "G7", "<=", 0),
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


def check_access(obj, where, rep):
    acc = obj.get("access")
    if need(acc, list(ACCESS_KEYS), where + " access", rep):
        for k in ACCESS_KEYS:
            if not isinstance(acc[k], list):
                rep.err(where, f"access.{k} must be a list")


def ledger_refs(entries):
    return {f"L:{e.get('watch')}:{e.get('turn')}" for e in entries}


def load_quiet(path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def compute_pool(w, act_id, reasoner):
    """Suspect pool for an act, from what the reasoner can know. Returns (pool, reasons) or
    (None, why) when the reasoner has no readable trace of the act."""
    s = w.state
    deeds = load_quiet(s / "deeds.json", {}) or {}
    acts = {a.get("id"): a for a in deeds.get("acts", [])}
    act = acts.get(act_id)
    if act is None:
        return None, f"no act {act_id}"
    soul = load_quiet(s / "crew" / reasoner / "soul.json")
    if soul is None:
        return None, f"no soul for reasoner {reasoner}"
    roles = set(soul.get("roles", []))
    queried = set()
    for c in deeds.get("cases", []):
        if c.get("investigator") == reasoner:
            queried |= set(c.get("known", []))

    def readable(tr):
        who = set(tr.get("who_can_read", []))
        return tr.get("id") in queried or "anyone" in who or reasoner in who or bool(roles & who)

    traces = deeds.get("traces", [])
    if not any(tr.get("act") == act_id and readable(tr) for tr in traces):
        return None, f"{reasoner} has no readable trace of {act_id}"

    people = {}
    for cid in w.crew_ids():
        sl = load_quiet(s / "crew" / cid / "soul.json", {}) or {}
        people[cid] = sl.get("access", {})
    pl = load_quiet(s / "player.json", {}) or {}
    people["player"] = pl.get("access", {})

    cons = act.get("constraints", {})
    means = cons.get("means", {})
    opp = cons.get("opportunity", {})
    win = opp.get("window")
    pool, reasons = [], {}
    for pid, acc in sorted(people.items()):
        if pid == reasoner:
            continue
        lacking = [f"{k}:{x}" for k in ACCESS_KEYS for x in means.get(k, []) if x not in acc.get(k, [])]
        if lacking:
            reasons[pid] = "lacks " + ", ".join(lacking)
            continue
        alibi = None
        if win:
            for tr in traces:
                tw = tr.get("window")
                if tr.get("type") == "location" and tr.get("subject") == pid and tw and readable(tr) \
                        and tr.get("where") != opp.get("where") and tw[0] <= win[0] and tw[1] >= win[1]:
                    alibi = tr.get("id")
                    break
        if alibi:
            reasons[pid] = f"placed elsewhere by {alibi}"
            continue
        pool.append(pid)
        reasons[pid] = "could have"
    return pool, reasons


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
    player = load(s / "player.json", rep)
    if player is not None and need(player, ["name", "rank", "post", "access", "location"],
                                   "player.json", rep):
        check_access(player, "player.json", rep)
    all_entries = w.ledger()
    lrefs = ledger_refs(all_entries)

    # crew
    changed = {(e.get("who"), str(e.get("field", "")).split(".")[0]) for e in added
               if e.get("type") == "CHANGED"}
    for cid in sorted(crew):
        where = f"crew/{cid}/soul.json"
        soul = load(s / "crew" / cid / "soul.json", rep)
        if soul is None:
            continue
        if not need(soul, ["id", "name", "rank", "post", "tier", "created_at", "persona", "regard",
                           "routing", "agenda", "relationships", "schedule", "location", "access",
                           "roles", "competence"], where, rep):
            continue
        check_access(soul, where, rep)
        for r in soul["roles"]:
            if r not in ROLE_SET:
                rep.err(where, f"role '{r}' not in {sorted(ROLE_SET)}")
        if (soul["competence"] or {}).get("deduction") not in COMPETENCE:
            rep.err(where, f"competence.deduction must be one of {sorted(COMPETENCE)}")
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
        # a later fact may reinterpret an earlier one (an instrument artifact, other conditions);
        # the earlier fact itself never changes
        all_fact_ids = {f.get("id") for f in facts["facts"] if isinstance(f, dict)}
        for i, f in enumerate(facts["facts"]):
            r = f.get("reinterprets") if isinstance(f, dict) else None
            if r is not None and (r == f.get("id") or r not in all_fact_ids):
                rep.err(f"facts.json[{i}]", f"reinterprets unknown fact '{r}'")
        old = head_json(f"{w.rel}/.world/state/facts.json") or {}
        cur = {f.get("id"): f for f in facts["facts"] if isinstance(f, dict)}
        for of in old.get("facts", []):
            if of.get("surfaced_at") is None:
                continue
            nf = cur.get(of["id"])
            if nf is None:
                rep.err("facts.json", f"surfaced fact {of['id']} was removed")
                continue
            for k in ("statement", "surfaced_at", "source", "created_at", "reinterprets"):
                if nf.get(k) != of.get(k):
                    rep.err("facts.json", f"surfaced fact {of['id']} changed field '{k}'")
            if not set(of.get("known_by", [])) <= set(nf.get("known_by", [])):
                rep.err("facts.json", f"surfaced fact {of['id']} lost a knower (known_by only grows)")

    fact_known = {f.get("id"): set(f.get("known_by", [])) for f in (facts or {}).get("facts", [])
                  if isinstance(f, dict)}
    fact_reinterprets = {f.get("id"): f.get("reinterprets") for f in (facts or {}).get("facts", [])
                         if isinstance(f, dict)}

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

    # divergence: every difference from canon traces back to something somebody did
    div = load(s / "divergence.json", rep)
    div_ids = set()
    if div is not None and need(div, ["divergences"], "divergence.json", rep):
        graph = {}
        for i, d in enumerate(div["divergences"]):
            where = f"divergence.json[{i}]"
            if not need(d, ["id", "canon", "branch", "parents", "at"], where, rep):
                continue
            if d["id"] in div_ids:
                rep.err(where, f"duplicate id {d['id']}")
            div_ids.add(d["id"])
            graph[d["id"]] = d["parents"]
        for did, parents in graph.items():
            if not parents:
                rep.err("divergence.json", f"{did} has no parents: every divergence needs a cause")
            for par in parents:
                if par.startswith("L:"):
                    if par not in lrefs:
                        rep.err("divergence.json", f"{did} cites {par}, which matches no ledger entry")
                elif par not in graph:
                    rep.err("divergence.json", f"{did} cites unknown parent {par}")

        def reaches_ledger(node, seen):
            if node in seen:
                return None  # cycle
            seen = seen | {node}
            ok = False
            for par in graph.get(node, []):
                if par.startswith("L:"):
                    ok = ok or par in lrefs
                elif par in graph:
                    r = reaches_ledger(par, seen)
                    if r is None:
                        return None
                    ok = ok or r
            return ok

        for did in graph:
            r = reaches_ledger(did, set())
            if r is None:
                rep.err("divergence.json", f"{did} is part of a cycle")
            elif not r:
                rep.err("divergence.json", f"{did} never reaches a ledger entry")
        old = head_text(f"{w.rel}/.world/state/divergence.json")
        if old:
            cur = {d.get("id"): d for d in div["divergences"] if isinstance(d, dict)}
            for od in json.loads(old).get("divergences", []):
                if cur.get(od.get("id")) != od:
                    rep.err("divergence.json", f"{od.get('id')} was edited or removed (append-only)")

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
                    elif st["status"] != "on_track":
                        c = st.get("cause")
                        if not c:
                            rep.err(where, f"trajectory[{j}] is '{st['status']}' with no cause")
                        elif not (c in div_ids or c in lrefs):
                            rep.err(where, f"trajectory[{j}] cause '{c}' is neither a divergence "
                                           "nor a ledger reference (L:watch:turn)")

    # deeds: acts, traces, cases
    dd = load(s / "deeds.json", rep)
    trace_ids, act_ids = set(), set()
    if dd is not None and need(dd, ["acts", "traces", "cases"], "deeds.json", rep):
        for i, a in enumerate(dd["acts"]):
            where = f"deeds.json acts[{i}]"
            if not need(a, ["id", "actor", "what", "at", "where", "visibility", "valence",
                            "constraints", "traces"], where, rep):
                continue
            act_ids.add(a["id"])
            if not valid_ref(a["actor"], crew, {"player"}):
                rep.err(where, f"actor '{a['actor']}' unknown")
            if a["visibility"] not in VISIBILITY:
                rep.err(where, f"visibility must be one of {sorted(VISIBILITY)}")
            if a["valence"] not in VALENCE:
                rep.err(where, f"valence must be one of {sorted(VALENCE)}")
            cons = a["constraints"] or {}
            for k in (cons.get("means") or {}):
                if k not in ACCESS_KEYS:
                    rep.err(where, f"constraints.means key '{k}' not in {list(ACCESS_KEYS)}")
            win = (cons.get("opportunity") or {}).get("window")
            if win is not None and not (isinstance(win, list) and len(win) == 2):
                rep.err(where, "constraints.opportunity.window must be [from, to]")
        for i, tr in enumerate(dd["traces"]):
            where = f"deeds.json traces[{i}]"
            if not need(tr, ["id", "type", "where", "who_can_read", "lasts", "created_at"], where, rep):
                continue
            trace_ids.add(tr["id"])
            if tr["type"] not in TRACE_TYPES:
                rep.err(where, f"type must be one of {sorted(TRACE_TYPES)}")
            for x in tr["who_can_read"]:
                if not valid_ref(x, crew, ROLES):
                    rep.err(where, f"who_can_read names unknown '{x}'")
            if tr["type"] == "location" and "subject" in tr \
                    and not valid_ref(tr["subject"], crew, {"player"}):
                rep.err(where, f"location subject '{tr['subject']}' unknown")
        for i, a in enumerate(dd["acts"]):
            for k in (a.get("traces") or []) if isinstance(a, dict) else []:
                if k not in trace_ids:
                    rep.err(f"deeds.json acts[{i}]", f"trace '{k}' does not exist")
        for tr in dd["traces"]:
            if isinstance(tr, dict) and tr.get("act") and tr["act"] not in act_ids:
                rep.err("deeds.json", f"trace {tr.get('id')} names unknown act {tr['act']}")
        old_cases = {c.get("case_id"): c for c in
                     (head_json(f"{w.rel}/.world/state/deeds.json") or {}).get("cases", [])}
        for i, c in enumerate(dd["cases"]):
            where = f"deeds.json cases[{i}]"
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
            runs = c.get("runs", [])
            n_old = len((old_cases.get(c["case_id"]) or {}).get("runs", []))
            for j, r in enumerate(runs):
                for k in r.get("cited", []):
                    if k not in c["known"]:
                        rep.err(where, f"run at turn {r.get('turn')} cites '{k}', outside the "
                                       "investigator's light cone")
                if j < n_old:
                    continue
                if not need(r, ["watch", "turn", "act", "isolated", "cited", "pool", "suspects"],
                            f"{where} runs[{j}]", rep):
                    continue
                pool, why = compute_pool(w, r["act"], c["investigator"])
                if pool is None:
                    rep.err(where, f"runs[{j}]: {why}")
                elif sorted(pool) != sorted(r["pool"]):
                    rep.err(where, f"runs[{j}] pool {sorted(r['pool'])} does not match the computed "
                                   f"pool {sorted(pool)} (python3 tools/wk.py suspects)")

    # projects
    pj = load(s / "projects.json", rep)
    if pj is not None and need(pj, ["projects"], "projects.json", rep):
        prec_ids = {x.get("id") for x in (prec or {}).get("precedents", [])} if prec else set()
        for i, pr in enumerate(pj["projects"]):
            where = f"projects.json[{i}]"
            if not need(pr, ["id", "title", "owner", "collaborators", "kind", "goal", "stages",
                             "status", "precedents", "started_at"], where, rep):
                continue
            for x in [pr["owner"]] + list(pr["collaborators"]):
                if not valid_ref(x, crew, {"player"}):
                    rep.err(where, f"names unknown '{x}'")
            if pr["kind"] not in PROJECT_KINDS:
                rep.err(where, f"kind must be one of {sorted(PROJECT_KINDS)}")
            if pr["status"] not in PROJECT_STATUS:
                rep.err(where, f"status must be one of {sorted(PROJECT_STATUS)}")
            for j, st in enumerate(pr["stages"]):
                if need(st, ["name", "status", "needs", "cost"], f"{where} stages[{j}]", rep) \
                        and st["status"] not in STAGE_STATUS:
                    rep.err(where, f"stages[{j}] status must be one of {sorted(STAGE_STATUS)}")
            for x in pr["precedents"]:
                if x not in prec_ids:
                    rep.err(where, f"precedent '{x}' does not exist")

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
            elif t in ("OBJECTION", "LORECHECK") and e.get("verdict") not in VERDICTS:
                rep.err(where, f"verdict must be one of {sorted(VERDICTS)}")
            elif t == "SAID" and e.get("fact"):
                kb = fact_known.get(e["fact"])
                by = e.get("by")
                if kb is None:
                    rep.err(where, f"SAID cites unknown fact '{e['fact']}'")
                elif isinstance(by, str) and by.startswith("crowd:") and "all" not in kb:
                    rep.err(where, f"{by} cites {e['fact']}, which the crowd can't know")
                elif by in crew and by not in kb and "all" not in kb:
                    rep.err(where, f"{by} cites {e['fact']}, which isn't in their knowledge (known_by)")
            elif t == "ATTEMPT" and e.get("outcome") not in OUTCOMES:
                rep.err(where, f"outcome must be one of {sorted(OUTCOMES)}")
            elif t == "TOLD" and fact_ids and e.get("fact") not in fact_ids:
                rep.err(where, f"TOLD fact '{e.get('fact')}' does not exist")
            if t == "LORECHECK" and e.get("layer") not in LAYERS:
                rep.err(where, f"layer must be one of {sorted(LAYERS)}")
            elif t == "PRECEDENT" and prec and e.get("id") not in {p.get("id") for p in prec.get("precedents", [])}:
                rep.err(where, f"PRECEDENT '{e.get('id')}' does not exist")

    # unknowns: black boxes with an observation record
    pd = preset_dir(w)
    card_ids = set()
    if pd and (pd / "canon" / "cards.jsonl").exists():
        for l in (pd / "canon" / "cards.jsonl").read_text().splitlines():
            if l.strip():
                try:
                    card_ids.add(json.loads(l).get("id"))
                except json.JSONDecodeError:
                    pass
    un = load(s / "unknowns.json", rep)
    unknown_ids = set()
    if un is not None and need(un, ["unknowns"], "unknowns.json", rep):
        for i, u in enumerate(un["unknowns"]):
            where = f"unknowns.json[{i}]"
            if not need(u, ["id", "subject", "canon_record", "observations"], where, rep):
                continue
            unknown_ids.add(u["id"])
            for k in u["canon_record"]:
                if k not in card_ids:
                    rep.err(where, f"canon_record card '{k}' does not exist")
            for f_ in u["observations"]:
                if f_ not in fact_known:
                    rep.err(where, f"observation fact '{f_}' does not exist")
            if any(k in u for k in ("explanation", "truth", "mechanism")):
                rep.err(where, "an unknown holds observations only, never an explanation")

    # hypotheses: survive, never crowned; falsified is permanent
    hy = load(s / "hypotheses.json", rep)
    if hy is not None and need(hy, ["hypotheses"], "hypotheses.json", rep):
        old_h = {h.get("id"): h for h in
                 (head_json(f"{w.rel}/.world/state/hypotheses.json") or {}).get("hypotheses", [])}
        cur_ids = set()
        by_id = {h.get("id"): h for h in hy["hypotheses"] if isinstance(h, dict)}
        for i, h in enumerate(hy["hypotheses"]):
            where = f"hypotheses.json[{i}]"
            if not need(h, ["id", "subject", "statement", "proposed_by", "held_by", "physics_basis",
                            "predictions", "tests", "status", "created_at"], where, rep):
                continue
            cur_ids.add(h["id"])
            for x in [h["proposed_by"]] + list(h["held_by"]):
                if not valid_ref(x, crew, {"player"}):
                    rep.err(where, f"names unknown '{x}'")
            if h["status"] not in HYP_STATUS:
                rep.err(where, f"status must be one of {sorted(HYP_STATUS)}")
            preds = {pr.get("id") for pr in h["predictions"] if isinstance(pr, dict)}
            results = []
            for j, te in enumerate(h["tests"]):
                if not need(te, ["prediction", "via", "observation", "result"], f"{where} tests[{j}]", rep):
                    continue
                if te["prediction"] not in preds:
                    rep.err(where, f"tests[{j}] names unknown prediction '{te['prediction']}'")
                if te["observation"] not in fact_known:
                    rep.err(where, f"tests[{j}] cites observation '{te['observation']}', which isn't a fact")
                if te["result"] not in TEST_RESULTS:
                    rep.err(where, f"tests[{j}] result must be one of {sorted(TEST_RESULTS)}")
                results.append(te["result"])
            if "falsified" in results and h["status"] != "falsified":
                rep.err(where, "a test falsified it, so its status must be 'falsified'")
            if h["status"] == "surviving" and "supported" not in results:
                rep.err(where, "'surviving' needs at least one supported test")
            if h["status"] == "falsified" and "falsified" not in results:
                rep.err(where, "'falsified' needs a falsifying test")
            # a new hypothesis may revive a falsified one, but only through a fact that
            # reinterprets an observation that falsified it
            rv = h.get("revives")
            if rv is not None:
                old_one = by_id.get(rv.get("hypothesis")) if isinstance(rv, dict) else None
                if old_one is None or old_one.get("id") == h["id"]:
                    rep.err(where, "revives must name another hypothesis by id")
                elif old_one.get("status") != "falsified":
                    rep.err(where, f"revives {old_one['id']}, which isn't falsified")
                else:
                    killers = {te.get("observation") for te in old_one.get("tests", [])
                               if isinstance(te, dict) and te.get("result") == "falsified"}
                    via = rv.get("via")
                    if via not in fact_known or fact_reinterprets.get(via) not in killers:
                        rep.err(where, f"revives {old_one['id']} only via a fact that reinterprets "
                                       f"an observation that falsified it")
            oh = old_h.get(h["id"])
            if oh:
                if oh.get("status") == "falsified" and h["status"] != "falsified":
                    rep.err(where, "a falsified hypothesis stays falsified; propose a new one instead")
                if h["tests"][:len(oh.get("tests", []))] != oh.get("tests", []):
                    rep.err(where, "tests are append-only")
                if oh.get("statement") != h["statement"]:
                    rep.err(where, "a hypothesis's statement never changes; propose a refined one instead")
                if oh.get("revives") != h.get("revives"):
                    rep.err(where, "what a hypothesis revives never changes")
        for hid in old_h:
            if hid not in cur_ids:
                rep.err("hypotheses.json", f"hypothesis {hid} was removed")

    # entries added in this commit: TOLD updates knowledge; lore touches are checked
    for e in added:
        if e.get("type") == "TOLD" and e.get("fact") in fact_known:
            kb = fact_known[e["fact"]]
            for x in e.get("to", []):
                if x in crew and x not in kb and "all" not in kb:
                    rep.err("ledger.jsonl", f"TOLD {e['fact']} to {x}, but {x} isn't added to its known_by")
    for e in added:
        if e.get("type") == "CALC":
            try:
                v = safe_eval(str(e.get("expression")))
                r = float(e.get("result"))
                if abs(v - r) > 1e-6 * max(1.0, abs(v)):
                    rep.err("ledger.jsonl", f"CALC {e.get('expression')} = {v:.6g}, not {r:.6g}")
            except Exception as ex:  # noqa: BLE001
                rep.err("ledger.jsonl", f"CALC {e.get('expression')!r} can't be checked: {ex}")
        if e.get("type") == "ROLL" and "outcomes" in e:
            oc, roll = e.get("outcomes") or [], e.get("roll")
            if not isinstance(roll, int) or not 1 <= roll <= len(oc):
                rep.err("ledger.jsonl", f"ROLL {roll} is outside its {len(oc)} written outcomes")
            elif e.get("result") != oc[roll - 1]:
                rep.err("ledger.jsonl", f"ROLL {roll} names outcome {oc[roll - 1]!r} but records "
                                        f"{e.get('result')!r}")
    touches, checks = {}, {}
    for e in added:
        key = (e.get("watch"), e.get("turn"))
        if e.get("type") == "TURN":
            touches[key] = touches.get(key, 0) + len(e.get("lore_touch") or [])
        elif e.get("type") == "LORECHECK":
            checks[key] = checks.get(key, 0) + 1
    for key, n in touches.items():
        if checks.get(key, 0) < n:
            rep.err("ledger.jsonl", f"turn {key[1]} touched lore {n} time(s) but has "
                                    f"{checks.get(key, 0)} LORECHECK entr(ies)")

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


def validate_canon(root):
    """modules/*/canon/cards.jsonl: cited, layered, append-only."""
    rep = Report()
    for cp in sorted(root.glob("modules/*/canon/cards.jsonl")):
        rel = cp.relative_to(root).as_posix()
        cur = cp.read_text()
        old = head_text(rel)
        if old is not None and not cur.startswith(old):
            rep.err(rel, "is append-only: verified cards are never edited; supersede them instead")
        ids = set()
        for n, line in enumerate(cur.splitlines(), 1):
            if not line.strip():
                continue
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                rep.err(rel, f"line {n} is not valid JSON")
                continue
            where = f"{rel} line {n}"
            if not need(c, ["id", "layer", "topic", "statement", "sources", "verified_at", "supersedes"],
                        where, rep):
                continue
            if c["id"] in ids:
                rep.err(where, f"duplicate id {c['id']}")
            ids.add(c["id"])
            if c["layer"] not in LAYERS:
                rep.err(where, f"layer must be one of {sorted(LAYERS)}")
            if not c["sources"]:
                rep.err(where, "a card needs at least one source")
            if c["supersedes"] and c["supersedes"] not in ids:
                rep.err(where, f"supersedes unknown or later card {c['supersedes']}")
    for mp in sorted(root.glob("modules/*/canon/mechanisms.jsonl")):
        rel = mp.relative_to(root).as_posix()
        cur = mp.read_text()
        old = head_text(rel)
        if old is not None and not cur.startswith(old):
            rep.err(rel, "is append-only: verified mechanism cards are never edited; supersede them")
        ids = set()
        for n, line in enumerate(cur.splitlines(), 1):
            if not line.strip():
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                rep.err(rel, f"line {n} is not valid JSON")
                continue
            where = f"{rel} line {n}"
            if not need(m, ["id", "tech", "canon_capabilities", "canon_limits", "physics_basis",
                            "postulates", "engineering_gap", "budgets", "failure_modes", "sources",
                            "verified_at", "supersedes"], where, rep):
                continue
            if m["id"] in ids:
                rep.err(where, f"duplicate id {m['id']}")
            ids.add(m["id"])
            bad = set(m["postulates"]) - POSTULATES
            if bad:
                rep.err(where, f"postulates {sorted(bad)} are not in the closed list {sorted(POSTULATES)}")
            if not m["sources"]:
                rep.err(where, "a mechanism card needs at least one source")
            for b in m["budgets"]:
                basis = str(b.get("basis", ""))
                if not basis.startswith("CALC:"):
                    rep.err(where, f"budget '{b.get('quantity')}' isn't computed (basis must be 'CALC: <expr>')")
                    continue
                try:
                    safe_eval(basis[5:].strip())
                except Exception as ex:  # noqa: BLE001
                    rep.err(where, f"budget '{b.get('quantity')}' expression doesn't evaluate: {ex}")
            if m["supersedes"] and m["supersedes"] not in ids:
                rep.err(where, f"supersedes unknown or later card {m['supersedes']}")
    return rep


def cmd_validate(a):
    worlds = all_structured_worlds() if a.all else [World(a.world)]
    bad = 0
    crep = validate_canon(repo_root())
    for m in crep.errors:
        print(f"ERROR    canon: {m}")
    bad += bool(crep.errors)
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


# ---------------------------------------------------------------- calc

CONSTANTS = {
    "c": 299792458.0, "G": 6.67430e-11, "h": 6.62607015e-34, "hbar": 1.054571817e-34,
    "kB": 1.380649e-23, "e": 1.602176634e-19, "me": 9.1093837015e-31, "mp": 1.67262192369e-27,
    "NA": 6.02214076e23, "ly": 9.4607304725808e15, "au": 1.495978707e11, "pc": 3.0856775814913673e16,
    "year": 31557600.0, "day": 86400.0, "hour": 3600.0, "pi": math.pi, "tau": math.tau,
    "euler": math.e,
}
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {n: getattr(math, n) for n in ("sqrt", "exp", "log", "log10", "log2", "sin", "cos", "tan",
                                         "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh",
                                         "hypot", "radians", "degrees", "floor", "ceil")}
_FUNCS.update({"abs": abs, "min": min, "max": max, "round": round})


def safe_eval(expr):
    """Arithmetic, physical constants and math functions only."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name) and n.id in CONSTANTS:
            return CONSTANTS[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS \
                and not n.keywords:
            return _FUNCS[n.func.id](*[ev(a) for a in n.args])
        raise ValueError(f"not allowed in a calculation: {ast.dump(n)[:60]}")
    return ev(ast.parse(expr, mode="eval"))


def cmd_calc(a):
    v = safe_eval(a.expression)
    print(json.dumps({"expression": a.expression, "result": v, "result_text": f"{v:.6g}"}))


# ---------------------------------------------------------------- suspects

def cmd_suspects(a):
    w = World(a.world)
    pool, reasons = compute_pool(w, a.act, a.reasoner)
    if pool is None:
        print(json.dumps({"act": a.act, "as": a.reasoner, "pool": None, "why": reasons}, indent=2))
        return
    print(json.dumps({"act": a.act, "as": a.reasoner, "pool": pool, "reasons": reasons}, indent=2))


# ---------------------------------------------------------------- lore

STOP = set("""the a an and or of to in on at for with by from is are was were be been it its this that
these those as not no can can't cannot could would should will may might than then there their they
them who what when where which while into onto over under about does do did has have had any all
some such only also very more most other""".split())


def tokens(text):
    return {x for x in re.findall(r"[a-z][a-z'-]{2,}", str(text).lower()) if x not in STOP}


def preset_dir(w):
    ch = (w.path / "charter.md")
    if ch.exists():
        m = re.search(r"^preset:\s*(\S+)", ch.read_text(), flags=re.M)
        if m:
            return w.root / m.group(1)
    return None


def lore_search(w, claim, top=5):
    q = tokens(claim)
    found = {"cards": [], "mechanisms": [], "law": [], "precedents": [], "divergences": []}
    pd = preset_dir(w)
    if pd:
        cp = pd / "canon" / "cards.jsonl"
        if cp.exists():
            cards = [json.loads(l) for l in cp.read_text().splitlines() if l.strip()]
            superseded = {c.get("supersedes") for c in cards if c.get("supersedes")}
            for c in cards:
                if c.get("id") in superseded:
                    continue
                sc = len(q & tokens(c.get("topic", "") + " " + c.get("statement", "")))
                if sc:
                    found["cards"].append((sc, {k: c.get(k) for k in
                                                ("id", "layer", "topic", "statement", "sources")}))
        mp = pd / "canon" / "mechanisms.jsonl"
        if mp.exists():
            mechs = [json.loads(l) for l in mp.read_text().splitlines() if l.strip()]
            sup = {m.get("supersedes") for m in mechs if m.get("supersedes")}
            for m in mechs:
                if m.get("id") in sup:
                    continue
                text = " ".join([m.get("tech", ""), " ".join(m.get("canon_capabilities", [])),
                                 " ".join(m.get("canon_limits", [])), m.get("physics_basis", ""),
                                 " ".join(m.get("failure_modes", []))])
                sc = len(q & tokens(text)) + 2 * len(q & tokens(m.get("tech", "")))
                if sc:
                    found["mechanisms"].append((sc, {k: m.get(k) for k in
                                                     ("id", "tech", "postulates", "canon_limits",
                                                      "physics_basis", "sources")}))
        lp = pd / "law.md"
        if lp.exists():
            for n, line in enumerate(lp.read_text().splitlines(), 1):
                if line.strip().startswith("-"):
                    sc = len(q & tokens(line))
                    if sc:
                        found["law"].append((sc, {"line": n, "text": line.strip()}))
    for x in (load_quiet(w.state / "precedents.json", {}) or {}).get("precedents", []):
        sc = len(q & tokens(x.get("ruling", "") + " " + x.get("reason", "")))
        if sc:
            found["precedents"].append((sc, x))
    for x in (load_quiet(w.state / "divergence.json", {}) or {}).get("divergences", []):
        sc = len(q & tokens(x.get("canon", "") + " " + x.get("branch", "")))
        if sc:
            found["divergences"].append((sc, x))
    out = {}
    for k, v in found.items():
        v.sort(key=lambda p: -p[0])
        out[k] = [dict(score=s, **item) for s, item in v[:top]]
    best = max([r["score"] for k in ("cards", "mechanisms", "law", "precedents") for r in out[k]] or [0])
    out["coverage"] = "covered" if best >= 2 else ("thin" if best == 1 else "none")
    return out


def cmd_lore(a):
    w = World(a.world)
    res = lore_search(w, a.claim)
    res["claim"] = a.claim
    if res["coverage"] != "covered":
        res["next"] = ("No solid coverage. Spawn a fresh lore agent with modules/eval/LORE_AGENT.md, "
                       "passing this claim, this output and the world path. Record its verdict as a "
                       "LORECHECK with agent: true, and add any verified card it returns.")
    else:
        res["next"] = ("Read the matches. Rules layer: does the claim obey them? History after the "
                       "branch: does it follow from this branch's state and divergences? Record a "
                       "LORECHECK.")
    print(json.dumps(res, indent=2))


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
    runs = total = ignored = 0
    dd = load_quiet(w.state / "deeds.json", {}) or {}
    for c in dd.get("cases", []):
        comp = ((load_quiet(w.state / "crew" / c.get("investigator", "") / "soul.json", {}) or {})
                .get("competence") or {}).get("deduction")
        for r in c.get("runs", []):
            if watch is None or r.get("watch") == watch:
                total += 1
                runs += bool(r.get("isolated"))
                pool = r.get("pool") or []
                if comp in ("high", "medium") and len(pool) == 1 and pool[0] not in r.get("suspects", []):
                    ignored += 1
    m["cases_isolated"] = ratio(runs, total)
    m["pool_ignored"] = ignored if total else None

    # G1: lore checks and divergence
    touches = sum(len(t.get("lore_touch") or []) for t in turns)
    checks = [e for e in entries if e.get("type") == "LORECHECK"]
    m["lore_checked_rate"] = ratio(min(len(checks), touches), touches)
    m["lore_checks"] = {k: sum(e.get("verdict") == k for e in checks) for k in sorted(VERDICTS)}
    m["lore_agent_calls"] = sum(bool(e.get("agent")) for e in checks)
    m["divergences"] = len((load_quiet(w.state / "divergence.json", {}) or {}).get("divergences", []))
    last_re = max([e.get("watch", 0) for e in led if e.get("type") == "REAUDIT"] or [0])
    prec_since = sum(1 for e in led if e.get("type") == "PRECEDENT" and e.get("watch", 0) > last_re)
    cur_watch = max([e.get("watch", 0) for e in led] or [0])
    m["reaudit_due"] = (cur_watch - last_re >= 5) or prec_since >= 10
    m["calcs"] = sum(e.get("type") == "CALC" for e in entries)
    m["rolls"] = sum(e.get("type") == "ROLL" for e in entries)
    hyps = (load_quiet(w.state / "hypotheses.json", {}) or {}).get("hypotheses", [])
    m["hypotheses"] = {k: sum(h.get("status") == k for h in hyps) for k in sorted(HYP_STATUS)}

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

    p = sub.add_parser("calc"); p.add_argument("expression"); p.set_defaults(fn=cmd_calc)

    p = sub.add_parser("suspects"); p.add_argument("world"); p.add_argument("--act", required=True)
    p.add_argument("--as", dest="reasoner", required=True); p.set_defaults(fn=cmd_suspects)

    p = sub.add_parser("lore"); p.add_argument("world"); p.add_argument("claim")
    p.set_defaults(fn=cmd_lore)

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
