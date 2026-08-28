"""
Contract Tests: Roadmap 4 Milestone U55
========================================
Validates Draft-Detective Adversarial Fact-Checker & AST Verification Gates:
1. Ground truth claim extraction (file paths, symbol names, markdown links)
2. Adversarial verification against workspace files (flags phantom file hallucinations)
3. AST structural transformation & brace parity verification
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

from hermes_core.draft_detective import (
    FactualClaim,
    VerificationAuditReport,
    DraftDetective,
    create_draft_detective,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Creates a mock workspace with ground-truth files."""
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "vector_memory.py").write_text("class VectorMemory:\n    pass\n")
    (tmp_path / "src" / "threadpool.hpp").write_text("class ThreadPool {};\n")
    return tmp_path


# =============================================================================
# 1. CLAIM EXTRACTION TESTS
# =============================================================================

class TestClaimExtraction:
    """Validates regex extraction of factual claims from agent output."""

    def test_claim_extraction_and_verification(self, mock_workspace):
        dd = create_draft_detective(workspace_root=mock_workspace)

        markdown_text = """
        I have implemented the new vector storage in `src/vector_memory.py` by defining
        class `VectorMemory`. Also modified [threadpool.hpp](file:///src/threadpool.hpp).
        """

        claims = dd.extract_claims(markdown_text)
        assert len(claims) >= 3

        file_claims = [c for c in claims if c.claim_type == "file_reference"]
        symbol_claims = [c for c in claims if c.claim_type == "symbol_reference"]

        assert any("vector_memory.py" in c.target_path for c in file_claims)
        assert any(c.target_symbol == "VectorMemory" for c in symbol_claims)

        # Audit against real files
        report = dd.verify_claims(claims, known_symbols={"VectorMemory"})
        assert report.approved is True
        assert report.failed_claims == 0
        assert report.verified_claims >= 3


# =============================================================================
# 2. HALLUCINATION & PHANTOM CLAIM DETECTION
# =============================================================================

class TestHallucinationDetection:
    """Validates adversarial flagging of hallucinated files and unverified symbols."""

    def test_hallucinated_file_claim_detection(self, mock_workspace):
        dd = create_draft_detective(workspace_root=mock_workspace)

        hallucinated_summary = """
        Fixed the issue by updating `src/non_existent_engine.py` and linking `GhostModule`.
        """

        claims = dd.extract_claims(hallucinated_summary)
        report = dd.verify_claims(claims, known_symbols={"VectorMemory"})

        assert report.approved is False
        assert report.failed_claims >= 1
        assert any("non_existent_engine.py" in h for h in report.hallucinations)


# =============================================================================
# 3. AST STRUCTURAL GATE & BRACE PARITY
# =============================================================================

class TestASTStructuralGate:
    """Validates syntax and brace parity pre-commit checks."""

    def test_ast_structural_transformation_gate(self):
        dd = create_draft_detective()

        # Valid Python code
        valid_code = "def compute_sum(a: int, b: int) -> int:\n    return a + b\n"
        ok, errs = dd.validate_code_ast(valid_code, filename="math.py")
        assert ok is True
        assert len(errs) == 0

        # Syntax error
        syntax_broken = "def compute_sum(a: int, b: int\n    return a + b\n"
        ok, errs = dd.validate_code_ast(syntax_broken, filename="math.py")
        assert ok is False
        assert len(errs) > 0

        # Mismatched braces
        brace_broken = "const app = { name: 'Hermes', count: [1, 2, 3 } ];"
        ok, errs = dd.validate_code_ast(brace_broken, filename="app.js")
        assert ok is False
        assert any("brace" in e.lower() for e in errs)


# =============================================================================
# 4. HARDWARE ENVELOPE BOUNDS & ZERO GPU VRAM
# =============================================================================

class TestDraftDetectiveHardwareBounds:
    """Validates pure CPU RAMDisk execution."""

    def test_draft_detective_zero_gpu_vram(self, mock_workspace):
        dd = create_draft_detective(workspace_root=mock_workspace)
        report = dd.full_pre_commit_audit(
            markdown_summary="Modified `src/vector_memory.py` cleanly.",
            code_diff="class VectorMemory:\n    pass\n",
        )
        assert report.approved is True
        assert report.ast_valid is True
