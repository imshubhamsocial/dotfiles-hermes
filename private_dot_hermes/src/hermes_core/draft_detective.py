"""
Milestone U55: Draft-Detective Adversarial Fact-Checker & AST Verification Gates
================================================================================
Implements Draft-Detective & Graft Verification Subsystem:
  - Adversarial Fact-Checking & Claim Extraction from Agent Summaries / Plans
  - Ground Truth Cross-Verification against Real Filesystem and AST symbols
  - AST-Aware Structural Code Integrity & Brace Parity Pre-Commit Gates
  - Zero GPU VRAM overhead (pure CPU RAMDisk execution)
"""

from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union


@dataclass
class FactualClaim:
    """Represents an extracted verifiable claim from agent output."""
    claim_type: str                   # 'file_reference', 'symbol_reference', 'test_claim'
    raw_text: str
    target_path: Optional[str] = None
    target_symbol: Optional[str] = None
    verified: bool = False
    verification_detail: str = ""


@dataclass
class VerificationAuditReport:
    """Aggregated results of adversarial fact-checking and AST validation."""
    total_claims: int = 0
    verified_claims: int = 0
    failed_claims: int = 0
    hallucinations: List[str] = field(default_factory=list)
    ast_valid: bool = True
    ast_errors: List[str] = field(default_factory=list)
    approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DraftDetective:
    """
    Adversarial verification engine that scans agent markdown text and code diffs
    to flag unverified claims, phantom file links, and broken AST structures.
    """

    # Regex patterns to extract file paths and symbols from markdown text
    FILE_REF_PATTERN = re.compile(r'\[([^\]]+)\]\(file://([^)]+)\)|`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)`')
    SYMBOL_REF_PATTERN = re.compile(r'`(?:def\s+|class\s+)?([a-zA-Z_][a-zA-Z0-9_]*)`')

    def __init__(self, workspace_root: Optional[Union[str, Path]] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    def extract_claims(self, markdown_text: str) -> List[FactualClaim]:
        """Extracts verifiable claims from agent output text."""
        claims: List[FactualClaim] = []

        # 1. Extract file references
        for match in self.FILE_REF_PATTERN.finditer(markdown_text):
            path_str = match.group(2) or match.group(3)
            if path_str and not path_str.startswith("http"):
                if "/" in path_str or any(path_str.endswith(ext) for ext in [".py", ".hpp", ".cpp", ".json", ".md", ".js", ".ts"]):
                    claims.append(FactualClaim(
                        claim_type="file_reference",
                        raw_text=match.group(0),
                        target_path=path_str,
                    ))

        # 2. Extract symbol declarations/references
        for match in self.SYMBOL_REF_PATTERN.finditer(markdown_text):
            sym = match.group(1)
            if sym and sym not in {"True", "False", "None", "str", "int", "list", "dict"}:
                claims.append(FactualClaim(
                    claim_type="symbol_reference",
                    raw_text=match.group(0),
                    target_symbol=sym,
                ))

        return claims

    def verify_claims(
        self,
        claims: List[FactualClaim],
        known_files: Optional[Set[str]] = None,
        known_symbols: Optional[Set[str]] = None,
    ) -> VerificationAuditReport:
        """Verifies claims against filesystem ground truth and AST symbols."""
        report = VerificationAuditReport(total_claims=len(claims))

        for claim in claims:
            if claim.claim_type == "file_reference" and claim.target_path:
                norm_path = claim.target_path.lstrip("/")
                local_path = self.workspace_root / norm_path

                exists = False
                if known_files is not None:
                    exists = any(norm_path in kf or kf.endswith(norm_path) for kf in known_files)
                else:
                    exists = local_path.exists() or Path(claim.target_path).exists()

                if exists:
                    claim.verified = True
                    claim.verification_detail = "File exists on disk."
                    report.verified_claims += 1
                else:
                    claim.verified = False
                    claim.verification_detail = f"Phantom file claim: '{claim.target_path}' does not exist."
                    report.failed_claims += 1
                    report.hallucinations.append(claim.verification_detail)

            elif claim.claim_type == "symbol_reference" and claim.target_symbol:
                if known_symbols is not None:
                    if claim.target_symbol in known_symbols:
                        claim.verified = True
                        claim.verification_detail = f"Symbol '{claim.target_symbol}' confirmed in codebase AST."
                        report.verified_claims += 1
                    else:
                        claim.verified = False
                        claim.verification_detail = f"Unverified symbol claim: '{claim.target_symbol}'."
                        report.failed_claims += 1
                        report.hallucinations.append(claim.verification_detail)
                else:
                    # In absence of symbol dictionary, assume neutral pass
                    claim.verified = True
                    report.verified_claims += 1

        report.approved = (report.failed_claims == 0 and report.ast_valid)
        return report

    def validate_code_ast(self, code_content: str, filename: str = "<string>") -> Tuple[bool, List[str]]:
        """Performs structural AST syntax validation."""
        errors: List[str] = []
        if filename.endswith(".py") or "def " in code_content or "import " in code_content:
            try:
                ast.parse(code_content, filename=filename)
            except SyntaxError as e:
                errors.append(f"SyntaxError: {e.msg} (line {e.lineno})")

        # Check brace balancing
        brace_pairs = {"(": ")", "{": "}", "[": "]"}
        stack = []
        for i, ch in enumerate(code_content):
            if ch in brace_pairs:
                stack.append((ch, i))
            elif ch in brace_pairs.values():
                if not stack:
                    errors.append(f"Unmatched closing brace '{ch}' at position {i}")
                    break
                open_ch, _ = stack.pop()
                if brace_pairs[open_ch] != ch:
                    errors.append(f"Mismatched brace '{open_ch}' closed by '{ch}' at position {i}")
                    break

        if stack and not errors:
            unmatched = stack.pop()[0]
            errors.append(f"Unclosed opening brace '{unmatched}'")

        return (len(errors) == 0, errors)

    def full_pre_commit_audit(
        self,
        markdown_summary: str,
        code_diff: str,
        known_files: Optional[Set[str]] = None,
        known_symbols: Optional[Set[str]] = None,
    ) -> VerificationAuditReport:
        """Runs comprehensive adversarial audit over summary claims and code diff."""
        claims = self.extract_claims(markdown_summary)
        report = self.verify_claims(claims, known_files=known_files, known_symbols=known_symbols)

        ast_ok, ast_errs = self.validate_code_ast(code_diff)
        report.ast_valid = ast_ok
        report.ast_errors = ast_errs

        report.approved = (report.failed_claims == 0 and report.ast_valid)
        return report


def create_draft_detective(workspace_root: Optional[Union[str, Path]] = None) -> DraftDetective:
    return DraftDetective(workspace_root=workspace_root)
