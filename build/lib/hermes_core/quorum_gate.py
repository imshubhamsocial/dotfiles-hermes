"""
Quorum Cross-Model Consensus & Audit Gate (berrzebb/quorum integration)
========================================================================
Implements the Quorum protocol for multi-agent software engineering:
  edit -> audit -> agree -> retro -> commit

Key Principles:
1. Structural Separation: No model/agent can approve its own code (author != auditor).
2. Blast Radius Calculation: Measures files, symbols, and AST tree depth touched.
3. Multi-Dimensional Fitness Gate: Combines AST syntax health, static verification,
   and test execution match rate into an objective score [0.0 - 1.0].
4. Structured Audit Receipts: Machine-verifiable JSON/Markdown receipts.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Set, Tuple


@dataclass
class BlastRadius:
    """Measures the blast radius of a code modification."""
    files_changed: List[str] = field(default_factory=list)
    symbols_affected: List[str] = field(default_factory=list)
    ast_depth_max: int = 0
    total_lines_changed: int = 0
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"

    def compute_risk(self) -> str:
        if len(self.files_changed) > 5 or self.total_lines_changed > 300 or len(self.symbols_affected) > 10:
            self.risk_level = "CRITICAL"
        elif len(self.files_changed) > 2 or self.total_lines_changed > 100:
            self.risk_level = "HIGH"
        elif len(self.files_changed) > 1 or self.total_lines_changed > 30:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"
        return self.risk_level


@dataclass
class QuorumAuditReceipt:
    """Structured receipt representing an independent audit verdict."""
    session_id: str
    task_id: str
    author: str
    auditor: str
    verdict: Literal["AGREED", "REJECTED", "ESCALATED"]
    fitness_score: float  # 0.0 to 1.0
    blast_radius: BlastRadius
    checks: Dict[str, bool] = field(default_factory=dict)
    rejection_reasons: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def __post_init__(self):
        if not self.signature:
            raw = f"{self.session_id}:{self.task_id}:{self.author}:{self.auditor}:{self.verdict}:{self.fitness_score}:{self.timestamp}"
            self.signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["blast_radius"] = asdict(self.blast_radius)
        return d


class QuorumAuditGate:
    """
    Cross-model consensus gate that enforces independent audit before commit.
    """

    def __init__(
        self,
        min_fitness_score: float = 0.85,
        enforce_distinct_auditor: bool = True,
    ):
        self.min_fitness_score = min_fitness_score
        self.enforce_distinct_auditor = enforce_distinct_auditor
        self.audit_history: List[QuorumAuditReceipt] = []

    def calculate_blast_radius(
        self,
        file_paths: Sequence[Union[str, Path]],
        diff_text: str = "",
    ) -> BlastRadius:
        """Calculate blast radius from affected files and AST structure."""
        radius = BlastRadius()
        total_lines = 0
        symbols: Set[str] = set()
        max_depth = 0

        for fp in file_paths:
            p = Path(fp)
            radius.files_changed.append(str(p))
            if p.exists() and p.suffix == ".py":
                try:
                    tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            symbols.add(node.name)
                    # Depth estimation
                    def get_depth(n, curr=1):
                        return max([get_depth(c, curr + 1) for c in ast.iter_child_nodes(n)], default=curr)
                    max_depth = max(max_depth, get_depth(tree))
                except Exception:
                    pass

        if diff_text:
            for line in diff_text.splitlines():
                if line.startswith("+") or line.startswith("-"):
                    total_lines += 1

        radius.symbols_affected = sorted(list(symbols))
        radius.ast_depth_max = max_depth
        radius.total_lines_changed = total_lines or (len(radius.files_changed) * 20)
        radius.compute_risk()
        return radius

    def audit_step(
        self,
        task_id: str,
        author_agent: str,
        auditor_agent: str,
        affected_files: Sequence[Union[str, Path]],
        ast_valid: bool = True,
        tests_passed: bool = True,
        pass_rate: float = 1.0,
        diff_text: str = "",
        session_id: str = "default",
    ) -> QuorumAuditReceipt:
        """
        Execute Quorum audit step:
        edit -> audit -> agree -> retro -> commit
        """
        rejections: List[str] = []

        # Rule 1: Structural separation
        if self.enforce_distinct_auditor and author_agent == auditor_agent:
            rejections.append(f"Quorum Violation: Author '{author_agent}' cannot audit its own code.")

        # Rule 2: AST validity
        if not ast_valid:
            rejections.append("AST Syntax Failure: Tree contains syntax/grammar errors.")

        # Rule 3: Test execution
        if not tests_passed or pass_rate < 1.0:
            rejections.append(f"Test Regression: pass rate {pass_rate:.1%} < 100%.")

        blast = self.calculate_blast_radius(affected_files, diff_text)
        if blast.risk_level == "CRITICAL" and not tests_passed:
            rejections.append("Critical Blast Radius: High impact change without passing test coverage.")

        # Compute multi-dimensional fitness score
        ast_score = 1.0 if ast_valid else 0.0
        test_score = pass_rate
        risk_penalty = 0.15 if blast.risk_level in ("HIGH", "CRITICAL") else 0.0
        fitness = max(0.0, (0.4 * ast_score + 0.6 * test_score) - risk_penalty)

        verdict: Literal["AGREED", "REJECTED", "ESCALATED"]
        if not rejections and fitness >= self.min_fitness_score:
            verdict = "AGREED"
        elif blast.risk_level == "CRITICAL" and fitness < self.min_fitness_score:
            verdict = "ESCALATED"
        else:
            verdict = "REJECTED"

        receipt = QuorumAuditReceipt(
            session_id=session_id,
            task_id=task_id,
            author=author_agent,
            auditor=auditor_agent,
            verdict=verdict,
            fitness_score=round(fitness, 3),
            blast_radius=blast,
            checks={
                "ast_valid": ast_valid,
                "tests_passed": tests_passed,
                "structural_separation": author_agent != auditor_agent,
                "fitness_gate": fitness >= self.min_fitness_score,
            },
            rejection_reasons=rejections,
        )
        self.audit_history.append(receipt)
        return receipt
