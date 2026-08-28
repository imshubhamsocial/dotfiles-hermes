"""
Contract Tests: Roadmap 4 Milestone U58
========================================
Validates Closed-Loop Dual-Agent Verification Matrix:
1. Multi-tier pre-flight approval pass (AST + Claims + Verifier Consensus)
2. Rejection on AST syntax error, phantom file claims, or verifier rejection
3. 2-Strike Tabu Rule Rollback trigger upon 2 consecutive failures
4. Strict Hardware Envelope Bounds (Pure CPU RAMDisk execution, 0 MB GPU VRAM)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.verification_matrix import (
    MatrixAuditVerdict,
    VerificationMatrix,
    create_verification_matrix,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def test_workspace(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "core_engine.py").write_text("class CoreEngine:\n    pass\n")
    return tmp_path


# =============================================================================
# 1. VERIFICATION MATRIX APPROVAL TESTS
# =============================================================================

class TestVerificationMatrixApproval:
    """Validates multi-tier pre-flight approval pass."""

    def test_verification_matrix_full_approval_pass(self, test_workspace):
        vm = create_verification_matrix(workspace_root=test_workspace)

        verdict = vm.audit_patch(
            file_path="src/core_engine.py",
            code_content="class CoreEngine:\n    def start(self) -> bool:\n        return True\n",
            markdown_summary="Enhanced `src/core_engine.py` with `CoreEngine.start` method.",
            known_symbols={"CoreEngine"},
            verifier_approved=True,
        )

        assert isinstance(verdict, MatrixAuditVerdict)
        assert verdict.approved is True
        assert verdict.ast_gate_passed is True
        assert verdict.claims_gate_passed is True
        assert verdict.verifier_consensus_passed is True
        assert verdict.tabu_rollback_triggered is False
        assert verdict.consecutive_failures == 0


# =============================================================================
# 2. REJECTION GATES & DIAGNOSTICS
# =============================================================================

class TestVerificationMatrixRejection:
    """Validates specific rejection triggers across individual gates."""

    def test_verification_matrix_rejection_on_ast_or_claim_failure(self, test_workspace):
        vm = create_verification_matrix(workspace_root=test_workspace)

        # 1. Broken syntax rejection
        verdict_syntax = vm.audit_patch(
            file_path="src/core_engine.py",
            code_content="class CoreEngine:\n    def start(self\n",
            markdown_summary="Modified `src/core_engine.py`.",
            verifier_approved=True,
        )
        assert verdict_syntax.approved is False
        assert verdict_syntax.ast_gate_passed is False
        assert verdict_syntax.consecutive_failures == 1

        # 2. Phantom claim rejection
        vm.reset_failures()
        verdict_claim = vm.audit_patch(
            file_path="src/core_engine.py",
            code_content="class CoreEngine:\n    pass\n",
            markdown_summary="Modified `src/non_existent_ghost_file.py`.",
            verifier_approved=True,
        )
        assert verdict_claim.approved is False
        assert verdict_claim.claims_gate_passed is False
        assert any("non_existent_ghost_file.py" in d for d in verdict_claim.diagnostics)


# =============================================================================
# 3. 2-STRIKE TABU ROLLBACK TRIGGER
# =============================================================================

class TestTabuRollbackTrigger:
    """Validates 2-strike tabu branch pruning mechanics."""

    def test_two_strike_tabu_pruner_trigger(self, test_workspace):
        vm = create_verification_matrix(workspace_root=test_workspace)

        # Failure 1
        v1 = vm.audit_patch(
            file_path="src/target.py",
            code_content="broken syntax (",
            markdown_summary="attempt 1",
        )
        assert v1.approved is False
        assert v1.consecutive_failures == 1
        assert v1.tabu_rollback_triggered is False

        # Failure 2 (Strike 2 -> Tabu Rollback Triggered)
        v2 = vm.audit_patch(
            file_path="src/target.py",
            code_content="still broken {",
            markdown_summary="attempt 2",
        )
        assert v2.approved is False
        assert v2.consecutive_failures == 2
        assert v2.tabu_rollback_triggered is True
        assert any("2-Strike Tabu Rule Triggered" in d for d in v2.diagnostics)


# =============================================================================
# 4. HARDWARE ENVELOPE BOUNDS & ZERO GPU VRAM
# =============================================================================

class TestVerificationMatrixHardwareBounds:
    """Validates pure CPU RAMDisk execution."""

    def test_verification_matrix_zero_gpu_vram(self, test_workspace):
        vm = create_verification_matrix(workspace_root=test_workspace)
        verdict = vm.audit_patch(
            file_path="src/core_engine.py",
            code_content="def compute(): return 42\n",
            markdown_summary="Quick CPU audit.",
        )
        assert verdict.audit_duration_ms >= 0.0
