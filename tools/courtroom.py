#!/usr/bin/env python3
"""File-backed mock-court controller. Python 3.10+, standard library only.

Checks persistence, record references and packet filtering, not legal reasoning.
Packed case material is spoiler-reduction, NOT encryption or access control.
"""
from __future__ import annotations
import argparse
import base64
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zlib

VERSION = "1.0.0"
SEED_SHA256 = "3483d21265f857d764a548baf609e9ecb8b40775b0c9606eba52029de273b116"
ROLES = {"player", "opponent", "bench", "W1", "W2", "W3", "W4"}
ACTORS = ROLES | {"clerk", "solicitor", "engine"}
PHASES = ["conference", "preparation", "opening", "evidence", "closing", "judgment", "closed"]
KINDS = {"dialogue", "action", "private", "phase", "question", "pass", "answer", "objection", "reply", "ruling", "submission", "stipulation", "show", "erratum", "gap", "repair", "judgment", "checkpoint", "unsealed"}
USES = {"truth", "notice", "context", "credibility"}
CASE = Path(".world/cases/case-001")
PUBLIC = Path("chronicle/case-001")

class CourtError(ValueError):
    """A rejected operation leaves the authoritative record unchanged."""

def require(ok: bool, message: str) -> None:
    if not ok:
        raise CourtError(message)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def atomic(path: Path, data: bytes) -> None:
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
    require(bool(re.fullmatch(r"[a-z][a-z0-9-]{0,47}", name)), "Invalid world name.")
    parent = root.resolve() / "worlds"
    require(not parent.is_symlink(), "Worlds directory must not be a symlink.")
    result = parent / name
    require(not result.is_symlink(), "World directory must not be a symlink.")
    return result

@contextmanager
def locked(world: Path):
    lock = world / ".world/courtroom.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CourtError("Courtroom is locked. Check for a live writer before removing a stale .world/courtroom.lock.") from exc
    try:
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)

def source_seed(root: Path) -> bytes:
    packed = (root / "modules/courtroom/.sealed/case-001.json.zlib.b64").read_bytes()
    raw = zlib.decompress(base64.b64decode(packed.strip(), validate=True))
    require(digest(raw) == SEED_SHA256, "Committed seed digest mismatch. Do not regenerate a live case.")
    return raw

def initialise(root: Path, name: str) -> Path:
    world = world_path(root, name)
    if world.exists():
        verify(world)
        return world
    raw = source_seed(root)
    seed = json.loads(raw)
    world.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".court-init-", dir=world.parent))
    try:
        fixed: list[str] = []
        def save(rel: str | Path, data: bytes, immutable: bool = True):
            atomic(temp / rel, data)
            if immutable:
                fixed.append(str(Path(rel).as_posix()))
        save("charter.md", (root / "templates/courtroom-charter.md").read_bytes(), False)
        for name_ in ("procedure.md", "authorities.md"):
            save(Path("canon") / name_, (root / "modules/courtroom" / name_).read_bytes())
        save(CASE / "case-base.json", raw)
        save(PUBLIC / "brief.md", seed["brief"].encode())
        for key, doc in seed["documents"].items():
            save(PUBLIC / "documents" / f"{key}.md", doc["text"].encode())
        for role, info in seed["roles"].items():
            packet = deepcopy(info)
            if role == "opponent":
                packet["client_knowledge"] = {r: seed["roles"][r]["knowledge"] for r in info["client_knowledge"]}
            save(CASE / "role-packets" / f"initial-{role}.json", encode(packet))
        save(PUBLIC / "client-instructions.md", seed["roles"]["player"]["private_instructions"].encode())
        save(".world/truth.json", encode({"courtroom_version": VERSION, "active_case": "case-001", "case_base": str(CASE / "case-base.json"), "seed_sha256": SEED_SHA256, "opening": seed["opening"], "note": "No desired verdict. Historical facts are fixed; events hold later developments."}))
        manifest = {"version": 1, "seed_sha256": SEED_SHA256, "files": {p: digest((temp / p).read_bytes()) for p in sorted(fixed)}}
        save(CASE / "base-manifest.json", encode(manifest), False)
        save(CASE / "events.jsonl", b"", False)
        render(temp, seed, [])
        require(not world.exists(), "Another process created this world; no overwrite performed.")
        temp.rename(world)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return world

def read_case(world: Path) -> dict:
    manifest = load(world / CASE / "base-manifest.json")
    require(manifest.get("seed_sha256") == SEED_SHA256, "Wrong case commitment.")
    require(digest((world / CASE / "case-base.json").read_bytes()) == SEED_SHA256, "Historical case base changed.")
    for rel, expected in manifest["files"].items():
        path = world / rel
        require(not Path(rel).is_absolute() and ".." not in Path(rel).parts, "Unsafe manifest path.")
        require(path.resolve().is_relative_to(world.resolve()), "Manifest path escapes world.")
        require(path.is_file() and digest(path.read_bytes()) == expected, f"Fixed material changed: {rel}")
    return load(world / CASE / "case-base.json")

def read_events(world: Path) -> list[dict]:
    events = []
    previous = "0" * 64
    for n, line in enumerate((world / CASE / "events.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        e = json.loads(line)
        signature = e.pop("hash")
        require(e.get("id") == f"T{n:04d}" and e.get("previous") == previous, "Broken event sequence.")
        require(digest(encode(e)) == signature, f"Event {n} digest mismatch.")
        e["hash"] = signature
        previous = signature
        events.append(e)
    return events

def initial_state(seed: dict) -> dict:
    return {"phase": "conference", "pending": None, "assessment_paused": False, "unsealed": False,
            "documents": {k: {"status": d["initial_status"], "uses": ["truth"] if d["initial_status"] == "admitted" else []} for k, d in seed["documents"].items()},
            "shown": {r: [] for r in ROLES}, "testimony_uses": {}, "corrections": {}, "judgment": None}

def check_refs(refs: list, state: dict, events: list[dict]) -> None:
    indexed = {e["id"]: e for e in events}
    for ref in refs:
        require(set(ref) == {"id", "use"} and ref["use"] in USES, "Reference needs id and permitted use.")
        key, use = ref["id"], ref["use"]
        if key in state["documents"]:
            d = state["documents"][key]
            require(d["status"] in {"admitted", "limited"} and use in d["uses"], f"Impermissible document use: {key}/{use}")
        else:
            e = indexed.get(key)
            require(e is not None and "bench" in e["audience"] and e["type"] in {"answer", "stipulation"}, f"Not merits evidence: {key}")
            require(key not in state["corrections"], f"Corrected testimony {key} must be re-established openly before reliance.")
            require(use in state["testimony_uses"].get(key, ["truth", "credibility"]), f"Excluded testimony use: {key}/{use}")

def apply(state: dict, e: dict, earlier: list[dict], seed: dict) -> None:
    kind, data, actor = e["type"], e.get("data", {}), e["actor"]
    require(kind in KINDS and actor in ACTORS and isinstance(e["text"], str), "Invalid event type, actor or text.")
    require(isinstance(e["audience"], list) and all(isinstance(r, str) for r in e["audience"]) and set(e["audience"]) <= ROLES, "Invalid event audience.")
    require(isinstance(data, dict), "Event data must be an object.")
    if kind in {"question", "answer", "objection", "reply", "ruling", "submission", "stipulation", "judgment"}:
        require({"player", "opponent", "bench"} <= set(e["audience"]), "Hearing events must be shared with both parties and bench.")
    if kind == "phase":
        require(actor == "engine" and state["pending"] is None, "Only controller can advance an idle hearing.")
        current = PHASES.index(state["phase"])
        require(current + 1 < len(PHASES) and data.get("to") == PHASES[current + 1], "Invalid phase transition.")
        if data["to"] == "closed":
            require(state["judgment"] is not None, "Cannot close without judgment.")
        state["phase"] = data["to"]
    elif kind == "question":
        require(state["phase"] == "evidence" and state["pending"] is None, "Question requires evidence phase and no pending question.")
        require(actor in {"player", "opponent", "bench"} and data.get("witness") in {"W1", "W2", "W3", "W4"}, "Invalid examiner or witness.")
        require(data["witness"] in e["audience"], "The witness must hear the question.")
        state["pending"] = {"id": e["id"], "witness": data["witness"], "waiting": [r for r in ("player", "opponent") if r != actor], "objection": False}
    elif kind == "pass":
        p = state["pending"]
        require(p is not None and actor in p["waiting"] and not p["objection"], "No available objection opportunity for that actor.")
        p["waiting"].remove(actor)
    elif kind == "objection":
        p = state["pending"]
        require(p is not None and actor in p["waiting"] and not p["objection"], "No pending objection opportunity.")
        require(data.get("rule") in seed["rules"], "Objection needs a disclosed rule ID.")
        p["waiting"].remove(actor)
        p["objection"] = True
    elif kind == "answer":
        p = state["pending"]
        require(p is not None and not p["waiting"] and not p["objection"], "Answer blocked: objection opportunity/ruling pending.")
        require(actor == p["witness"], "Only the questioned witness may answer.")
        state["pending"] = None
    elif kind == "ruling":
        require(actor == "bench" and data.get("rule") in seed["rules"], "Ruling needs bench and disclosed rule ID.")
        effect = data.get("effect")
        if effect == "objection":
            p = state["pending"]
            require(p is not None and p["objection"], "No objection awaits ruling.")
            require(data.get("result") in {"sustained", "overruled", "rephrase"}, "Invalid ruling result.")
            if data["result"] != "overruled":
                state["pending"] = None
            else:
                p["objection"] = False
        elif effect == "document":
            key, status, uses = data.get("document"), data.get("status"), data.get("uses", [])
            require(key in state["documents"] and status in {"marked", "admitted", "limited", "excluded"}, "Invalid exhibit ruling.")
            require(isinstance(uses, list) and set(uses) <= USES, "Invalid permitted uses.")
            require(bool(uses) == (status in {"admitted", "limited"}), "Permitted uses inconsistent with status.")
            state["documents"][key] = {"status": status, "uses": uses, "reason": e["text"], "turn": e["id"]}
        elif effect == "testimony":
            key, uses = data.get("turn"), data.get("uses", [])
            require(any(x["id"] == key and x["type"] in {"answer", "stipulation"} for x in earlier), "Unknown testimony.")
            require(isinstance(uses, list) and set(uses) <= USES, "Invalid testimony uses.")
            state["testimony_uses"][key] = uses
        else:
            require(effect == "procedure", "Unknown ruling effect.")
    elif kind == "stipulation":
        require(actor == "bench" and set(data.get("agreed_by", [])) == {"player", "opponent"}, "A stipulation requires both parties and entry by the bench.")
    elif kind == "show":
        require(data.get("document") in seed["documents"] and data.get("to") in ROLES, "Invalid disclosure.")
        require(data["to"] in e["audience"], "Recipient must receive the disclosure event.")
        state["shown"][data["to"]].append(data["document"])
    elif kind in {"gap", "erratum"}:
        require(actor == "engine", "Only controller records engine faults.")
        state["assessment_paused"] = True
        if kind == "erratum":
            target = next((x for x in earlier if x["id"] == data.get("target")), None)
            require(target is not None and isinstance(data.get("replacement"), str), "Erratum needs an existing turn and exact correction.")
            require(set(target["audience"]) <= set(e["audience"]), "Correction must reach original recipients.")
            state["corrections"][target["id"]] = e["id"]
        if data.get("cancel_pending"):
            state["pending"] = None
    elif kind == "repair":
        require(actor == "engine" and state["assessment_paused"], "No engine repair is pending.")
        require(bool(e["text"].strip()), "Repair needs an open explanation.")
        require(data.get("reopen", state["phase"]) in PHASES[:-1], "Invalid repair phase.")
        state["phase"] = data.get("reopen", state["phase"])
        state["assessment_paused"] = False
        state["judgment"] = None
    elif kind == "unsealed":
        require(actor == "engine" and state["phase"] == "closed", "Unsealing requires a closed case.")
        state["unsealed"] = True
    elif kind == "judgment":
        require(actor == "bench" and state["phase"] == "judgment" and state["pending"] is None and not state["assessment_paused"], "Hearing not ready for judgment.")
        findings = data.get("findings", [])
        require(len(findings) == len(seed["issues"]) and {f.get("issue") for f in findings} == set(seed["issues"]), "Judgment must address every supplied issue.")
        for f in findings:
            require(f.get("finding") in {"proved", "not_proved", "not_reached"} and bool(f.get("reason")), "Each finding needs a status and reason.")
            require(isinstance(f.get("refs"), list), "Each finding needs a record-reference list.")
            require(f["finding"] != "proved" or bool(f["refs"]), "A proved finding needs evidence references.")
            check_refs(f["refs"], state, earlier)
        found = {f["issue"]: f["finding"] for f in findings}
        award = data.get("award_aud")
        require(type(award) is int and 0 <= award <= seed["maximum_award"], "Invalid whole-dollar award.")
        require(found["I1"] != "not_reached", "I1 must be decided.")
        require(award == 0 or (found["I1"] == "proved" and found["I2"] == "proved"), "An award needs both issues proved.")
        state["judgment"] = {"turn": e["id"], "text": e["text"], **data}


def replay(seed: dict, events: list[dict]) -> dict:
    state = initial_state(seed)
    for i, e in enumerate(events):
        apply(state, e, events[:i], seed)
    return state

def packet(world: Path, role: str) -> dict:
    require(role in ROLES, "Unknown role.")
    seed, events = read_case(world), read_events(world)
    state = replay(seed, events)
    initial = load(world / CASE / "role-packets" / f"initial-{role}.json")
    allowed = set(initial["documents"]) | set(state["shown"][role])
    if role == "bench":
        allowed = {k for k, d in state["documents"].items() if d["status"] in {"admitted", "limited"}}
    result = {"role": initial, "brief": seed["brief"], "procedure": (world / "canon/procedure.md").read_text(encoding="utf-8"), "phase": state["phase"], "pending": state["pending"], "assessment_paused": state["assessment_paused"], "documents": {k: {"text": seed["documents"][k]["text"], **state["documents"][k]} for k in sorted(allowed)}, "events": []}
    # Never export the sealed private_note, digest metadata, author truth or another role's instructions.
    for e in events:
        if role in e["audience"]:
            row = {k: e[k] for k in ("id", "type", "actor", "text", "data")}
            if e["id"] in state["corrections"]:
                row["corrected_by"] = state["corrections"][e["id"]]
            row["evidence_uses"] = [] if e["id"] in state["corrections"] else state["testimony_uses"].get(e["id"], ["truth", "credibility"] if e["type"] in {"answer", "stipulation"} else [])
            result["events"].append(row)
    if role == "player":
        result["informed_replay"] = state["unsealed"]
    if role == "bench":
        # The bench can encounter offered material for admissibility only, never as automatic merits evidence.
        result["admissibility_only"] = {k: seed["documents"][k]["text"] for k, d in state["documents"].items() if d["status"] == "marked"}
    return result

def projections(seed: dict, events: list[dict]) -> dict[Path, bytes]:
    state = replay(seed, events)
    hearing = [e for e in events if "bench" in e["audience"]]
    private = [e for e in events if "player" in e["audience"] and "bench" not in e["audience"]]
    def transcript(items, heading):
        return (heading + "\n\n" + "\n\n".join(f"## {e['id']} | {e['actor']} | {e['type']}\n\n{e['text']}\n\nRecord data: {json.dumps(e['data'], ensure_ascii=False, sort_keys=True)}" for e in items) + "\n").encode()
    table = "# Document status\n\nID | Title | Status | Permitted uses\n---|---|---|---\n"
    table += "\n".join(f"{k} | {seed['documents'][k]['title']} | {d['status']} | {', '.join(d['uses']) or 'none'}" for k, d in state["documents"].items()) + "\n"
    card = f"# Courtroom card\n\nCase: case-001\nPhase: {state['phase']}\nLast turn: {events[-1]['id'] if events else 'none'}\nPending: {json.dumps(state['pending'])}\nAssessment paused: {state['assessment_paused']}\n\nTelling: senses, dialogue-led, one consequential beat; options off.\nRead charter at scene changes. Fixed facts: cases/case-001/case-base.json.\nLive court state is projected from events.jsonl; do not hand-edit projections.\nUse filtered role packets before anyone speaks; preserve player strategy privacy.\n"
    ledger = "# Courtroom ledger (append-equivalent projection of events.jsonl)\n\n" + "\n".join(f"{e['id']} {e['type']} {json.dumps(e, ensure_ascii=False, sort_keys=True)}" for e in events) + "\n"
    return {CASE / "live.json": encode(state), Path(".world/state.md"): card.encode(), Path(".world/ledger.md"): ledger.encode(), PUBLIC / "transcript.md": transcript(hearing, "# Exact hearing record"), PUBLIC / "private-record.md": transcript(private, "# Counsel's private record (not court evidence)"), PUBLIC / "exhibit-index.md": table.encode(), PUBLIC / "rulings.md": transcript([e for e in hearing if e["type"] == "ruling"], "# Rulings"), PUBLIC / "judgment.md": (("# Judgment\n\n" + state["judgment"]["text"] + "\n") if state["judgment"] else "# Judgment\n\nNot yet delivered.\n").encode(), CASE / "errata.md": transcript([e for e in events if e["type"] in {"gap", "erratum", "repair"}], "# Engine errors and repairs")}

def render(world: Path, seed: dict, events: list[dict]) -> None:
    for path, content in projections(seed, events).items():
        atomic(world / path, content)

def verify(world: Path, check_projections: bool = True) -> dict:
    seed, events = read_case(world), read_events(world)
    state = replay(seed, events)
    if check_projections:
        for path, expected in projections(seed, events).items():
            require((world / path).exists() and (world / path).read_bytes() == expected, f"Stale/edited projection: {path}; use resume after checking the authoritative event log.")
        snapshot = world / CASE / "adjudication.json"
        if state["judgment"] is None:
            require(not snapshot.exists(), "Stale adjudication snapshot; use resume.")
        else:
            require(snapshot.exists() and snapshot.read_bytes() == encode(packet(world, "bench")), "Stale/edited adjudication snapshot; use resume.")
    return {"case": seed["case_id"], "phase": state["phase"], "events": len(events), "fixed_files": len(load(world / CASE / "base-manifest.json")["files"]), "status": "PASS"}

def record(world: Path, inputs: dict | list[dict]) -> list[str]:
    with locked(world):
        seed, events = read_case(world), read_events(world)
        state = replay(seed, events)
        batch = inputs if isinstance(inputs, list) else [inputs]
        require(bool(batch), "Empty event batch.")
        new_ids = []
        for raw in batch:
            require(isinstance(raw, dict) and set(raw) <= {"type", "actor", "text", "audience", "data", "private_note"}, "Unknown event fields.")
            require({"type", "actor", "text", "audience"} <= set(raw), "Missing event fields.")
            e = deepcopy(raw)
            e.setdefault("data", {})
            e["id"] = f"T{len(events)+1:04d}"
            e["previous"] = events[-1]["hash"] if events else "0" * 64
            apply(state, e, events, seed)
            e["hash"] = digest(encode(e))
            events.append(e)
            new_ids.append(e["id"])
        # One authoritative atomic commit; projections can be recovered if the process then dies.
        data = b"".join(json.dumps(e, ensure_ascii=False, sort_keys=True).encode() + b"\n" for e in events)
        atomic(world / CASE / "events.jsonl", data)
        render(world, seed, events)
        if state["judgment"] is not None:
            atomic(world / CASE / "adjudication.json", encode(packet(world, "bench")))
        else:
            (world / CASE / "adjudication.json").unlink(missing_ok=True)
        return new_ids

def resume(world: Path) -> dict:
    with locked(world):
        seed, events = read_case(world), read_events(world)
        render(world, seed, events)
        state = replay(seed, events)
        if state["judgment"] is not None:
            atomic(world / CASE / "adjudication.json", encode(packet(world, "bench")))
        else:
            (world / CASE / "adjudication.json").unlink(missing_ok=True)
        return verify(world)

def unseal(world: Path, confirmed: bool) -> Path:
    require(confirmed, "Spoilers cannot be unseen. Repeat with --confirm-spoilers only after the player confirms.")
    require(verify(world)["phase"] == "closed", "Close this case before unsealing it.")
    record(world, {"type": "unsealed", "actor": "engine", "text": "Player confirmed opening case-001. Subsequent practice is informed, not blind.", "audience": ["player"]})
    dest = world / PUBLIC / "unsealed-case.json"
    atomic(dest, (world / CASE / "case-base.json").read_bytes())
    return dest

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "verify", "resume", "packet", "record", "unseal"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--world", default="courtroom-trial")
    parser.add_argument("--role", choices=sorted(ROLES))
    parser.add_argument("--event", type=Path)
    parser.add_argument("--out", type=Path, help="Write a packet without printing its contents; keep private packets under .world.")
    parser.add_argument("--confirm-spoilers", action="store_true")
    args = parser.parse_args()
    try:
        world = world_path(args.root, args.world)
        if args.command == "init":
            print(f"Ready: {initialise(args.root, args.world)} (existing hearings are never reset).")
        elif args.command == "verify":
            print(json.dumps(verify(world), sort_keys=True))
        elif args.command == "resume":
            print(json.dumps(resume(world), sort_keys=True))
        elif args.command == "record":
            require(args.event is not None, "record requires --event JSON_FILE.")
            print("Recorded " + ", ".join(record(world, json.loads(args.event.read_text(encoding="utf-8")))))
        elif args.command == "packet":
            require(args.role is not None, "packet requires --role.")
            output = encode(packet(world, args.role))
            if args.out:
                # Prevent accidentally overwriting the case, events, or public documents.
                dest = args.out.resolve()
                safe = (world / ".world/packets").resolve()
                require(dest.is_relative_to(safe) and dest.suffix == ".json", "Packet output must be a JSON file under this world's .world/packets/.")
                atomic(dest, output)
                print(f"Packet written: {dest}")
            else:
                print(output.decode(), end="")
        else:
            print(f"Unsealed only case-001: {unseal(world, args.confirm_spoilers)}")
        return 0
    except (CourtError, OSError, ValueError, KeyError, TypeError, zlib.error) as exc:
        print(f"Courtroom error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
