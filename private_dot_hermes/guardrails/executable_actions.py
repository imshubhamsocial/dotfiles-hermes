#!/usr/bin/env python3.13
"""Deterministic Python Action Bindings for NVIDIA NeMo Guardrails v0.11+ / v0.24+."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from nemoguardrails.actions import action

HERMES_DIR = Path(__file__).resolve().parent.parent
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

import mcp_openjev

ZERO_TEST_RE = re.compile(r"(?:Ran\s+0\s+tests|collected\s+0\s+items|no\s+tests\s+ran)", re.IGNORECASE)
VICTORY_CLAIM_RE = re.compile(r"(?:all\s+tests\s+pass|verification\s+complete|100%\s+passed|task\s+complete)", re.IGNORECASE)


@action(is_system_action=True)
async def check_input_security_action(text: str = "") -> dict[str, Any]:
    return mcp_openjev.sanitize_and_audit_input(raw_text=text or "")


@action(is_system_action=True)
async def check_retrieval_poisoning_action(chunks: Any = None) -> dict[str, Any]:
    text = json.dumps(chunks) if not isinstance(chunks, str) else (chunks or "")
    res = mcp_openjev.sanitize_and_audit_input(raw_text=text)
    return {"passed": bool(res.get("security_passed", True))}


@action(is_system_action=True)
async def enforce_u12_and_tabu_action(
    tool_name: str = "patch",
    diff_lines: int = 0,
    strike_count: int = 0,
    ast_callers: int = 0,
    target_file: str = "",
    workspace_dir: str = ".",
) -> dict[str, Any]:
    u12_passed = int(diff_lines or 0) <= 15
    tabu_reverted = False
    if int(strike_count or 0) >= 2 and target_file:
        ws_path = Path(workspace_dir).resolve()
        target_path = (ws_path / target_file).resolve()
        ws_hash = mcp_openjev._workspace_hash(str(ws_path))
        backup_dir = mcp_openjev.ACTIVE_HERMES_HOME / "cache" / "shadow_backups" / ws_hash
        disambig_bak, legacy_bak = mcp_openjev._resolve_turn1_backup_paths(backup_dir, target_path)
        active_bak = disambig_bak if disambig_bak.is_file() else legacy_bak
        if active_bak.is_file() and target_path.is_file():
            target_path.write_bytes(active_bak.read_bytes())
            tabu_reverted = True
    decision_gate = None
    if int(strike_count or 0) >= 1 or int(ast_callers or 0) >= 3:
        decision_gate = mcp_openjev.jev_decide(
            premise=f"High-uncertainty mutation on {target_file or tool_name}",
            hypothesis_a="Apply surgical AST-verified patch preserving caller contracts",
            hypothesis_b="Abort mutation and run Spec-Kit cluster annealing",
            action_type="mutate",
            strike_count=int(strike_count or 0),
            diff_lines=int(diff_lines or 0),
            ast_callers=int(ast_callers or 0),
            workspace_dir=workspace_dir,
        )
    return {
        "u12_passed": u12_passed,
        "tabu_reverted": tabu_reverted,
        "decision_gate": decision_gate,
    }


@action(is_system_action=True)
async def verify_epistemic_receipt_action(
    bot_response: str = "",
    last_tool_output: str = "",
    workspace_dir: str = ".",
) -> dict[str, Any]:
    combined = f"{bot_response or ''}\n{last_tool_output or ''}"
    if ZERO_TEST_RE.search(combined):
        return {"verified": False, "reason": "vacuous_test_execution"}
    if VICTORY_CLAIM_RE.search(bot_response or ""):
        receipt_path = Path("/tmp/hermes_verified_receipt.json")
        if receipt_path.is_file():
            try:
                data = json.loads(receipt_path.read_text(encoding="utf-8"))
                if data.get("exitstatus") != 0:
                    return {"verified": False, "reason": "receipt_nonzero_exit"}
            except Exception:  # noqa: BLE001
                return {"verified": False, "reason": "corrupt_receipt"}
    return {"verified": True, "reason": "ok"}
