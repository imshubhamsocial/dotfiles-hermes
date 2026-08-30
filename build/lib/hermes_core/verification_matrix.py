"""
Milestone U58: Closed-Loop Dual-Agent Verification Matrix
=========================================================
Implements Multi-Tier Pre-Flight Verification Matrix:
  - AST Syntax & Brace Verification (DraftDetective)
  - Adversarial Claim Grounding & Phantom Link Prevention
  - COG Dual-Agent Worker/Verifier Consensus Gate
  - 2-Strike Tabu Rollback Trigger
  - Zero GPU VRAM overhead (pure CPU RAMDisk execution)
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

from hermes_core.draft_detective import DraftDetective, VerificationAuditReport, create_draft_detective


@dataclass
class MatrixAuditVerdict:
    """Final aggregated verdict across all verification gates."""
    approved: bool
    ast_gate_passed: bool
    claims_gate_passed: bool
    verifier_consensus_passed: bool
    consecutive_failures: int
    tabu_rollback_triggered: bool
    diagnostics: List[str] = field(default_factory=list)
    audit_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VerificationMatrix:
    """
    Dual-Agent Closed-Loop Pre-Flight Verification Subsystem.
    Combines AST validation, fact checking, and tabu branch pruning.
    """

    MAX_CONSECUTIVE_FAILURES: int = 2

    def __init__(self, workspace_root: Optional[Union[str, Path]] = None, draft_detective: Optional[DraftDetective] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.detective = draft_detective or create_draft_detective(workspace_root=self.workspace_root)
        self.failure_counts: Dict[str, int] = {}

    def audit_patch(
        self,
        file_path: str,
        code_content: str,
        markdown_summary: str,
        known_files: Optional[Set[str]] = None,
        known_symbols: Optional[Set[str]] = None,
        verifier_approved: bool = True,
    ) -> MatrixAuditVerdict:
        """Runs multi-tier pre-commit audit over candidate file mutation."""
        t0 = time.perf_counter()
        diagnostics: List[str] = []

        # 1. AST Structural Syntax & Brace Balance Gate
        ast_ok, ast_errors = self.detective.validate_code_ast(code_content, filename=file_path)
        if not ast_ok:
            diagnostics.extend(ast_errors)

        # 2. Adversarial Claim Verification Gate
        claims = self.detective.extract_claims(markdown_summary)
        claims_report = self.detective.verify_claims(claims, known_files=known_files, known_symbols=known_symbols)
        claims_ok = claims_report.approved
        if not claims_ok:
            diagnostics.extend(claims_report.hallucinations)

        # 3. Dual-Agent Consensus Gate
        verifier_ok = verifier_approved
        if not verifier_ok:
            diagnostics.append("Dual-agent verifier consensus rejected candidate patch.")

        overall_pass = ast_ok and claims_ok and verifier_ok

        # Track failure count and Tabu trigger
        key = file_path
        if overall_pass:
            self.failure_counts[key] = 0
            tabu_triggered = False
        else:
            self.failure_counts[key] = self.failure_counts.get(key, 0) + 1
            tabu_triggered = (self.failure_counts[key] >= self.MAX_CONSECUTIVE_FAILURES)
            if tabu_triggered:
                diagnostics.append(f"2-Strike Tabu Rule Triggered: {self.failure_counts[key]} consecutive failures on {file_path}. Reverting to parent commit.")

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return MatrixAuditVerdict(
            approved=overall_pass,
            ast_gate_passed=ast_ok,
            claims_gate_passed=claims_ok,
            verifier_consensus_passed=verifier_ok,
            consecutive_failures=self.failure_counts.get(key, 0),
            tabu_rollback_triggered=tabu_triggered,
            diagnostics=diagnostics,
            audit_duration_ms=round(elapsed_ms, 3),
        )

    def reset_failures(self, file_path: Optional[str] = None):
        if file_path:
            self.failure_counts[file_path] = 0
        else:
            self.failure_counts.clear()


def create_verification_matrix(workspace_root: Optional[Union[str, Path]] = None) -> VerificationMatrix:
    return VerificationMatrix(workspace_root=workspace_root)
