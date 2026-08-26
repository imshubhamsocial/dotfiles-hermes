"""
U6 Append-Only Trajectory Event Stream (Phase 4.1)
===================================================
Machine-parseable immutable record of every harness turn, tool payload,
gate verdict and test result (roadmap §4.1) — the distillation source for
U7 replay, U17 lineage search and U18 AlphaEvolve.

Storage law (Trap-1: NVMe write amplification):
  - ACTIVE stream lives on the RAMDisk (/dev/shm/hermes_trajectory/).
  - `flush_to_milestone_disk()` copies it to the persistent canonical
    location (.hermes/trajectory.jsonl) ONLY at milestone completion,
    applying Btrfs `chattr +C` (NOCOW) best-effort before writing.

Immutability proof: every event is sealed into a sha256 hash chain
(`prev` -> `hash`); `verify_chain()` detects any mutation, deletion or
reordering after the fact. Appends use O_APPEND semantics.
"""

import hashlib
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RAMDISK_DIR = Path("/dev/shm/hermes_trajectory")
CANONICAL_RELATIVE = Path(".hermes") / "trajectory.jsonl"
EVENT_TYPES = ("turn_start", "tool_call", "gate_check", "tool_result",
               "test_result", "handoff", "response", "turn_end")


def active_path() -> Path:
    """Active RAMDisk stream location (env override honored for tests)."""
    override = os.environ.get("HERMES_TRAJECTORY_PATH")
    return Path(override) if override else RAMDISK_DIR / "trajectory.jsonl"


def _canonical(event: Dict[str, Any]) -> str:
    return json.dumps(event, sort_keys=True, separators=(",", ":"))


def _seal(event: Dict[str, Any], prev_hash: str) -> Dict[str, Any]:
    body = {k: v for k, v in event.items() if k not in ("prev", "hash")}
    body["prev"] = prev_hash
    digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
    body["hash"] = digest
    return body


class TrajectoryRecorder:
    """Appends hash-chained events to the shared append-only JSONL stream."""

    def __init__(self, session_id: Optional[str] = None,
                 path: Optional[Path] = None):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.path = Path(path) if path else active_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _tail_hash(self) -> str:
        last = self._read_last_event()
        return last["hash"] if last else "GENESIS"

    def _read_last_event(self) -> Optional[Dict[str, Any]]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        with open(self.path, "rb") as fh:
            fh.seek(-2, os.SEEK_END)
            while fh.read(1) != b"\n":
                pos = fh.tell()
                if pos <= 1:
                    fh.seek(0)
                    break
                fh.seek(-2, os.SEEK_CUR)
            return json.loads(fh.readline().decode("utf-8"))

    def append(self, **fields: Any) -> Dict[str, Any]:
        # Re-read chain head + seq on EVERY append so interleaved recorders
        # (multiple sessions, engine loops) can never fork the chain.
        event = {"seq": self._next_seq(), "ts": int(time.time() * 1000),
                 "session": self.session_id}
        unknown_type = fields.get("event") not in EVENT_TYPES
        if unknown_type and "event" in fields:
            raise ValueError(f"unknown trajectory event type: {fields.get('event')}")
        event.update(fields)
        sealed = _seal(event, self._tail_hash())
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(_canonical(sealed) + "\n")
        return sealed

    def _next_seq(self) -> int:
        last = self._read_last_event()
        return (last["seq"] + 1) if last else 0

    # -- typed helpers ---------------------------------------------------
    def record_turn(self, turn: int, role: str, prompt_tokens: int = 0,
                    **extra: Any) -> Dict[str, Any]:
        return self.append(event="turn_start", turn=turn, role=role,
                           prompt_tokens=prompt_tokens, **extra)

    def record_tool_call(self, turn: int, role: str, tool: str,
                         args_head: str = "", **extra: Any) -> Dict[str, Any]:
        return self.append(event="tool_call", turn=turn, role=role, tool=tool,
                           args_head=str(args_head)[:200], **extra)

    def record_gate(self, turn: int, tool: str, gate_status: str,
                    reason: str = "", **extra: Any) -> Dict[str, Any]:
        return self.append(event="gate_check", turn=turn, tool=tool,
                           gate_status=gate_status, reason=str(reason)[:300],
                           **extra)

    def record_tool_result(self, turn: int, tool: str, result_ok: bool,
                           result_head: str = "", **extra: Any) -> Dict[str, Any]:
        return self.append(event="tool_result", turn=turn, tool=tool,
                           result_ok=bool(result_ok),
                           result_head=str(result_head)[:200], **extra)

    def record_test(self, turn: int, test_passed: bool, command: str = "",
                    **extra: Any) -> Dict[str, Any]:
        return self.append(event="test_result", turn=turn,
                           test_passed=bool(test_passed), command=command[:200],
                           **extra)

    def record_tool_result(self, turn: int, tool: str, result_head: str = "",
                           result_ok: bool = True, **extra: Any) -> Dict[str, Any]:
        return self.append(event="tool_result", turn=turn, tool=tool,
                           result_head=str(result_head)[:300],
                           result_ok=bool(result_ok), **extra)


# ─── Offline verification & milestone flush ──────────────────────────────────

def load_events(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    target = Path(path) if path else active_path()
    if not target.exists():
        return []
    out = []
    with open(target, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def verify_chain(path: Optional[Path] = None) -> Tuple[bool, str]:
    """Recompute the full chain: seq continuity + prev linkage + hashes."""
    events = load_events(path)
    prev = "GENESIS"
    for i, ev in enumerate(events):
        if ev.get("seq") != i:
            return False, f"seq discontinuity at index {i}: got {ev.get('seq')}"
        body = {k: v for k, v in ev.items() if k != "hash"}
        if body.get("prev") != prev:
            return False, f"broken prev linkage at seq {ev.get('seq')}"
        if hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() != ev.get("hash"):
            return False, f"hash mismatch (tamper) at seq {ev.get('seq')}"
        prev = ev["hash"]
    return True, f"chain intact: {len(events)} events"


def flush_to_milestone_disk(target: Optional[Path] = None,
                            source: Optional[Path] = None) -> Dict[str, Any]:
    """Materialize the RAMDisk stream ONCE per milestone into persistent
    storage. Incoming events are RE-SEALED to continue the destination
    chain (seq + prev linkage), so the milestone file remains one valid,
    unbroken ledger across all milestones. Existing destination bytes are
    never rewritten — new sealed lines are appended only."""
    dst = Path(target) if target else CANONICAL_RELATIVE
    src = Path(source) if source else active_path()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        chattr = subprocess.run(["chattr", "+C", str(dst.parent)], capture_output=True)
    except FileNotFoundError:
        chattr = None

    def _dst_tail():
        if not dst.exists() or dst.stat().st_size == 0:
            return "GENESIS", 0
        with open(dst, "rb") as fh:
            fh.seek(-2, os.SEEK_END)
            while fh.read(1) != b"\n":
                pos = fh.tell()
                if pos <= 1:
                    fh.seek(0)
                    break
                fh.seek(-2, os.SEEK_CUR)
            tail = json.loads(fh.readline().decode("utf-8"))
        return tail["hash"], tail["seq"] + 1

    merged = skipped = 0
    if src.exists():
        prev, next_seq = _dst_tail()
        with open(dst, "a", encoding="utf-8") as out, \
             open(src, "r", encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if not s:
                    continue
                try:
                    body = {k: v for k, v in json.loads(s).items()
                            if k not in ("prev", "hash")}
                except json.JSONDecodeError:
                    skipped += 1
                    continue
                body["prev"] = prev
                body["seq"] = next_seq
                next_seq += 1
                digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
                body["hash"] = digest
                prev = digest
                out.write(_canonical(body) + "\n")
                merged += 1
        src.unlink(missing_ok=True)
    flushed = dst.stat().st_size if dst.exists() else 0
    ok, detail = verify_chain(dst)
    return {"target": str(dst), "bytes_on_disk": flushed,
            "events_merged": merged, "malformed_skipped": skipped,
            "chain_valid_after_merge": ok,
            "nocow_applied": chattr is not None and chattr.returncode == 0}


if __name__ == "__main__":
    rec = TrajectoryRecorder(session_id="demo")
    rec.record_turn(turn=1, role="coder", prompt_tokens=1420)
    rec.record_gate(turn=1, tool="patch", gate_status="PASS")
    rec.record_test(turn=1, test_passed=True, command="pytest -q")
    ok, detail = verify_chain()
    print(ok, "|", detail)
