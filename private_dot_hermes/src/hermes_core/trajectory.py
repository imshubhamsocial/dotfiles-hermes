"""
U6 Append-Only Trajectory Event Stream & OpenLIT / OTel Observability (Milestone U6 & D7-10)
===========================================================================================
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

OpenLIT / OpenTelemetry Integration (Milestone D7-10):
  - Every hash-chained event is mirrored as an OpenTelemetry custom span
    (`hermes.trajectory.{event_type}`) annotated with hash-chain headers
    (seq, hash, prev, session) and LLM semantic conventions.
  - `init_observability()` sets up OpenLIT auto-instrumentation and OTLP export.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Graceful OpenLIT & OpenTelemetry optional imports
try:
    import openlit
    OPENLIT_AVAILABLE = True
except (ImportError, Exception):
    openlit = None
    OPENLIT_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except (ImportError, Exception):
    trace = None
    Status = None
    StatusCode = None
    OPENTELEMETRY_AVAILABLE = False

RAMDISK_DIR = Path("/dev/shm/hermes_trajectory")
CANONICAL_RELATIVE = Path(".hermes") / "trajectory.jsonl"
EVENT_TYPES = (
    "turn_start",
    "tool_call",
    "gate_check",
    "tool_result",
    "test_result",
    "handoff",
    "response",
    "turn_end",
)

_OBSERVABILITY_INITIALIZED = False


def init_observability(
    application_name: str = "hermes-agent-os",
    otlp_endpoint: Optional[str] = None,
    disable_batch: bool = True,
    **kwargs: Any,
) -> bool:
    """
    Initializes OpenLIT and OpenTelemetry auto-instrumentation and tracing.
    Can be called during harness boot or CLI initialization.
    Returns True if OpenLIT initialized successfully, False otherwise.
    """
    global _OBSERVABILITY_INITIALIZED
    if os.environ.get("HERMES_OTEL_DISABLED", "false").lower() in ("1", "true", "yes"):
        return False

    if _OBSERVABILITY_INITIALIZED:
        return True

    if OPENLIT_AVAILABLE and openlit is not None:
        endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
        try:
            openlit.init(
                otlp_endpoint=endpoint,
                application_name=application_name,
                disable_batch=disable_batch,
                **kwargs,
            )
            _OBSERVABILITY_INITIALIZED = True
            return True
        except Exception:
            pass

    return False


def get_trajectory_tracer(name: str = "hermes.trajectory") -> Optional[Any]:
    """Returns the OpenTelemetry tracer if available and enabled."""
    if os.environ.get("HERMES_OTEL_DISABLED", "false").lower() in ("1", "true", "yes"):
        return None
    if OPENTELEMETRY_AVAILABLE and trace is not None:
        try:
            return trace.get_tracer(name)
        except Exception:
            return None
    return None


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
    """
    Appends hash-chained events to the shared append-only JSONL stream
    and emits OpenTelemetry / OpenLIT custom spans for each sealed event.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        path: Optional[Path] = None,
        enable_otel: Optional[bool] = None,
        tracer: Optional[Any] = None,
    ):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.path = Path(path) if path else active_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if enable_otel is False or os.environ.get("HERMES_OTEL_DISABLED", "false").lower() in ("1", "true", "yes"):
            self.tracer = None
        else:
            self.tracer = tracer if tracer is not None else get_trajectory_tracer("hermes.trajectory")

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
        event = {"seq": self._next_seq(), "ts": int(time.time() * 1000), "session": self.session_id}
        unknown_type = fields.get("event") not in EVENT_TYPES
        if unknown_type and "event" in fields:
            raise ValueError(f"unknown trajectory event type: {fields.get('event')}")
        event.update(fields)
        sealed = _seal(event, self._tail_hash())
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(_canonical(sealed) + "\n")

        # Emit OpenTelemetry custom span wrapping the hash chain event
        self._emit_otel_span(sealed)

        return sealed

    def _emit_otel_span(self, sealed: Dict[str, Any]) -> None:
        """Emits an OTel custom span capturing hash-chain metadata and event payload."""
        if not self.tracer:
            return
        event_type = sealed.get("event", "unknown")
        span_name = f"hermes.trajectory.{event_type}"
        try:
            with self.tracer.start_as_current_span(span_name) as span:
                span.set_attribute("hermes.session", str(self.session_id))
                span.set_attribute("hermes.seq", sealed.get("seq", 0))
                span.set_attribute("hermes.hash", sealed.get("hash", ""))
                span.set_attribute("hermes.prev", sealed.get("prev", ""))
                span.set_attribute("hermes.event_type", event_type)
                span.set_attribute("hermes.ts", sealed.get("ts", 0))

                for k, v in sealed.items():
                    if k in ("session", "seq", "hash", "prev", "event", "ts"):
                        continue
                    if isinstance(v, (bool, str, int, float)):
                        span.set_attribute(f"hermes.{k}", v)
                    else:
                        span.set_attribute(f"hermes.{k}", json.dumps(v))

                # Standard LLM semantic conventions for prompt_tokens if present
                if "prompt_tokens" in sealed and isinstance(sealed["prompt_tokens"], int):
                    span.set_attribute("gen_ai.usage.prompt_tokens", sealed["prompt_tokens"])
                    span.set_attribute("llm.usage.prompt_tokens", sealed["prompt_tokens"])

                # Error & Gate status annotations
                if event_type == "test_result" and not sealed.get("test_passed", True):
                    if Status and StatusCode:
                        span.set_status(Status(StatusCode.ERROR, description="test_failed"))
                elif event_type == "gate_check" and sealed.get("gate_status") == "REJECT":
                    if Status and StatusCode:
                        span.set_status(
                            Status(StatusCode.ERROR, description=str(sealed.get("reason", "gate_rejected")))
                        )
                elif event_type == "tool_result" and not sealed.get("result_ok", True):
                    if Status and StatusCode:
                        span.set_status(Status(StatusCode.ERROR, description="tool_result_failed"))
                else:
                    if Status and StatusCode:
                        span.set_status(Status(StatusCode.OK))
        except Exception:
            pass

    @contextmanager
    def trace_span(self, event: str, **fields: Any) -> Iterator[Dict[str, Any]]:
        """
        Context manager wrapping an operation in an OTel custom span,
        auto-appending a hash-chained trajectory event upon completion.
        Yields a dict that the caller can mutate before completion.
        """
        span_fields = dict(fields)
        span_fields["event"] = event
        tracer = self.tracer or get_trajectory_tracer()
        span_name = f"hermes.trajectory.{event}"

        if tracer and trace is not None:
            with tracer.start_as_current_span(span_name) as span:
                try:
                    yield span_fields
                except Exception as exc:
                    span_fields["error"] = str(exc)
                    if Status and StatusCode:
                        span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                    raise
                finally:
                    # Prevent duplicate nested span emission
                    prev_tracer = self.tracer
                    self.tracer = None
                    try:
                        sealed = self.append(**span_fields)
                    finally:
                        self.tracer = prev_tracer

                    span.set_attribute("hermes.session", str(self.session_id))
                    span.set_attribute("hermes.seq", sealed.get("seq", 0))
                    span.set_attribute("hermes.hash", sealed.get("hash", ""))
                    span.set_attribute("hermes.prev", sealed.get("prev", ""))
                    span.set_attribute("hermes.event_type", event)
                    for k, v in sealed.items():
                        if k not in ("session", "seq", "hash", "prev", "event", "ts"):
                            if isinstance(v, (bool, str, int, float)):
                                span.set_attribute(f"hermes.{k}", v)
                            else:
                                span.set_attribute(f"hermes.{k}", json.dumps(v))
        else:
            try:
                yield span_fields
            finally:
                self.append(**span_fields)

    def _next_seq(self) -> int:
        last = self._read_last_event()
        return (last["seq"] + 1) if last else 0

    # -- typed helpers ---------------------------------------------------
    def record_turn(self, turn: int, role: str, prompt_tokens: int = 0, **extra: Any) -> Dict[str, Any]:
        return self.append(event="turn_start", turn=turn, role=role, prompt_tokens=prompt_tokens, **extra)

    def record_tool_call(self, turn: int, role: str, tool: str, args_head: str = "", **extra: Any) -> Dict[str, Any]:
        return self.append(event="tool_call", turn=turn, role=role, tool=tool, args_head=str(args_head)[:200], **extra)

    def record_gate(self, turn: int, tool: str, gate_status: str, reason: str = "", **extra: Any) -> Dict[str, Any]:
        return self.append(
            event="gate_check", turn=turn, tool=tool, gate_status=gate_status, reason=str(reason)[:300], **extra
        )

    def record_tool_result(
        self, turn: int, tool: str, result_head: str = "", result_ok: bool = True, **extra: Any
    ) -> Dict[str, Any]:
        return self.append(
            event="tool_result",
            turn=turn,
            tool=tool,
            result_head=str(result_head)[:300],
            result_ok=bool(result_ok),
            **extra,
        )

    def record_test(self, turn: int, test_passed: bool, command: str = "", **extra: Any) -> Dict[str, Any]:
        return self.append(
            event="test_result", turn=turn, test_passed=bool(test_passed), command=command[:200], **extra
        )


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


def events_to_otel_spans(events: List[Dict[str, Any]], tracer: Optional[Any] = None) -> int:
    """
    Exports an existing list of hash-chained trajectory events as OTel custom spans.
    Useful for replaying, inspecting, or exporting historical trajectory streams to OTel collectors.
    """
    t = tracer or get_trajectory_tracer("hermes.trajectory.replay")
    if not t:
        return 0
    exported = 0
    for ev in events:
        event_type = ev.get("event", "unknown")
        span_name = f"hermes.trajectory.{event_type}"
        with t.start_as_current_span(span_name) as span:
            span.set_attribute("hermes.seq", ev.get("seq", 0))
            span.set_attribute("hermes.hash", ev.get("hash", ""))
            span.set_attribute("hermes.prev", ev.get("prev", ""))
            span.set_attribute("hermes.event_type", event_type)
            for k, v in ev.items():
                if k not in ("seq", "hash", "prev", "event"):
                    if isinstance(v, (bool, str, int, float)):
                        span.set_attribute(f"hermes.{k}", v)
                    else:
                        span.set_attribute(f"hermes.{k}", json.dumps(v))
            exported += 1
    return exported


def flush_to_milestone_disk(target: Optional[Path] = None, source: Optional[Path] = None) -> Dict[str, Any]:
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
        with open(dst, "a", encoding="utf-8") as out, open(src, "r", encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if not s:
                    continue
                try:
                    body = {k: v for k, v in json.loads(s).items() if k not in ("prev", "hash")}
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
    return {
        "target": str(dst),
        "bytes_on_disk": flushed,
        "events_merged": merged,
        "malformed_skipped": skipped,
        "chain_valid_after_merge": ok,
        "nocow_applied": chattr is not None and chattr.returncode == 0,
    }


__all__ = [
    "TrajectoryRecorder",
    "init_observability",
    "get_trajectory_tracer",
    "load_events",
    "verify_chain",
    "flush_to_milestone_disk",
    "events_to_otel_spans",
    "active_path",
    "OPENLIT_AVAILABLE",
    "OPENTELEMETRY_AVAILABLE",
    "EVENT_TYPES",
]


if __name__ == "__main__":
    init_observability()
    rec = TrajectoryRecorder(session_id="demo")
    rec.record_turn(turn=1, role="coder", prompt_tokens=1420)
    rec.record_gate(turn=1, tool="patch", gate_status="PASS")
    rec.record_test(turn=1, test_passed=True, command="pytest -q")
    ok, detail = verify_chain()
    print(ok, "|", detail)
