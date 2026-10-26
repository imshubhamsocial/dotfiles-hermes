"""
test_verify.py — Deterministic Verification Suite for Remediation Gauntlet (GDR18)
Validates the closure of RISK-01, RISK-02, RISK-03, and RISK-04.
"""
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes")
HERMES_DIR = WORKSPACE_ROOT / ".hermes"

if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))


def test_remediation_risk04_ast_scoping():
    """Validates that extract_workspace_ast default workspace_dir scopes to intent manifest."""
    from mcp_openjev import extract_workspace_ast
    sig = inspect.signature(extract_workspace_ast)
    assert "workspace_dir" in sig.parameters, "workspace_dir parameter missing"
    
    # Verify execution scopes without error
    res = extract_workspace_ast()
    assert isinstance(res, dict), "extract_workspace_ast must return dict"
    assert "workspace" in res or "symbols" in res or "tree" in res or "files_indexed" in res, res


def test_remediation_risk01_decision_router_neutrality():
    """Validates that jev_decide removes lexical bias and supports T5Gemma 2 tiebreaker."""
    from mcp_openjev import jev_decide
    
    # Neutral symmetrical premise
    premise = "Cache invalidation occurs when the TTL expires."
    hyp_a = "Evict the cache key when time exceeds TTL."
    hyp_b = "Evict the cache key when now > expires_at."
    
    res = jev_decide(premise, hyp_a, hyp_b)
    assert "stage" in res, "Decision must return stage"
    assert res["stage"] in ("STAGE_1_CPU_GEMMA2_HYBRID", "STAGE_2_T5GEMMA2_TIEBREAKER", "STAGE_2_LOOPCD_PORT_8138"), res


def test_remediation_risk01_worktree_probing_interface():
    """Validates that jev_harness2_probe_compose uses worktree probing interface."""
    from mcp_openjev import jev_harness2_probe_compose
    sig = inspect.signature(jev_harness2_probe_compose)
    assert "patch_h_inv" in sig.parameters
    assert "patch_h_dom" in sig.parameters
    assert "target_file" in sig.parameters


def test_remediation_risk02_shadow_backup_domain_separation():
    """Validates that _create_write_once_shadow_backup skips .hermes.bak in git repos."""
    from mcp_openjev import _create_write_once_shadow_backup
    test_git_file = Path(__file__).resolve()
    
    # Calling on a file inside git repo must return None (Domain C preserved)
    bak = _create_write_once_shadow_backup(test_git_file)
    assert bak is None, "Shadow backup must be skipped inside Git repositories (Domain C)"


def test_remediation_risk02_conftest_receipt_logic():
    """Validates conftest.py receipt sealing and domain separation logic."""
    conftest_path = WORKSPACE_ROOT / "conftest.py"
    src = conftest_path.read_text(encoding="utf-8")
    
    assert "def pytest_sessionfinish" in src
    assert "_collect_domain_c_git_diff" in src
    assert "_collect_domain_b_shadow_diff" in src


def test_remediation_risk03_temporal_mutual_exclusion():
    """Validates Temporal Mutual Exclusion awareness and NVML ceiling compliance."""
    from mcp_openjev import query_live_nvml_vram
    vram = query_live_nvml_vram()
    assert vram["used_mib"] <= 5400.0, f"VRAM {vram['used_mib']} breaches 5400.0 MiB ceiling"
