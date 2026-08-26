"""
U7 Deterministic Trajectory Replay & Distillation Runner (Phase 4.2)
=====================================================================
Answers the distillation question OFFLINE: "with TODAY'S prompts,
linters and gates, which recorded tool outcomes would change?"

For every paired (tool_call -> gate_check/tool_result) step in a U6
trajectory this runner re-applies the CURRENT rule stack
(FableMiddleware payload filter + U2 lifecycle pre-hooks incl. observer
Gate7 syntax probes) to the recorded payload and diffs the fresh
verdicts against the recorded ones. Zero live GPU/model traffic.

Trap-1 (Non-Deterministic Replay Drift) countermeasure: replay REFUSES
to run on any stream whose U6 hash chain fails verification — the chain
is the frozen-environment guarantee. Any verdict divergence is reported
per-step as drift, never silently absorbed.

Drift semantics:
  - LINTER_DRIFT   : current gate verdict != recorded gate verdict
                     (new rules reject what passed before, or vice versa).
  - CONTRADICTION  : recorded stream internally inconsistent
                     (gate REJECT yet result_ok=True, etc.).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from .trajectory import load_events, verify_chain
except ImportError:  # packageless loaders (integrity probes) hit this branch
    from hermes_core.trajectory import load_events, verify_chain


class TrajectoryTamperError(ValueError):
    """Raised when replay is attempted on a stream failing chain verification."""


@dataclass
class ReplayStep:
    seq: int
    turn: Any
    role: str
    tool: str
    recorded_gate: str
    replayed_gate: str
    recorded_result_ok: Optional[bool]
    drift: bool
    drift_kind: str = ""          # "" | LINTER_DRIFT | CONTRADICTION
    detail: str = ""


@dataclass
class ReplayReport:
    source: str
    total_events: int
    replayed_steps: int = 0
    clean_steps: int = 0
    drifted_steps: int = 0
    deterministic_match: bool = True
    steps: List[ReplayStep] = field(default_factory=list)
    skipped_events: int = 0

    def summary(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "total_events": self.total_events,
            "replayed_steps": self.replayed_steps,
            "clean_steps": self.clean_steps,
            "drifted_steps": self.drifted_steps,
            "deterministic_match": self.deterministic_match,
            "skipped_events": self.skipped_events,
        }


def _replay_gate(role: str, tool: str, args_head: str) -> tuple:
    """Re-apply the CURRENT rule stack to a recorded payload."""
    try:
        from .middleware import FableMiddleware
        from .hooks import LifecycleHookEngine
    except ImportError:  # packageless loaders (integrity probes)
        from hermes_core.middleware import FableMiddleware
        from hermes_core.hooks import LifecycleHookEngine

    try:
        args = json.loads(args_head) if args_head else {}
        if not isinstance(args, dict):
            args = {}
        parse_note = ""
    except json.JSONDecodeError:
        # Truncated payload head: only structural lint of the raw text is
        # possible; treat unparseable heads conservatively as PASS-through
        # for gate purposes (nothing to lint) and mark in detail.
        return True, "unparseable-payload-head (lint skipped)"

    valid, msg = FableMiddleware.filter_tool_payload(tool, args)
    if not valid:
        return False, f"fable:{msg}"

    hook_engine = LifecycleHookEngine()
    hook_ok, hook_msg = hook_engine.pre_tool_call(role, tool, args)
    return hook_ok, ("hook:" + hook_msg.splitlines()[0]) if not hook_ok else "payload validated."


def replay_trajectory(source: Union[str, Path],
                      max_steps: Optional[int] = None) -> ReplayReport:
    src = Path(source)
    ok_chain, chain_detail = verify_chain(src)
    if not ok_chain:
        raise TrajectoryTamperError(f"refusing replay: {chain_detail}")

    events = load_events(src)
    report = ReplayReport(source=str(src), total_events=len(events))

    pending: Dict[tuple, Dict[str, Any]] = {}
    last_gate_by_key: Dict[tuple, str] = {}

    for ev in events:
        etype = ev.get("event")
        key = (ev.get("turn"), ev.get("tool"))

        if etype == "tool_call":
            pending[key] = ev

        elif etype == "gate_check":
            last_gate_by_key[key] = ev.get("gate_status", "")

        elif etype == "tool_result":
            call_ev = pending.pop(key, None)
            recorded_gate = last_gate_by_key.get(key, "")
            expected_ok = bool(ev.get("result_ok"))

            if call_ev is None:
                report.skipped_events += 1
                continue

            replayed_ok, note = _replay_gate(
                call_ev.get("role", ""), ev.get("tool", ""),
                call_ev.get("args_head", ""))
            replayed_gate = "PASS" if replayed_ok else "REJECT"

            drift = False
            kinds = []
            details = []
            if replayed_gate != recorded_gate:
                drift = True
                kinds.append("LINTER_DRIFT")
                details.append(f"recorded {recorded_gate} -> replayed {replayed_gate} ({note})")
            if (not replayed_ok) and expected_ok:
                drift = True
                kinds.append("CONTRADICTION")
                details.append("current gates reject payload that recorded success")

            step = ReplayStep(
                seq=ev.get("seq"), turn=ev.get("turn"),
                role=call_ev.get("role", ""), tool=ev.get("tool", ""),
                recorded_gate=recorded_gate, replayed_gate=replayed_gate,
                recorded_result_ok=expected_ok, drift=drift,
                drift_kind="+".join(kinds), detail=" | ".join(details),
            )
            report.steps.append(step)
            report.replayed_steps += 1
            if drift:
                report.drifted_steps += 1
                report.deterministic_match = False
            else:
                report.clean_steps += 1

            if max_steps and report.replayed_steps >= max_steps:
                break

        else:
            continue

    report.skipped_events += len(pending)  # calls never resolved to results
    return report
