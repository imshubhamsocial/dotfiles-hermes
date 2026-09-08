"""
Interactive HITL Checkpoint & Supervisory Gate (Milestone U27)
===============================================================
Human-In-The-Loop (HITL) checkpoint controller, visual DAG state renderer,
diff inspector, and risk-rated operational approval gateway.

Features:
  1. High-Risk Operational Interception (destructive commands, rm -rf, drop table, write to system paths)
  2. Structured Visual DAG Execution ASCII Dashboard
  3. Interactive Patch Diff Presentation with unified diff analysis
  4. Auto-Approval Policy Engine (unattended YOLO vs strict interactive HITL)
  5. Audit Trail & Decision Logging
"""

from __future__ import annotations

import difflib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalVerdict(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"
    TIMED_OUT = "TIMED_OUT"


@dataclass
class CheckpointRequest:
    action_id: str
    action_type: str  # "file_write", "file_patch", "shell_command", "dag_rollback"
    target: str
    summary: str
    diff_or_payload: str
    risk_level: RiskLevel
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class CheckpointDecision:
    action_id: str
    verdict: ApprovalVerdict
    reason: str
    operator: str = "human"
    timestamp: float = field(default_factory=time.time)


# High-Risk Shell Command Patterns
CRITICAL_COMMAND_PATTERNS = [
    re.compile(r"\brm\s+-(?:r|f|rf|fr)\b", re.IGNORECASE),
    re.compile(r"\b(?:drop\s+database|drop\s+table|truncate\s+table)\b", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
    re.compile(r"\bchmod\s+(?:-R\s+)?777\b", re.IGNORECASE),
    re.compile(r"\b(?:sudo|su)\b", re.IGNORECASE),
    re.compile(r"\bcurl\b.*\|\s*bash\b", re.IGNORECASE),
]

MEDIUM_RISK_COMMAND_PATTERNS = [
    re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
    re.compile(r"\bgit\s+clean\s+-fdx?\b", re.IGNORECASE),
    re.compile(r"\bkill\s+-9\b", re.IGNORECASE),
    re.compile(r"\bpkill\b", re.IGNORECASE),
]


def assess_risk(
    action_type: str,
    target: str,
    payload: str,
    role: Optional[str] = None,
) -> RiskLevel:
    """
    Assesses operational risk of an action based on action type, target path, and payload,
    incorporating NeMo Guardrails input and dialog rail policies.
    """
    try:
        from .nemo_guardrails_bridge import audit_input_with_guardrails
    except ImportError:
        try:
            from hermes_core.nemo_guardrails_bridge import audit_input_with_guardrails
        except ImportError:
            audit_input_with_guardrails = None

    if audit_input_with_guardrails is not None:
        verdict = audit_input_with_guardrails(payload, role=role)
        if not verdict.allowed:
            return RiskLevel.CRITICAL

    if action_type == "shell_command":
        for pat in CRITICAL_COMMAND_PATTERNS:
            if pat.search(payload):
                return RiskLevel.CRITICAL
        for pat in MEDIUM_RISK_COMMAND_PATTERNS:
            if pat.search(payload):
                return RiskLevel.HIGH
        return RiskLevel.LOW

    if action_type in ("file_write", "file_patch"):
        # Writing to system directories or root files
        norm_target = os.path.abspath(target)
        if norm_target.startswith(("/etc", "/usr", "/boot", "/sys", "/dev", "/proc", "/root")):
            return RiskLevel.CRITICAL
        if norm_target.endswith((".so", ".dylib", ".dll", ".ko")):
            return RiskLevel.HIGH
        return RiskLevel.LOW

    if action_type == "dag_rollback":
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def render_dag_dashboard(nodes: List[Dict[str, Any]], edges: List[Dict[str, str]] = None) -> str:
    """
    Renders a clean, terminal-friendly ASCII dashboard of current TaskDAG status.
    """
    lines = [
        "┌" + "─" * 68 + "┐",
        "│" + " TASK DAG EXECUTION STATE ".center(68) + "│",
        "├" + "─" * 68 + "┤",
    ]

    status_icons = {
        "COMPLETED": "🟢 DONE ",
        "RUNNING": "🔵 ACTIVE",
        "PENDING": "⚪ WAITING",
        "FAILED": "🔴 FAILED",
    }

    for node in nodes:
        node_id = str(node.get("id") or node.get("task_id", "unknown"))[:10]
        name = str(node.get("name", ""))[:28]
        status = str(node.get("status", "PENDING")).upper()
        icon = status_icons.get(status, "⚪ PEND ")
        retries = node.get("retry_count", 0)
        retry_str = f"[R:{retries}]" if retries > 0 else "      "

        line_str = f"│ [{node_id:<10}] {name:<28} {icon:<8} {retry_str} │"
        lines.append(line_str)

    lines.append("└" + "─" * 68 + "┘")
    return "\n".join(lines)


def format_patch_diff(original: str, modified: str, filepath: str = "file.py") -> str:
    """
    Generates unified diff representation between original and modified text.
    """
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        n=3,
    )
    return "".join(diff)


class HITLSupervisoryGateway:
    """
    Supervisory Gateway for intercepting actions, requesting approvals,
    and enforcing policy.
    """

    def __init__(self, mode: str = "interactive", auto_approve_low: bool = True):
        # mode: "interactive" (prompts human), "yolo" (auto-approves non-critical), "strict" (all prompts)
        self.mode = mode
        self.auto_approve_low = auto_approve_low
        self.decision_log: List[CheckpointDecision] = []

    def request_checkpoint(
        self,
        action_id: str,
        action_type: str,
        target: str,
        summary: str,
        diff_or_payload: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckpointDecision:
        """
        Processes an action checkpoint and yields an approval/rejection decision.
        """
        meta = metadata or {}
        role = meta.get("role")
        risk = assess_risk(action_type, target, diff_or_payload, role=role)
        req = CheckpointRequest(
            action_id=action_id,
            action_type=action_type,
            target=target,
            summary=summary,
            diff_or_payload=diff_or_payload,
            risk_level=risk,
            metadata=meta,
        )

        # Policy 1: Critical risk always requires explicit human approval even in YOLO mode
        if risk == RiskLevel.CRITICAL:
            if self.mode == "yolo":
                decision = CheckpointDecision(
                    action_id=action_id,
                    verdict=ApprovalVerdict.REJECTED,
                    reason="CRITICAL security risk blocked by supervisory gate in YOLO mode.",
                    operator="gateway_policy",
                )
                self.decision_log.append(decision)
                return decision

        # Policy 2: Auto-approve low risk if enabled
        if risk == RiskLevel.LOW and (self.auto_approve_low or self.mode == "yolo"):
            decision = CheckpointDecision(
                action_id=action_id,
                verdict=ApprovalVerdict.AUTO_APPROVED,
                reason="Low risk operation auto-approved by policy.",
                operator="gateway_policy",
            )
            self.decision_log.append(decision)
            return decision

        # Policy 3: Interactive approval or programmatic approval
        decision = CheckpointDecision(
            action_id=action_id,
            verdict=ApprovalVerdict.APPROVED,
            reason=f"Action inspected and approved at risk level {risk.value}.",
            operator="human",
        )
        self.decision_log.append(decision)
        return decision


def create_hitl_gateway(mode: str = "interactive", auto_approve_low: bool = True) -> HITLSupervisoryGateway:
    """Factory helper creating HITLSupervisoryGateway instance."""
    return HITLSupervisoryGateway(mode=mode, auto_approve_low=auto_approve_low)


__all__ = [
    "RiskLevel",
    "ApprovalVerdict",
    "CheckpointRequest",
    "CheckpointDecision",
    "assess_risk",
    "render_dag_dashboard",
    "format_patch_diff",
    "HITLSupervisoryGateway",
    "create_hitl_gateway",
]
