"""
Domain 5 Security, Multi-Bot Delegation & Test-Time Compute Verification Suite
=============================================================================
Tests Bubblewrap sandbox isolation, Capability Masks, HITL risk interception,
and Multi-Candidate Test-Time Compute Sampler.
"""

import pytest
from hermes_core.sandbox import sanitize_output, SANDBOX_DENIAL_GUIDANCE
from hermes_core.capability_masks import ROLE_POLICIES, READ_ONLY_TOOLS
from hermes_core.hitl_gateway import assess_risk, RiskLevel
from hermes_core.test_time_sampler import TestTimeComputeSampler, CandidatePlan


def test_sandbox_output_sanitization():
    """Verify denial sanitization (Issue #01)."""
    raw_denial = "bwrap: loopback: Operation not permitted"
    sanitized = sanitize_output(raw_denial)
    assert sanitized == SANDBOX_DENIAL_GUIDANCE


def test_capability_masks_trinity_isolation():
    """Verify @architect, @coder, and @tester tool isolation (Issue #36)."""
    arch_tools = ROLE_POLICIES["architect"]
    assert "write_file" not in arch_tools
    assert "patch_file" not in arch_tools

    tester_tools = ROLE_POLICIES["tester"]
    assert "write_file" not in tester_tools
    assert "run_test_suite" in tester_tools


def test_hitl_critical_command_interception():
    """Verify high-risk command interception (Issue #38)."""
    assert assess_risk("shell_command", ".", "rm -rf /tmp/test") == RiskLevel.CRITICAL
    assert assess_risk("shell_command", ".", "sudo apt install vim") == RiskLevel.CRITICAL
    assert assess_risk("shell_command", ".", "pytest -q") == RiskLevel.LOW


def test_test_time_compute_candidate_scoring():
    """Verify multi-candidate election across dual slots (Issue #48)."""
    sampler = TestTimeComputeSampler(top_k=2)

    valid_candidate = CandidatePlan(
        candidate_id="cand_1",
        code_content="def add(a: int, b: int) -> int:\n    return a + b\n",
        thought_process="Clean type-annotated addition function",
        target_filepath="math_utils.py",
    )

    broken_candidate = CandidatePlan(
        candidate_id="cand_2",
        code_content="def add(a, b\n    return a + b\n",
        thought_process="Broken syntax candidate",
        target_filepath="math_utils.py",
    )

    best = sampler.elect_best_candidate([broken_candidate, valid_candidate])
    assert best is not None
    assert best.candidate_id == "cand_1"
    assert best.passed_ast is True
    assert best.score > 50.0
