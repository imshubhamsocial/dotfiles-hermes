"""
Contract Tests: Quorum Cross-Model Consensus Gate & GEPA-Lite Optimizer
========================================================================
Validates:
1. Quorum structural separation (author != auditor).
2. Quorum blast radius & fitness gate calculations.
3. CogVerifier and DraftDetective Quorum audit integrations.
4. GEPA-Lite reflective Pareto optimization over candidates.
5. NVML memory reading in ContextWindowGuard.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from hermes_core.quorum_gate import QuorumAuditGate, BlastRadius, QuorumAuditReceipt
from hermes_core.gepa_optimizer import GEPALiteOptimizer, GEPACandidate
from hermes_core.cog_verifier import CogVerifier
from hermes_core.draft_detective import DraftDetective
from hermes_core.context_window_guard import ContextWindowGuard


def test_quorum_structural_separation():
    gate = QuorumAuditGate(enforce_distinct_auditor=True)
    # Same author and auditor should be rejected by structural rule
    receipt = gate.audit_step(
        task_id="t1",
        author_agent="agent_alpha",
        auditor_agent="agent_alpha",
        affected_files=[],
        ast_valid=True,
        tests_passed=True,
    )
    assert receipt.verdict == "REJECTED"
    assert any("cannot audit its own code" in r for r in receipt.rejection_reasons)


def test_quorum_successful_audit():
    gate = QuorumAuditGate(enforce_distinct_auditor=True, min_fitness_score=0.8)
    with tempfile.TemporaryDirectory() as td:
        test_py = Path(td) / "sample.py"
        test_py.write_text("def add(a, b):\n    return a + b\n")

        receipt = gate.audit_step(
            task_id="t2",
            author_agent="coder_agent",
            auditor_agent="verifier_agent",
            affected_files=[test_py],
            ast_valid=True,
            tests_passed=True,
            pass_rate=1.0,
            diff_text="+def add(a, b):\n+    return a + b\n",
        )
        assert receipt.verdict == "AGREED"
        assert receipt.fitness_score >= 0.8
        assert "sample.py" in str(receipt.blast_radius.files_changed)
        assert "add" in receipt.blast_radius.symbols_affected
        assert receipt.signature != ""


def test_cog_verifier_quorum_audit():
    with tempfile.TemporaryDirectory() as td:
        test_file = Path(td) / "mod.py"
        test_file.write_text("class Calculator:\n    def compute(self):\n        return 100\n")

        verifier = CogVerifier(verifier_name="audit_specialist")
        receipt = verifier.quorum_audit(
            task_id="t3",
            author_agent="worker_bot",
            affected_files=[str(test_file)],
        )
        assert receipt.auditor == "audit_specialist"
        assert receipt.author == "worker_bot"
        assert receipt.signature != ""


def test_draft_detective_quorum_audit():
    dd = DraftDetective()
    result = dd.quorum_pre_commit_audit(
        markdown_summary="Implemented feature `Calculator` in `calculator.py`",
        code_diff="def test():\n    return True\n",
        author_agent="coder",
        auditor_agent="reviewer",
    )
    assert "quorum_receipt" in result
    assert result["quorum_receipt"]["author"] == "coder"
    assert result["quorum_receipt"]["auditor"] == "reviewer"


def test_gepa_lite_optimization():
    optimizer = GEPALiteOptimizer(exploit_prob=0.8, not_merge_prob=0.5)
    pareto_data = [
        {"input": "sort numbers", "expected": "def sort_nums(arr): return sorted(arr)"},
        {"input": "reverse text", "expected": "def rev(s): return s[::-1]"},
    ]

    seed = "Please note that you should kindly write Python code to satisfy user requirements."
    result = optimizer.run_optimization(
        seed_prompt=seed,
        pareto_dataset=pareto_data,
        max_generations=3,
        population_size=3,
    )

    assert result.best_prompt != ""
    assert result.generations_run == 3
    assert result.pool_size >= 3
    # Verify filler phrases pruned in mutation
    assert "Please note that " not in result.best_prompt


def test_context_window_guard_nvml():
    guard = ContextWindowGuard()
    info = guard.get_detailed_vram_info()
    assert "total_mib" in info
    assert "used_mib" in info
    assert "free_mib" in info
    assert info["hard_ceiling_mib"] == 4812
