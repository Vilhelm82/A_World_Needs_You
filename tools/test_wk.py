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


def soul(cid, tier="canon", routing=None, codes=(), roles=(), deduction="medium"):
    return {"id": cid, "name": cid.title(), "rank": "Lt", "post": "ops", "tier": tier,
            "access": {"areas": [], "systems": [], "codes": list(codes), "skills": []},
            "roles": list(roles), "competence": {"deduction": deduction},
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
    write(w / "charter.md", "# Charter — test\n\npreset: modules/tng-d\n")
    write(repo / "modules/tng-d/law.md", "# Law\n\n- [canon] Phasers have a stun setting.\n")
    write(repo / "modules/tng-d/canon/cards.jsonl", json.dumps(
        {"id": "K-001", "layer": "rules", "topic": "transporters and shields",
         "statement": "A transporter cannot beam through raised deflector shields.",
         "sources": ["https://memory-alpha.fandom.com/wiki/Transporter"],
         "verified_at": "2026-10-18", "supersedes": None}) + "\n")
    write(w / ".world" / "timeline.json", {"main": "main"})
    write(s / "clock.json", {"stardate": 41153.7, "ship_time": "08:00", "day": 1, "alert": "normal",
                             "location": "Farpoint", "episode_open": None, "timeline": "main"})
    write(s / "ship.json", {"course": "none", "orders": [], "systems": {}})
    write(s / "player.json", {"name": "Will Lloyd", "rank": "Commander", "post": "first officer",
                              "access": {"areas": [], "systems": [], "skills": [],
                                         "codes": ["xo", "engineering-override"]},
                              "location": "bridge"})
    profiles = {"picard": dict(codes=["captain", "engineering-override"], roles=["captain"]),
                "data": dict(codes=[], roles=["ops"], deduction="high"),
                "yar": dict(codes=["security"], roles=["security"], deduction="high")}
    for cid in ("picard", "data", "yar"):
        write(s / "crew" / cid / "soul.json", soul(cid, **profiles[cid]))
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
    write(s / "deeds.json", {"acts": [], "traces": [], "cases": []})
    write(s / "divergence.json", {"divergences": []})
    write(s / "projects.json", {"projects": []})
    write(s / "unknowns.json", {"unknowns": []})
    write(s / "hypotheses.json", {"hypotheses": []})
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

        # deeds and deduction: only the XO's codes and the captain's could do it; the captain has an alibi
        ep = w / ".world/state/deeds.json"
        deeds = {"acts": [{"id": "A-001", "actor": "player", "what": "rerouted the plasma conduit",
                           "at": 41160.1, "where": "deck 31", "visibility": "unwitnessed",
                           "valence": "credit",
                           "constraints": {"means": {"codes": ["engineering-override"]},
                                           "opportunity": {"where": "deck 31",
                                                           "window": [41160.0, 41160.2]}},
                           "traces": ["T-001", "T-002", "T-003"]}],
                 "traces": [
                     {"id": "T-001", "type": "authorisation", "where": "computer core", "act": "A-001",
                      "who_can_read": ["security"], "lasts": "permanent", "created_at": "41160.1"},
                     {"id": "T-002", "type": "location", "where": "bridge", "subject": "picard",
                      "window": [41159.9, 41160.3], "act": "A-001", "who_can_read": ["security"],
                      "lasts": "permanent", "created_at": "41160.1"},
                     {"id": "T-003", "type": "witness", "where": "crowd:ensign", "act": "A-001",
                      "who_can_read": ["anyone"], "lasts": "memory", "created_at": "41160.1"}],
                 "cases": []}
        ep.write_text(json.dumps(deeds, indent=2))
        ok, out = commit(repo, "a deed")
        check("an act with traces and constraints commits", ok, out)
        r = json.loads(sh(*wk, "suspects", "worlds/test", "--act", "A-001", "--as", "yar", cwd=repo).stdout)
        check("deduction: exclusive access makes the XO the only suspect", r["pool"] == ["player"], r)
        check("deduction: an alibi from a readable location trace clears the captain",
              "placed elsewhere by T-002" in r["reasons"].get("picard", ""), r["reasons"])
        r = json.loads(sh(*wk, "suspects", "worlds/test", "--act", "A-001", "--as", "data", cwd=repo).stdout)
        check("deduction: Data sees the witness trace but not the security log",
              r["pool"] == ["picard", "player"], r)

        # a run that cites outside its light cone, then one with the wrong pool, then a correct one
        deeds["cases"] = [{"case_id": "C-001", "investigator": "yar", "trigger": "override alarm",
                           "known": ["T-001"], "next_step": "query", "status": "open",
                           "runs": [{"watch": 1, "turn": 2, "act": "A-001", "isolated": True,
                                     "cited": ["T-003"], "pool": ["player"], "suspects": ["player"]}]}]
        ep.write_text(json.dumps(deeds, indent=2))
        ok, out = commit(repo, "leaky investigator")
        check("an investigator citing outside its light cone is refused",
              not ok and "outside the investigator's light cone" in out, out)
        deeds["cases"][0]["runs"][0].update(cited=["T-001"], pool=["picard", "player"])
        ep.write_text(json.dumps(deeds, indent=2))
        ok, out = commit(repo, "wrong pool")
        check("a run whose pool doesn't match the computed pool is refused",
              not ok and "does not match the computed pool" in out, out)
        deeds["cases"][0]["runs"][0].update(pool=["player"], suspects=[])
        ep.write_text(json.dumps(deeds, indent=2))
        ok, out = commit(repo, "evidence")
        check("a run with the computed pool commits", ok, out)

        # knowledge locality for everyone
        before = lp.read_text()
        append(w, {"watch": 1, "turn": 3, "type": "SAID", "by": "data", "claim": "x", "truth": "true",
                   "fact": "F-002"})
        ok, out = commit(repo, "data knows too much")
        check("a crew member citing a fact they don't know is refused",
              not ok and "isn't in their knowledge" in out, out)
        lp.write_text(before)
        append(w, {"watch": 1, "turn": 3, "type": "SAID", "by": "crowd:ensign", "claim": "x",
                   "truth": "true", "fact": "F-002"})
        ok, out = commit(repo, "the crowd knows too much")
        check("the crowd citing a non-public fact is refused", not ok and "crowd can't know" in out, out)
        lp.write_text(before)
        append(w, {"watch": 1, "turn": 3, "type": "TOLD", "to": ["data"], "fact": "F-002"})
        ok, out = commit(repo, "told without update")
        check("telling someone a fact without updating known_by is refused",
              not ok and "isn't added to its known_by" in out, out)
        fd = json.loads(f.read_text()); fd["facts"][1]["known_by"].append("data")
        f.write_text(json.dumps(fd, indent=2))
        append(w, {"watch": 1, "turn": 4, "type": "SAID", "by": "data", "claim": "x", "truth": "true",
                   "fact": "F-002"})
        ok, out = commit(repo, "told properly")
        check("once told, they can cite it", ok, out)

        # lore touches need lore checks
        before = lp.read_text()
        t5 = turn(5, ["data"], ["data"], {"player": 1})
        t5["lore_touch"] = [{"what": "beaming through shields", "layer": "rules"}]
        append(w, t5)
        tdir = w / ".world/transcript"; tdir.mkdir(exist_ok=True)
        ok, out = commit(repo, "unchecked lore")
        check("a lore touch without a LORECHECK is refused", not ok and "touched lore" in out, out)
        append(w, {"watch": 1, "turn": 5, "type": "LORECHECK", "claim": "beaming through shields",
                   "layer": "rules", "verdict": "consistent", "cards": ["K-001"], "divergence": [],
                   "agent": False})
        ok, out = commit(repo, "checked lore")
        check("a lore touch with its LORECHECK commits", ok, out)
        res = json.loads(sh(*wk, "lore", "worlds/test", "can a transporter beam through shields",
                            cwd=repo).stdout)
        check("lore search finds the card", res["coverage"] == "covered"
              and res["cards"] and res["cards"][0]["id"] == "K-001", res)
        res = json.loads(sh(*wk, "lore", "worlds/test", "Ferengi trade bylaws", cwd=repo).stdout)
        check("lore search reports no coverage", res["coverage"] == "none", res)

        # canon cards are append-only and cited
        cards = repo / "modules/tng-d/canon/cards.jsonl"
        cbefore = cards.read_text()
        cards.write_text(cbefore.replace("cannot", "can"))
        ok, out = commit(repo, "edit a card")
        check("editing a verified card is refused", not ok and "append-only" in out, out)
        cards.write_text(cbefore + json.dumps({"id": "K-002", "layer": "rules", "topic": "t",
                                               "statement": "s", "sources": [],
                                               "verified_at": "2026-10-18", "supersedes": None}) + "\n")
        ok, out = commit(repo, "uncited card")
        check("a card without a source is refused", not ok and "at least one source" in out, out)
        cards.write_text(cbefore + json.dumps({"id": "K-002", "layer": "rules", "topic": "t",
                                               "statement": "s2", "sources": ["https://x"],
                                               "verified_at": "2026-10-18", "supersedes": "K-001"}) + "\n")
        ok, out = commit(repo, "superseding card")
        check("a superseding card commits", ok, out)

        # divergence chains must end in something somebody did
        dv = w / ".world/state/divergence.json"
        dv.write_text(json.dumps({"divergences": [
            {"id": "D-001", "canon": "c", "branch": "b", "parents": ["D-002"], "at": 41161},
            {"id": "D-002", "canon": "c", "branch": "b", "parents": ["D-001"], "at": 41161}]}))
        ok, out = commit(repo, "cycle")
        check("a divergence cycle is refused", not ok and "cycle" in out, out)
        dv.write_text(json.dumps({"divergences": [
            {"id": "D-001", "canon": "c", "branch": "b", "parents": ["L:9:9"], "at": 41161}]}))
        ok, out = commit(repo, "no cause")
        check("a divergence citing no real ledger entry is refused", not ok and "matches no ledger" in out, out)
        dv.write_text(json.dumps({"divergences": [
            {"id": "D-001", "canon": "the warp test happened", "branch": "it never ran",
             "parents": ["L:1:5"], "at": 41161},
            {"id": "D-002", "canon": "Wesley made acting ensign", "branch": "still a civilian",
             "parents": ["D-001"], "at": 41162}]}, indent=2))
        fo = w / ".world/state/forces.json"
        fod = json.loads(fo.read_text()); fod["forces"][0]["trajectory"][0].update(status="averted", cause="x")
        fo.write_text(json.dumps(fod))
        ok, out = commit(repo, "bad force cause")
        check("a force change whose cause is neither a divergence nor a ledger ref is refused",
              not ok and "neither a divergence" in out, out)
        fod["forces"][0]["trajectory"][0]["cause"] = "D-002"
        fo.write_text(json.dumps(fod, indent=2))
        ok, out = commit(repo, "divergence chain")
        check("a valid divergence chain and force cause commit", ok, out)

        # projects
        pj = w / ".world/state/projects.json"
        proj = {"id": "J-001", "title": "Warp field resonance", "owner": "player",
                "collaborators": ["laforge"], "kind": "experiment", "goal": "g",
                "stages": [{"name": "model", "status": "doing", "needs": "time", "cost": "a shift"}],
                "status": "active", "precedents": ["P-001"], "started_at": 41161}
        pj.write_text(json.dumps({"projects": [proj]}))
        ok, out = commit(repo, "unknown collaborator")
        check("a project naming an unknown person is refused", not ok and "unknown 'laforge'" in out, out)
        proj["collaborators"] = ["data"]
        pj.write_text(json.dumps({"projects": [proj]}, indent=2))
        ok, out = commit(repo, "project")
        check("a valid project commits", ok, out)

        # physics: mechanism cards
        mech = repo / "modules/tng-d/canon/mechanisms.jsonl"
        card = {"id": "M-001", "tech": "transporter", "canon_capabilities": ["beams people"],
                "canon_limits": ["not through raised shields"],
                "physics_basis": "quantum state transfer", "postulates": ["P2", "P6"],
                "engineering_gap": "state capture at scale",
                "budgets": [{"quantity": "rest energy, 70 kg", "value": "6.29e18 J", "basis": "CALC: 70 * c**2"}],
                "failure_modes": ["lock loss"], "sources": ["https://x"], "verified_at": "2026-10-18",
                "supersedes": None}
        mech.write_text(json.dumps(card) + "\n")
        ok, out = commit(repo, "extra postulate")
        check("a mechanism card using a postulate outside the closed list is refused",
              not ok and "closed list" in out, out)
        card["postulates"] = ["P2", "P4"]; card["budgets"][0]["basis"] = "about six exajoules"
        mech.write_text(json.dumps(card) + "\n")
        ok, out = commit(repo, "narrated number")
        check("a narrated (uncomputed) budget is refused", not ok and "isn't computed" in out, out)
        card["budgets"][0]["basis"] = "CALC: 70 * c**2"
        mech.write_text(json.dumps(card) + "\n")
        ok, out = commit(repo, "mechanism")
        check("a valid mechanism card commits", ok, out)
        res = json.loads(sh(*wk, "lore", "worlds/test", "how does the transporter work", cwd=repo).stdout)
        check("lore search finds the mechanism", res["mechanisms"] and res["mechanisms"][0]["id"] == "M-001", res)
        mech.write_text(json.dumps(dict(card, physics_basis="magic")) + "\n")
        ok, out = commit(repo, "edit mechanism")
        check("editing a mechanism card is refused", not ok and "append-only" in out, out)
        sh("git", "reset", "-q", "--hard", cwd=repo)

        # CALC and ROLL entries are checked
        before = lp.read_text()
        append(w, {"watch": 1, "turn": 5, "type": "CALC", "expression": "70 * c**2", "result": 5e18,
                   "units": "J", "purpose": "a narrated guess"})
        ok, out = commit(repo, "bad calc")
        check("a CALC with the wrong result is refused", not ok and "CALC 70 * c**2" in out, out)
        lp.write_text(before)
        append(w, {"watch": 1, "turn": 5, "type": "CALC", "expression": "70 * c**2",
                   "result": 6.291286251157723e18, "units": "J", "purpose": "transporter budget"},
                  {"watch": 1, "turn": 5, "type": "ROLL", "outcomes": ["a", "b", "c"], "roll": 2,
                   "result": "c"})
        ok, out = commit(repo, "bad roll")
        check("a ROLL recording the wrong outcome is refused", not ok and "names outcome" in out, out)
        lp.write_text(before)
        append(w, {"watch": 1, "turn": 5, "type": "CALC", "expression": "70 * c**2",
                   "result": 6.291286251157723e18, "units": "J", "purpose": "transporter budget"},
                  {"watch": 1, "turn": 5, "type": "ROLL", "outcomes": ["a", "b", "c"], "roll": 2,
                   "result": "b"})
        ok, out = commit(repo, "calc and roll")
        check("a correct CALC and ROLL commit", ok, out)

        # the sheet fills in as the person plays; the soft check flags slips before they land
        before = lp.read_text()
        append(w, {"watch": 1, "turn": 5, "type": "SHEET", "text": "Has a sister in Hobart.",
                   "outcome": "taken", "reason": "colour; no canon conflict"})
        ok, out = commit(repo, "sheet entry not written")
        check("a taken SHEET entry must be on sheet.md", not ok and "not on sheet.md" in out, out)
        (w / "sheet.md").write_text("# Sheet\n\n- (watch 1, turn 5) Has a sister in Hobart.\n")
        ok, out = commit(repo, "sheet entry")
        check("a taken SHEET entry on sheet.md commits", ok, out)
        before = lp.read_text()
        append(w, {"watch": 1, "turn": 6, "type": "CHECK", "claim": "Lloyd names Lore to Data",
                   "kind": "vibes", "conflicts_with": "Lloyd can't know of Lore", "answer": "changed"})
        ok, out = commit(repo, "bad check")
        check("a CHECK with an unknown kind is refused", not ok and "CHECK kind" in out, out)
        lp.write_text(before)
        append(w, {"watch": 1, "turn": 6, "type": "CHECK", "claim": "Lloyd names Lore to Data",
                   "kind": "knowledge", "conflicts_with": "Lloyd can't know of Lore", "answer": "changed"})
        ok, out = commit(repo, "check")
        check("a valid CHECK commits", ok, out)

        # unknowns hold observations only
        un = w / ".world/state/unknowns.json"
        un.write_text(json.dumps({"unknowns": [{"id": "q", "subject": "Q", "canon_record": ["K-001"],
                                               "observations": ["F-001"], "explanation": "a subspace being"}]}))
        ok, out = commit(repo, "explained Q")
        check("an unknown with an explanation is refused", not ok and "never an explanation" in out, out)
        un.write_text(json.dumps({"unknowns": [{"id": "q", "subject": "Q", "canon_record": ["K-001"],
                                               "observations": ["F-001"]}]}, indent=2))
        ok, out = commit(repo, "unknown")
        check("an unknown with observations only commits", ok, out)

        # hypotheses: survive, never crowned; falsified is permanent
        hp = w / ".world/state/hypotheses.json"
        hyp = {"id": "H-001", "subject": "q", "statement": "Q manifests through subspace distortions.",
               "proposed_by": "player", "held_by": ["player", "data"], "physics_basis": "P1",
               "predictions": [{"id": "p1", "if": "Q appears", "then": "subspace sensors register a spike"}],
               "tests": [], "status": "surviving", "created_at": 41170}
        hp.write_text(json.dumps({"hypotheses": [hyp]}))
        ok, out = commit(repo, "crowned")
        check("'surviving' with no supported test is refused", not ok and "needs at least one supported" in out, out)
        hyp["tests"] = [{"prediction": "p1", "via": "A-001", "observation": "F-001", "result": "supported"}]
        hp.write_text(json.dumps({"hypotheses": [hyp]}, indent=2))
        ok, out = commit(repo, "supported")
        check("a supported hypothesis can be surviving", ok, out)
        hyp["tests"].append({"prediction": "p1", "via": "A-001", "observation": "F-002", "result": "falsified"})
        hp.write_text(json.dumps({"hypotheses": [hyp]}, indent=2))
        ok, out = commit(repo, "ignore falsification")
        check("a falsified test forces status falsified", not ok and "must be 'falsified'" in out, out)
        hyp["status"] = "falsified"
        hp.write_text(json.dumps({"hypotheses": [hyp]}, indent=2))
        ok, out = commit(repo, "falsified")
        check("a falsified hypothesis commits", ok, out)
        hyp["status"] = "surviving"; hyp["tests"] = hyp["tests"][:1]
        hp.write_text(json.dumps({"hypotheses": [hyp]}, indent=2))
        ok, out = commit(repo, "revive")
        check("a falsified hypothesis can't be revived", not ok and "stays falsified" in out, out)
        sh("git", "reset", "-q", "--hard", cwd=repo)

        # later evidence reinterprets an observation; it never rewrites it
        base = sh("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
        fp = w / ".world/state/facts.json"
        fdata = json.loads(fp.read_text())
        f3 = {"id": "F-003", "statement": "The spike was the sensor pallet's own resonance.",
              "known_by": ["data"], "surfaced_at": None, "source": "test", "created_at": "41180",
              "reinterprets": "F-999"}
        fp.write_text(json.dumps({"facts": fdata["facts"] + [f3]}, indent=2))
        ok, out = commit(repo, "reinterpret nothing")
        check("reinterpreting an unknown fact is refused", not ok and "reinterprets unknown fact" in out, out)
        h2 = {"id": "H-002", "subject": "q", "statement": "Q manifests through subspace, and the "
              "contrary reading was a sensor artifact.", "proposed_by": "player", "held_by": ["player"],
              "physics_basis": "P1", "predictions": [{"id": "p1", "if": "Q appears", "then": "a spike"}],
              "tests": [], "status": "open", "created_at": 41180,
              "revives": {"hypothesis": "H-001", "via": "F-001"}}
        f3["reinterprets"] = "F-002"
        fp.write_text(json.dumps({"facts": fdata["facts"] + [f3]}, indent=2))
        hp.write_text(json.dumps({"hypotheses": [hyp_falsified := json.loads(
            sh("git", "show", "HEAD:worlds/test/.world/state/hypotheses.json", cwd=repo).stdout
        )["hypotheses"][0], h2]}, indent=2))
        ok, out = commit(repo, "revive without cause")
        check("reviving without a reinterpreting fact is refused",
              not ok and "only via a fact that reinterprets" in out, out)
        h2["revives"]["via"] = "F-003"
        hp.write_text(json.dumps({"hypotheses": [hyp_falsified, h2]}, indent=2))
        ok, out = commit(repo, "revive")
        check("a hypothesis revives a falsified one through a reinterpreting fact", ok, out)
        check("the falsified hypothesis stays falsified", hyp_falsified["status"] == "falsified")
        sh("git", "reset", "-q", "--hard", base, cwd=repo)

        # metrics: 12 turns where the player is addressed heavily and yar is neglected
        tdir = w / ".world/transcript"; tdir.mkdir(exist_ok=True)
        entries, text = [], "## turn 5\n...\n"
        for n in range(6, 18):
            entries.append(turn(n, ["picard", "data", "yar"], ["picard", "data"],
                                {"player": 3, "data": 1}, initiated=["data"] if n % 2 else []))
            text += f"## turn {n}\n...\n"
        entries += [{"watch": 1, "turn": 17, "type": "MOVED", "by": "q", "what": "x", "cause": "force:q"},
                    {"watch": 1, "turn": 17, "type": "MOVED", "by": "player", "what": "y", "cause": "player"},
                    {"watch": 1, "turn": 17, "type": "DECIDED", "by": "picard", "what": "z",
                     "without_player": True}]
        append(w, *entries)
        (tdir / "watch-001.md").write_text(text)
        ok, out = commit(repo, "play")
        check("a turn of play commits", ok, out)
        m = json.loads(sh(*wk, "metrics", "worlds/test", "--watch", "1", "--write", cwd=repo).stdout)
        check("address share computed", m["player_address_share"] == 0.75, m["player_address_share"])
        check("neglected officer detected", m["neglected_ids"] == ["yar"] and m["neglected_windows"] == 4,
              (m["neglected_ids"], m["neglected_windows"]))
        check("autonomy computed", m["autonomy"] == 0.5, m["autonomy"])
        check("investigator isolation computed", m["cases_isolated"] == 1.0, m["cases_isolated"])
        check("pool_ignored flags the protected suspect", m["pool_ignored"] == 1, m["pool_ignored"])
        check("lore checked rate computed", m["lore_checked_rate"] == 1.0, m["lore_checked_rate"])
        check("divergences counted", m["divergences"] == 2, m["divergences"])
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

        # the world runs from disk; origin (GitHub) is the remote copy and gets every commit
        remote = tmp / "remote.git"
        sh("git", "init", "-q", "--bare", str(remote), cwd=tmp)
        sh("git", "remote", "add", "origin", str(remote), cwd=repo)
        sh("git", "push", "-q", "origin", "main", cwd=repo)

        def remote_sha(ref):
            out = sh("git", "ls-remote", "origin", ref, cwd=repo).stdout.split()
            return out[0] if out else None

        def local_sha(ref):
            return sh("git", "rev-parse", ref, cwd=repo).stdout.strip()

        # timelines
        sh(*wk, "save", "worlds/test", "start", cwd=repo)
        check("save tags", "save/test/start" in sh("git", "tag", cwd=repo).stdout)
        check("save pushes its tag", remote_sha("refs/tags/save/test/start") == local_sha("save/test/start"))
        check("save pushes main", remote_sha("refs/heads/main") == local_sha("main"))
        sh(*wk, "fork", "worlds/test", "ale", cwd=repo)
        check("fork switches branch", sh("git", "branch", "--show-current", cwd=repo).stdout.strip()
              == "fork/test/ale")
        check("fork pushes its branch", remote_sha("refs/heads/fork/test/ale") == local_sha("HEAD"))
        fd = json.loads(f.read_text())
        fd["facts"].append({"id": "F-003", "statement": "Lloyd shot a security officer.",
                            "known_by": ["all"], "surfaced_at": "41160.0", "source": "fork",
                            "created_at": "41160.0"})
        f.write_text(json.dumps(fd, indent=2)); commit(repo, "fork play")
        check("every commit is pushed (post-commit hook)",
              remote_sha("refs/heads/fork/test/ale") == local_sha("HEAD"))
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
        check("holodeck resets the remote copy's main too", remote_sha("refs/heads/main") == local_sha("main"))
        hb = forks.split()[-1]
        check("holodeck pushes the run's fork", remote_sha(f"refs/heads/{hb}") is not None, hb)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'ALL PASSED' if not FAILS else f'{len(FAILS)} FAILED'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
