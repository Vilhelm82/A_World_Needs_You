#!/usr/bin/env python3
"""Regression tests for tools/wk.py. Builds a throwaway repo with a tiny world and
checks that valid changes commit, invalid ones are refused, metrics compute, and
timelines behave. Run: python3 tools/test_wk.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAILS = []


def sh(*args, cwd, ok=True):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    if ok and r.returncode != 0:
        raise AssertionError(f"{' '.join(args)} failed:\n{r.stdout}{r.stderr}")
    return r


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"\n     {detail}"))
    if not cond:
        FAILS.append(name)


def soul(cid, tier="canon", routing=None):
    return {"id": cid, "name": cid.title(), "rank": "Lt", "post": "ops", "tier": tier,
            "created_at": "41153.7",
            "persona": {"values": ["duty"], "traits": ["precise"], "tired_of": "x",
                        "wrong_about": "y", "cares_about": "z"},
            "regard": {"gives_freely": ["candour"], "gives_rarely": ["praise"], "toward": {}},
            "routing": routing or {"ship": ["player"]},
            "agenda": [{"goal": "g", "next_step": "s", "horizon": "week"}],
            "relationships": {}, "schedule": {"duty": "alpha"}, "location": "bridge"}


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n" if not isinstance(obj, str) else obj)


def build(repo):
    w = repo / "worlds" / "test"
    s = w / ".world" / "state"
    write(w / "charter.md", "# Charter — test\n")
    write(w / ".world" / "timeline.json", {"main": "main"})
    write(s / "clock.json", {"stardate": 41153.7, "ship_time": "08:00", "day": 1, "alert": "normal",
                             "location": "Farpoint", "episode_open": None, "timeline": "main"})
    write(s / "ship.json", {"course": "none", "orders": [], "systems": {}})
    for cid in ("picard", "data", "yar"):
        write(s / "crew" / cid / "soul.json", soul(cid))
        write(s / "crew" / cid / "memory.json", {"learned": [], "beliefs": [], "recent": []})
    write(s / "facts.json", {"facts": [
        {"id": "F-001", "statement": "The Enterprise left Farpoint.", "known_by": ["all"],
         "surfaced_at": "41153.7", "source": "build", "created_at": "41153.7"},
        {"id": "F-002", "statement": "A hidden thing.", "known_by": ["yar"],
         "surfaced_at": None, "source": "build", "created_at": "41153.7"}]})
    write(s / "precedents.json", {"precedents": [
        {"id": "P-001", "ruling": "Replicator logs exist.", "kind": "tech", "reason": "lore",
         "source": "build", "created_at": "41153.7"}]})
    write(s / "forces.json", {"forces": [{"id": "q", "state": "watching", "wants": "test",
                                          "capabilities": "all", "trajectory": [
                                              {"step": "return", "preconditions": "quiet",
                                               "status": "on_track"}]}]})
    write(s / "evidence.json", {"traces": [], "cases": []})
    write(s / "premises.json", {"premises": []})
    write(s / "pins.json", {"pins": []})
    write(w / ".world" / "ledger.jsonl", json.dumps({"watch": 1, "turn": 0, "type": "WATCH"}) + "\n")
    return w


def turn(n, present, speakers, addressed, initiated=()):
    return {"watch": 1, "turn": n, "type": "TURN", "stardate": 41153.8, "present": present,
            "speakers": speakers, "addressed": addressed, "initiated": list(initiated),
            "transcript": f"watch-001.md#turn-{n}"}


def append(w, *entries):
    with open(w / ".world" / "ledger.jsonl", "a") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def commit(repo, msg, ok=True):
    sh("git", "add", "-A", cwd=repo)
    r = sh("git", "commit", "-q", "-m", msg, cwd=repo, ok=False)
    return r.returncode == 0, r.stdout + r.stderr


def main():
    tmp = Path(tempfile.mkdtemp(prefix="wk-test-"))
    repo = tmp / "repo"
    repo.mkdir()
    try:
        sh("git", "init", "-q", "-b", "main", cwd=repo)
        sh("git", "config", "user.email", "t@t", cwd=repo)
        sh("git", "config", "user.name", "t", cwd=repo)
        shutil.copytree(HERE, repo / "tools")
        (repo / "CLAUDE.md").write_text("harness\n")
        w = build(repo)
        wk = ["python3", "tools/wk.py"]
        sh(*wk, "install-hooks", cwd=repo)

        ok, out = commit(repo, "build")
        check("valid world commits", ok, out)

        # surfaced fact edited -> refused
        f = w / ".world/state/facts.json"
        good = f.read_text()
        d = json.loads(good); d["facts"][0]["statement"] = "Something else."
        f.write_text(json.dumps(d))
        ok, out = commit(repo, "edit surfaced")
        check("editing a surfaced fact is refused", not ok and "surfaced fact F-001" in out, out)
        f.write_text(good)

        # unsurfaced fact may be deepened
        d = json.loads(good); d["facts"][1]["statement"] = "A hidden thing, deeper."
        f.write_text(json.dumps(d, indent=2))
        ok, out = commit(repo, "deepen unsurfaced")
        check("an unsurfaced fact may be revised", ok, out)

        # ledger rewrite -> refused
        lp = w / ".world/ledger.jsonl"
        before = lp.read_text()
        lp.write_text(json.dumps({"watch": 1, "turn": 0, "type": "WATCH", "x": 1}) + "\n")
        ok, out = commit(repo, "rewrite ledger")
        check("rewriting the ledger is refused", not ok and "append-only" in out, out)
        lp.write_text(before)

        # unknown speaker -> refused
        append(w, turn(1, ["picard", "data"], ["ghost"], {"player": 1}))
        ok, out = commit(repo, "ghost")
        check("an unknown speaker is refused", not ok and "unknown 'ghost'" in out, out)
        lp.write_text(before)

        # persona change without CHANGED -> refused; with CHANGED -> allowed
        sp = w / ".world/state/crew/data/soul.json"
        sd = json.loads(sp.read_text()); sd["persona"]["traits"] = ["warmer"]
        sp.write_text(json.dumps(sd, indent=2))
        ok, out = commit(repo, "persona drift")
        check("a persona change without a cause is refused", not ok and "persona changed" in out, out)
        append(w, {"watch": 1, "turn": 1, "type": "CHANGED", "who": "data", "field": "persona.traits",
                   "cause": "ledger turn 1: saved a child"})
        ok, out = commit(repo, "persona with cause")
        check("a persona change with a CHANGED entry commits", ok, out)

        # precedent edited -> refused
        pp = w / ".world/state/precedents.json"
        pd = json.loads(pp.read_text()); pd["precedents"][0]["ruling"] = "No logs."
        pp.write_text(json.dumps(pd)); ok, out = commit(repo, "edit precedent")
        check("editing a precedent is refused", not ok and "append-only" in out, out)
        sh("git", "reset", "-q", "--hard", cwd=repo)

        # stardate backwards -> refused
        cp = w / ".world/state/clock.json"
        cd = json.loads(cp.read_text()); cd["stardate"] = 41100.0
        cp.write_text(json.dumps(cd)); ok, out = commit(repo, "time travel")
        check("the clock going backwards is refused", not ok and "backwards" in out, out)
        sh("git", "reset", "-q", "--hard", cwd=repo)

        # investigator citing a trace outside its light cone -> refused
        ep = w / ".world/state/evidence.json"
        ep.write_text(json.dumps({"traces": [
            {"id": "T-001", "type": "replicator", "where": "deck 8", "who_can_read": ["security"],
             "lasts": "permanent", "created_at": "41153.8"},
            {"id": "T-002", "type": "witness", "where": "crowd:ensign", "who_can_read": ["anyone"],
             "lasts": "memory", "created_at": "41153.8"}],
            "cases": [{"case_id": "C-001", "investigator": "yar", "trigger": "x", "known": ["T-001"],
                       "next_step": "query", "status": "open",
                       "runs": [{"watch": 1, "turn": 2, "isolated": True, "cited": ["T-002"]}]}]}))
        ok, out = commit(repo, "leaky investigator")
        check("an investigator citing outside its light cone is refused",
              not ok and "outside the investigator's light cone" in out, out)
        d = json.loads(ep.read_text()); d["cases"][0]["runs"][0]["cited"] = ["T-001"]
        ep.write_text(json.dumps(d, indent=2))
        ok, out = commit(repo, "evidence")
        check("an investigator citing its own light cone commits", ok, out)

        # metrics: 12 turns where the player is addressed heavily and yar is neglected
        tdir = w / ".world/transcript"; tdir.mkdir(exist_ok=True)
        entries, text = [], ""
        for n in range(2, 14):
            entries.append(turn(n, ["picard", "data", "yar"], ["picard", "data"],
                                {"player": 3, "data": 1}, initiated=["data"] if n % 2 else []))
            text += f"## turn {n}\n...\n"
        entries += [{"watch": 1, "turn": 13, "type": "MOVED", "by": "q", "what": "x", "cause": "force:q"},
                    {"watch": 1, "turn": 13, "type": "MOVED", "by": "player", "what": "y", "cause": "player"},
                    {"watch": 1, "turn": 13, "type": "DECIDED", "by": "picard", "what": "z",
                     "without_player": True}]
        append(w, *entries)
        (tdir / "watch-001.md").write_text(text)
        ok, out = commit(repo, "play")
        check("a turn of play commits", ok, out)
        m = json.loads(sh(*wk, "metrics", "worlds/test", "--watch", "1", "--write", cwd=repo).stdout)
        check("address share computed", m["player_address_share"] == 0.75, m["player_address_share"])
        check("neglected officer detected", m["neglected_ids"] == ["yar"] and m["neglected_windows"] == 3,
              (m["neglected_ids"], m["neglected_windows"]))
        check("autonomy computed", m["autonomy"] == 0.5, m["autonomy"])
        check("investigator isolation computed", m["cases_isolated"] == 1.0, m["cases_isolated"])
        check("parity computed", m["parity"] == 1.0, m["parity"])

        # report with an audit containing a spoiler finding
        audit = {"watch": 1, "self_report": {"checked": 5, "disagreements": []},
                 "goals": {"G4": {"score": 2, "findings": [
                     {"severity": "major", "turn": 5, "what": "Picard routed engineering to the XO.",
                      "evidence": "t5", "spoiler": False},
                     {"severity": "minor", "turn": 6, "what": "Yar knew the hidden thing.",
                      "evidence": "t6", "spoiler": True}]}}, "proposals": []}
        write(w / ".world/evals/watch-001.audit.json", audit)
        sh(*wk, "report", "worlds/test", "--watch", "1", cwd=repo)
        rep = (w / "evals/watch-001.md").read_text()
        check("report marks G4 missed", "| G4 | missed |" in rep, rep)
        check("report hides spoiler findings", "hidden thing" not in rep and "1 finding(s) withheld" in rep, rep)
        check("trend written", (w / "evals/TREND.md").exists())
        ok, out = commit(repo, "eval")

        # timelines
        sh(*wk, "save", "worlds/test", "start", cwd=repo)
        check("save tags", "save/test/start" in sh("git", "tag", cwd=repo).stdout)
        sh(*wk, "fork", "worlds/test", "ale", cwd=repo)
        check("fork switches branch", sh("git", "branch", "--show-current", cwd=repo).stdout.strip()
              == "fork/test/ale")
        fd = json.loads(f.read_text())
        fd["facts"].append({"id": "F-003", "statement": "Lloyd shot a security officer.",
                            "known_by": ["all"], "surfaced_at": "41160.0", "source": "fork",
                            "created_at": "41160.0"})
        f.write_text(json.dumps(fd, indent=2)); commit(repo, "fork play")
        sh(*wk, "return", "worlds/test", cwd=repo)
        check("return goes to main", sh("git", "branch", "--show-current", cwd=repo).stdout.strip() == "main")
        check("main untouched by fork", "shot a security officer" not in f.read_text())
        m = json.loads(sh(*wk, "metrics", "worlds/test", cwd=repo).stdout)
        check("no fork bleed", m["fork_bleed"] == 0, m["fork_bleed"])
        # bleed it deliberately
        f.write_text(json.dumps(fd, indent=2)); commit(repo, "bleed")
        m = json.loads(sh(*wk, "metrics", "worlds/test", cwd=repo).stdout)
        check("fork bleed detected", m["fork_bleed"] == 1, m["fork_bleed"])
        sh("git", "reset", "-q", "--hard", "HEAD~1", cwd=repo)

        # holodeck: play after the save, then move it to a fork
        fd2 = json.loads(f.read_text())
        fd2["facts"].append({"id": "F-004", "statement": "Romulan ale in the XO's quarters.",
                             "known_by": ["player"], "surfaced_at": "41161.0", "source": "play",
                             "created_at": "41161.0"})
        f.write_text(json.dumps(fd2, indent=2)); commit(repo, "regrettable play")
        sh(*wk, "holodeck", "worlds/test", cwd=repo)
        check("holodeck resets main to the save", "Romulan ale" not in f.read_text())
        forks = sh("git", "branch", "--list", "fork/test/holodeck-*", cwd=repo).stdout
        check("holodeck keeps the run on a fork", "holodeck-" in forks, forks)
        check("ledger records the holodeck run", '"HOLODECK"' in lp.read_text())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'ALL PASSED' if not FAILS else f'{len(FAILS)} FAILED'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
