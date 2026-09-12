#!/usr/bin/env python3
"""
Horizon 2 In-Process Verification Harness: Ponytail Minimalist Engineering
& Anti-Overengineering Guardrails (7-Rung YAGNI Ladder, AST Diff Pruner,
Unrequested Dependency Rejection, Root-Cause Call Graph Invariants)
==========================================================================
Verifies:
  1. Direct Prompt Injection of 7-Rung YAGNI Ladder & Root-Cause Remediation Invariant
  2. Ponytail 7-Rung Ladder Intent Classification (Rung 1 to Rung 7)
  3. AST Diff Size Calculation & Bloat Rejection (>3x Surgical Limit)
  4. Redundant Helper Function & Passthrough Pruning
  5. Unrequested 3rd-Party Dependency Rejection (YAGNI Rung 5)
  6. Root-Cause Call-Graph Invariant (Earliest Point of Divergence vs Caller Band-Aids)
  7. Observer Gate Pre-Commit Hook & CLI Integration
"""

import json
import os
import sys
from pathlib import Path

# Add active hermes-agent paths
for p in [
    Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/hermes-agent"),
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.ponytail_ladder import (
    YAGNIRung,
    BloatSeverity,
    BloatViolation,
    DiffAuditReport,
    PonytailDiffPruner,
    PonytailLadder,
    audit_code_simplicity,
    pre_commit_observer_gate,
)
from agent.prompt_builder import PONYTAIL_LADDER_GUIDANCE


def verify_prompt_injection() -> None:
    print("[1/7] Verifying 7-Rung YAGNI Ladder & Root-Cause Invariant prompt injection...")
    assert PONYTAIL_LADDER_GUIDANCE, "PONYTAIL_LADDER_GUIDANCE must be non-empty"
    assert "7-Rung YAGNI Ladder" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 1 (YAGNI)" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 2 (Codebase Reuse)" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 3 (Standard Library)" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 4 (Native OS / Platform)" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 5 (Installed Dependency)" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 6 (Single-Line Expression)" in PONYTAIL_LADDER_GUIDANCE
    assert "Rung 7 (Minimal Code)" in PONYTAIL_LADDER_GUIDANCE
    assert "Root-Cause Remediation Invariant" in PONYTAIL_LADDER_GUIDANCE
    assert "earliest point of divergence" in PONYTAIL_LADDER_GUIDANCE

    # Verify system_prompt imports and exposes guidance
    import agent.system_prompt as sys_p
    assert hasattr(sys_p, "PONYTAIL_LADDER_GUIDANCE"), "system_prompt must import PONYTAIL_LADDER_GUIDANCE"
    print("  ✓ 7-Rung YAGNI Ladder and Root-Cause Invariant verified in core system prompt.")


def verify_7_rung_ladder() -> None:
    print("[2/7] Verifying Ponytail 7-Rung Ladder classification across full spectrum...")
    # Rung 1: YAGNI
    r1, note1 = PonytailLadder.evaluate_intent("Add a futuristic abstraction layer just in case we need it later")
    assert r1 == YAGNIRung.RUNG_1_YAGNI, f"Expected Rung 1, got {r1}"
    assert "Do not build" in note1

    # Rung 2: Codebase Reuse
    r2, note2 = PonytailLadder.evaluate_intent(
        "Generate cryptographic signature using faraday_director",
        existing_symbols=["faraday_director", "loop_orchestrator"]
    )
    assert r2 == YAGNIRung.RUNG_2_CODEBASE_REUSE, f"Expected Rung 2, got {r2}"
    assert "faraday_director" in note2

    # Rung 3: Standard Library
    r3, note3 = PonytailLadder.evaluate_intent("Manipulate paths and read JSON file content")
    assert r3 == YAGNIRung.RUNG_3_STDLIB, f"Expected Rung 3, got {r3}"
    assert "Standard library" in note3

    # Rung 4: Native OS
    r4, note4 = PonytailLadder.evaluate_intent("Find files matching pattern via grep and tar archive")
    assert r4 == YAGNIRung.RUNG_4_NATIVE_OS, f"Expected Rung 4, got {r4}"
    assert "Native OS" in note4

    # Rung 5: Installed Dependency
    r5, note5 = PonytailLadder.evaluate_intent("Validate schema structure with sympy", installed_packages=["sympy"])
    assert r5 == YAGNIRung.RUNG_5_DEPENDENCY, f"Expected Rung 5, got {r5}"
    assert "sympy" in note5

    # Rung 6: Single-Line
    r6, note6 = PonytailLadder.evaluate_intent("Filter and map user IDs from response list")
    assert r6 == YAGNIRung.RUNG_6_ONE_LINE, f"Expected Rung 6, got {r6}"

    # Rung 7: Minimal Working Code
    r7, note7 = PonytailLadder.evaluate_intent("Synthesize optimized draft decoding tree kernel")
    assert r7 == YAGNIRung.RUNG_7_MINIMAL_CODE, f"Expected Rung 7, got {r7}"
    print("  ✓ Full 7-Rung YAGNI ladder accurately evaluates requirements from Rung 1 to Rung 7.")


def verify_ast_diff_size_gate() -> None:
    print("[3/7] Verifying AST diff size gate (Karpathy U12 3x surgical limit)...")
    old_code = """
def calculate_tax(subtotal: float) -> float:
    return subtotal * 0.05
"""
    # Over-engineered 20-line class replacing 2-line function (>3x surgical bloat)
    bloated_new_code = """
class TaxCalculationStrategyManager:
    def __init__(self, rate: float = 0.05):
        self.rate = rate

    def get_rate(self) -> float:
        return self.rate

    def set_rate(self, new_rate: float) -> None:
        self.rate = new_rate

    def calculate_tax(self, subtotal: float) -> float:
        if subtotal < 0:
            raise ValueError("Negative subtotal not permitted")
        tax_amount = subtotal * self.get_rate()
        return round(tax_amount, 2)
"""
    pruner = PonytailDiffPruner(strict_mode=True)
    report = pruner.audit_diff(old_code, bloated_new_code)
    assert not report.passed, "Bloated replacement should be rejected"
    assert report.verdict == "REJECTED"
    assert any(v.rule == "ast_diff_bloat" for v in report.violations), "Must detect ast_diff_bloat"
    assert report.diff_ratio > 3.0, f"Diff ratio {report.diff_ratio} should exceed 3.0"

    # Surgical minimal fix replacing function
    surgical_new_code = """
def calculate_tax(subtotal: float) -> float:
    return round(subtotal * 0.05, 2) if subtotal >= 0 else 0.0
"""
    surgical_report = pruner.audit_diff(old_code, surgical_new_code)
    assert surgical_report.passed, f"Surgical patch must pass: {surgical_report.violations}"
    assert surgical_report.verdict == "APPROVED"
    print("  ✓ AST diff size gate correctly blocks bloated expansions and approves surgical fixes.")


def verify_redundant_helper_pruning() -> None:
    print("[4/7] Verifying redundant helper function pruning...")
    old_code = """
def parse_int(raw: str) -> int:
    return int(raw.strip())
"""
    # Patch introduces an unnecessary wrapper function around standard library/builtins
    patch_with_redundant_helper = """
def _get_length(s: str) -> int:
    return len(s)

def parse_int(raw: str) -> int:
    if _get_length(raw) == 0:
        return 0
    return int(raw.strip())
"""
    res = pre_commit_observer_gate(old_code, patch_with_redundant_helper)
    assert not res["passed"], "Redundant helper function should trigger gate rejection"
    assert "_get_length" in res["report"]["redundant_helpers"]
    assert any(v["rule"] == "redundant_helper_function" for v in res["report"]["violations"])
    print("  ✓ Redundant helper functions successfully pruned at pre-commit gate.")


def verify_unrequested_dependency_rejection() -> None:
    print("[5/7] Verifying unrequested 3rd-party dependency rejection (YAGNI Rung 5)...")
    old_code = """
def fetch_data(url: str) -> str:
    import urllib.request
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')
"""
    # Patch introduces 'httpx' which is unrequested
    patch_with_unrequested_dep = """
import httpx

def fetch_data(url: str) -> str:
    response = httpx.get(url)
    return response.text
"""
    res = pre_commit_observer_gate(old_code, patch_with_unrequested_dep, requested_dependencies=[])
    assert not res["passed"], "Unrequested dependency 'httpx' must be rejected"
    assert "httpx" in res["report"]["unrequested_dependencies"]
    assert any(v["rule"] == "unrequested_dependency" for v in res["report"]["violations"])

    # When httpx is explicitly requested, gate approves
    res_approved = pre_commit_observer_gate(old_code, patch_with_unrequested_dep, requested_dependencies=["httpx"])
    assert res_approved["passed"], "Explicitly requested dependency should be approved"
    print("  ✓ Unrequested third-party dependency injection correctly rejected.")


def verify_root_cause_call_graph_invariant() -> None:
    print("[6/7] Verifying root-cause earliest divergence invariant (callee vs caller band-aids)...")
    old_code = """
def query_database(user_id: int) -> dict:
    if user_id == 0:
        return None
    return {"id": user_id, "name": "Alice"}

def render_profile(user_id: int) -> str:
    user = query_database(user_id)
    return f"<h1>{user['name']}</h1>"

def export_profile(user_id: int) -> str:
    user = query_database(user_id)
    return f"User:{user['name']}"
"""
    # Superficial caller-bandaid patch: instead of fixing query_database, developer wraps both callers!
    caller_bandaid_patch = """
def query_database(user_id: int) -> dict:
    if user_id == 0:
        return None
    return {"id": user_id, "name": "Alice"}

def render_profile(user_id: int) -> str:
    user = query_database(user_id)
    if user is None:
        return "<h1>Unknown</h1>"
    return f"<h1>{user['name']}</h1>"

def export_profile(user_id: int) -> str:
    user = query_database(user_id)
    if user is None:
        return "User:Unknown"
    return f"User:{user['name']}"
"""
    call_graph = {
        "query_database": ["render_profile", "export_profile"]
    }

    res_bandaid = pre_commit_observer_gate(
        old_code,
        caller_bandaid_patch,
        call_graph=call_graph,
        failing_symbol="query_database"
    )
    assert not res_bandaid["passed"], "Caller band-aids must be rejected when root callee is not remediated"
    assert not res_bandaid["report"]["root_cause_passed"]
    assert any(v["rule"] == "caller_bandaid_divergence" for v in res_bandaid["report"]["violations"])

    # Root-cause fix: Fixes query_database directly at the source
    root_cause_patch = """
def query_database(user_id: int) -> dict:
    if user_id == 0:
        return {"id": 0, "name": "Unknown"}
    return {"id": user_id, "name": "Alice"}

def render_profile(user_id: int) -> str:
    user = query_database(user_id)
    return f"<h1>{user['name']}</h1>"

def export_profile(user_id: int) -> str:
    user = query_database(user_id)
    return f"User:{user['name']}"
"""
    res_root = pre_commit_observer_gate(
        old_code,
        root_cause_patch,
        call_graph=call_graph,
        failing_symbol="query_database"
    )
    assert res_root["passed"], f"Root-cause remediation must be approved: {res_root['report']['violations']}"
    assert res_root["report"]["root_cause_passed"]
    print("  ✓ Root-cause invariant enforced: caller band-aids rejected, root fix approved.")


def verify_observer_gate_plugin_integration() -> None:
    print("[7/7] Verifying Observer Gate plugin and pre_commit_observer_gate integration...")
    from plugins.observer_gate import pre_commit_observer_gate as plugin_pc_gate
    old_code = "def add(a, b):\n    return a + b\n"
    new_code = "def add(a, b):\n    return int(a) + int(b)\n"
    res = plugin_pc_gate(old_code, new_code, filepath="math_util.py")
    assert res["passed"], "Clean patch should pass observer gate"
    assert res["verdict"] == "APPROVED"
    assert len(res["checks"]) >= 5
    print("  ✓ Observer Gate plugin pre_commit_observer_gate hook operational.")


def main():
    print("=" * 66)
    print("  HORIZON 2 IN-PROCESS VERIFICATION: PONYTAIL GUARDRAILS          ")
    print("  (7-Rung YAGNI Ladder, AST Diff Size, Dependency & Root-Cause)  ")
    print("=" * 66)

    verify_prompt_injection()
    verify_7_rung_ladder()
    verify_ast_diff_size_gate()
    verify_redundant_helper_pruning()
    verify_unrequested_dependency_rejection()
    verify_root_cause_call_graph_invariant()
    verify_observer_gate_plugin_integration()

    print("=" * 66)
    print("  ✅ HORIZON 2 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN   ")
    print("=" * 66)


if __name__ == "__main__":
    main()
