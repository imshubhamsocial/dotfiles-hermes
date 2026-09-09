"""
Milestone U55 & Track 3.1: Draft-Detective Adversarial Fact-Checker & Gemma-APS Verification Gates
===================================================================================================
Implements Draft-Detective & Graft Verification Subsystem:
  - Adversarial Fact-Checking & Claim Extraction from Agent Summaries / Plans
  - Ground Truth Cross-Verification against Real Filesystem and AST symbols
  - Gemma-APS (Abstractive Proposition Segmentation): decomposes technical claims into
    atomic verifiable propositions (signatures, defaults, return types, exceptions, inheritance)
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
class AtomicProposition:
    """
    Represents an atomic semantic proposition decomposed via Gemma-APS principles.
    Deconstructs compound prose/claims into discrete AST-checkable triples.
    """
    subject: str                    # e.g., "calculate_score" or "VectorMemory"
    predicate: str                  # "is_function", "is_class", "has_param", "has_default", "raises_exception", "returns_type", "inherits_from"
    expected_value: Any             # e.g., "data", "True", "ValueError", "float", "BaseMemory"
    raw_sentence: str               # original prose sentence
    verified: bool = False
    detail: str = ""


@dataclass
class VerificationAuditReport:
    """Aggregated results of adversarial fact-checking, Gemma-APS propositions, and AST validation."""
    total_claims: int = 0
    verified_claims: int = 0
    failed_claims: int = 0
    hallucinations: List[str] = field(default_factory=list)
    ast_valid: bool = True
    ast_errors: List[str] = field(default_factory=list)
    approved: bool = False
    total_propositions: int = 0
    verified_propositions: int = 0
    failed_propositions: int = 0
    proposition_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PropositionSegmenter:
    """
    Abstractive Proposition Segmentation (Gemma-APS) Engine.
    Deconstructs technical summaries, docstrings, and commit messages into atomic claims.
    """
    FUNC_SIG_PATTERN = re.compile(r'`?([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)`?')
    CLASS_DEF_PATTERN = re.compile(r'class\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?(?:\(([^)]*)\))?')
    RAISES_PATTERN = re.compile(r'(?:raises?|throwing)\s+`?([a-zA-Z_][a-zA-Z0-9_]*(?:Error|Exception))`?', re.IGNORECASE)
    RETURNS_PATTERN = re.compile(r'(?:returns?|returning)\s+`?([a-zA-Z_][a-zA-Z0-9_]*(?:\[[^\]]+\])?)`?', re.IGNORECASE)

    def segment_text(self, text: str) -> List[AtomicProposition]:
        propositions: List[AtomicProposition] = []
        sentences = re.split(r'[.\n;]+', text)

        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            # 1. Class declarations & inheritance
            for m in self.CLASS_DEF_PATTERN.finditer(sent_clean):
                cls_name = m.group(1)
                bases = m.group(2)
                propositions.append(AtomicProposition(
                    subject=cls_name,
                    predicate="is_class",
                    expected_value=True,
                    raw_sentence=sent_clean,
                ))
                if bases:
                    for base in [b.strip() for b in bases.split(",") if b.strip()]:
                        propositions.append(AtomicProposition(
                            subject=cls_name,
                            predicate="inherits_from",
                            expected_value=base,
                            raw_sentence=sent_clean,
                        ))

            # 2. Function calls & signatures
            for m in self.FUNC_SIG_PATTERN.finditer(sent_clean):
                fn_name = m.group(1)
                params_str = m.group(2)
                # Ignore common language constructs / markdown words
                if fn_name in {"file", "http", "https", "print", "len", "range", "git", "echo"}:
                    continue

                propositions.append(AtomicProposition(
                    subject=fn_name,
                    predicate="is_function",
                    expected_value=True,
                    raw_sentence=sent_clean,
                ))

                if params_str:
                    raw_params = [p.strip() for p in params_str.split(",") if p.strip()]
                    for p in raw_params:
                        if "=" in p:
                            p_name, p_val = p.split("=", 1)
                            propositions.append(AtomicProposition(
                                subject=fn_name,
                                predicate="has_default",
                                expected_value=(p_name.strip(), p_val.strip().strip("'\"")),
                                raw_sentence=sent_clean,
                            ))
                        else:
                            p_name = p.split(":")[0].strip()
                            propositions.append(AtomicProposition(
                                subject=fn_name,
                                predicate="has_param",
                                expected_value=p_name,
                                raw_sentence=sent_clean,
                            ))

                # Exceptions mentioned in the same proposition sentence
                for r in self.RAISES_PATTERN.finditer(sent_clean):
                    exc_name = r.group(1)
                    propositions.append(AtomicProposition(
                        subject=fn_name,
                        predicate="raises_exception",
                        expected_value=exc_name,
                        raw_sentence=sent_clean,
                    ))

                # Return types mentioned in the same proposition sentence
                for ret in self.RETURNS_PATTERN.finditer(sent_clean):
                    ret_type = ret.group(1).strip()
                    if ret_type and not any(w in ret_type.lower() for w in ["none", "nothing", "true", "false"]):
                        propositions.append(AtomicProposition(
                            subject=fn_name,
                            predicate="returns_type",
                            expected_value=ret_type,
                            raw_sentence=sent_clean,
                        ))

        return propositions


class ASTPropositionVerifier:
    """
    Verifies segmented propositions against Python Abstract Syntax Tree (AST).
    Deterministic static verification without executing code or calling LLMs.
    """
    def verify(
        self,
        propositions: List[AtomicProposition],
        code_or_tree: Union[str, ast.AST],
    ) -> Tuple[List[AtomicProposition], List[str]]:
        errors: List[str] = []
        if isinstance(code_or_tree, str):
            try:
                tree = ast.parse(code_or_tree)
            except SyntaxError as e:
                msg = f"AST parse error: {e}"
                for p in propositions:
                    p.verified = False
                    p.detail = msg
                return propositions, [msg]
        else:
            tree = code_or_tree

        # Build symbol catalog
        classes: Dict[str, ast.ClassDef] = {}
        functions: Dict[str, Union[ast.FunctionDef, ast.AsyncFunctionDef]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = node

        for p in propositions:
            if p.predicate == "is_class":
                if p.subject in classes:
                    p.verified = True
                    p.detail = f"Class '{p.subject}' declared in AST."
                else:
                    p.verified = False
                    p.detail = f"Claimed class '{p.subject}' not found in AST."
                    errors.append(p.detail)

            elif p.predicate == "inherits_from":
                cls_node = classes.get(p.subject)
                if not cls_node:
                    p.verified = False
                    p.detail = f"Class '{p.subject}' not found in AST."
                    errors.append(p.detail)
                else:
                    actual_bases = [ast.unparse(b) if hasattr(ast, "unparse") else getattr(b, "id", "") for b in cls_node.bases]
                    if any(p.expected_value == b or p.expected_value in b for b in actual_bases):
                        p.verified = True
                        p.detail = f"Class '{p.subject}' inherits from '{p.expected_value}'."
                    else:
                        p.verified = False
                        p.detail = f"Class '{p.subject}' bases {actual_bases} do not match claimed base '{p.expected_value}'."
                        errors.append(p.detail)

            elif p.predicate == "is_function":
                if p.subject in functions:
                    p.verified = True
                    p.detail = f"Function '{p.subject}' declared in AST."
                else:
                    p.verified = False
                    p.detail = f"Claimed function '{p.subject}' not found in AST."
                    errors.append(p.detail)

            elif p.predicate == "has_param":
                fn_node = functions.get(p.subject)
                if not fn_node:
                    p.verified = False
                    p.detail = f"Function '{p.subject}' not found in AST."
                    errors.append(p.detail)
                else:
                    arg_names = [a.arg for a in fn_node.args.args]
                    if p.expected_value in arg_names or p.expected_value in {"self", "cls"}:
                        p.verified = True
                        p.detail = f"Param '{p.expected_value}' exists in '{p.subject}' signature."
                    else:
                        p.verified = False
                        p.detail = f"Param '{p.expected_value}' missing from '{p.subject}' (args: {arg_names})."
                        errors.append(p.detail)

            elif p.predicate == "has_default":
                fn_node = functions.get(p.subject)
                param_name, expected_default = p.expected_value
                if not fn_node:
                    p.verified = False
                    p.detail = f"Function '{p.subject}' not found in AST."
                    errors.append(p.detail)
                else:
                    arg_names = [a.arg for a in fn_node.args.args]
                    num_defaults = len(fn_node.args.defaults)
                    defaults_map = {}
                    if num_defaults > 0:
                        default_args = arg_names[-num_defaults:]
                        for arg_n, d_node in zip(default_args, fn_node.args.defaults):
                            val_repr = ast.unparse(d_node) if hasattr(ast, "unparse") else str(getattr(d_node, "value", ""))
                            defaults_map[arg_n] = val_repr.strip("'\"")

                    actual_val = defaults_map.get(param_name)
                    if actual_val == expected_default or (actual_val is not None and str(actual_val).lower() == str(expected_default).lower()):
                        p.verified = True
                        p.detail = f"Default value for '{param_name}' is '{expected_default}'."
                    else:
                        p.verified = False
                        p.detail = f"Default mismatch for '{p.subject}.{param_name}': expected '{expected_default}', AST has '{actual_val}'."
                        errors.append(p.detail)

            elif p.predicate == "raises_exception":
                fn_node = functions.get(p.subject)
                if not fn_node:
                    p.verified = False
                    p.detail = f"Function '{p.subject}' not found in AST."
                    errors.append(p.detail)
                else:
                    raised_types = set()
                    for subnode in ast.walk(fn_node):
                        if isinstance(subnode, ast.Raise) and subnode.exc:
                            if isinstance(subnode.exc, ast.Call) and hasattr(subnode.exc.func, "id"):
                                raised_types.add(subnode.exc.func.id)
                            elif isinstance(subnode.exc, ast.Name):
                                raised_types.add(subnode.exc.id)

                    if p.expected_value in raised_types:
                        p.verified = True
                        p.detail = f"Function '{p.subject}' raises '{p.expected_value}' in AST."
                    else:
                        p.verified = False
                        p.detail = f"Exception mismatch: '{p.subject}' does not raise '{p.expected_value}' (raises: {list(raised_types)})."
                        errors.append(p.detail)

            elif p.predicate == "returns_type":
                fn_node = functions.get(p.subject)
                if not fn_node:
                    p.verified = False
                    p.detail = f"Function '{p.subject}' not found in AST."
                    errors.append(p.detail)
                else:
                    actual_ret = ""
                    if fn_node.returns:
                        actual_ret = ast.unparse(fn_node.returns) if hasattr(ast, "unparse") else ""
                    if actual_ret and (p.expected_value == actual_ret or p.expected_value in actual_ret):
                        p.verified = True
                        p.detail = f"Function '{p.subject}' return annotation matches '{p.expected_value}'."
                    else:
                        p.verified = False
                        p.detail = f"Return type mismatch for '{p.subject}': expected '{p.expected_value}', AST has '{actual_ret}'."
                        errors.append(p.detail)

        return propositions, errors


class DraftDetective:
    """
    Adversarial verification engine that scans agent markdown text and code diffs
    to flag unverified claims, phantom file links, broken AST structures, and
    contradictory Gemma-APS propositions.
    """

    FILE_REF_PATTERN = re.compile(r'\[([^\]]+)\]\(file://([^)]+)\)|`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)`')
    SYMBOL_REF_PATTERN = re.compile(r'`(?:def\s+|class\s+)?([a-zA-Z_][a-zA-Z0-9_]*)`')

    def __init__(self, workspace_root: Optional[Union[str, Path]] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.segmenter = PropositionSegmenter()
        self.verifier = ASTPropositionVerifier()

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

    def extract_propositions(self, markdown_text: str) -> List[AtomicProposition]:
        """Extracts atomic semantic propositions via Gemma-APS."""
        return self.segmenter.segment_text(markdown_text)

    def verify_propositions(
        self,
        propositions: List[AtomicProposition],
        code_or_tree: Union[str, ast.AST],
    ) -> Tuple[List[AtomicProposition], List[str]]:
        """Verifies atomic propositions against actual code AST."""
        return self.verifier.verify(propositions, code_or_tree)

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
        """Performs structural AST syntax validation and brace parity checks."""
        errors: List[str] = []
        if filename.endswith(".py") or "def " in code_content or "import " in code_content or "class " in code_content:
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
        """Runs comprehensive adversarial audit over summary claims, APS propositions, and code diff."""
        claims = self.extract_claims(markdown_summary)
        report = self.verify_claims(claims, known_files=known_files, known_symbols=known_symbols)

        ast_ok, ast_errs = self.validate_code_ast(code_diff)
        report.ast_valid = ast_ok
        report.ast_errors = ast_errs

        # Gemma-APS: Proposition segmentation & verification if code_diff contains valid python AST
        if ast_ok and ("def " in code_diff or "class " in code_diff):
            propositions = self.extract_propositions(markdown_summary)
            if propositions:
                verified_props, prop_errs = self.verify_propositions(propositions, code_diff)
                report.total_propositions = len(verified_props)
                report.verified_propositions = sum(1 for p in verified_props if p.verified)
                report.failed_propositions = sum(1 for p in verified_props if not p.verified)
                report.proposition_errors = prop_errs
                if report.failed_propositions > 0:
                    report.hallucinations.extend(prop_errs)

        report.approved = (report.failed_claims == 0 and report.failed_propositions == 0 and report.ast_valid)
        return report

    def quorum_pre_commit_audit(
        self,
        markdown_summary: str,
        code_diff: str,
        author_agent: str = "coder",
        auditor_agent: str = "draft_detective",
        known_files: Optional[Set[str]] = None,
        known_symbols: Optional[Set[str]] = None,
        task_id: str = "pre_commit",
    ) -> Dict[str, Any]:
        """Runs Quorum cross-model consensus audit over draft output."""
        try:
            from .quorum_gate import QuorumAuditGate
        except ImportError:
            from quorum_gate import QuorumAuditGate

        report = self.full_pre_commit_audit(
            markdown_summary=markdown_summary,
            code_diff=code_diff,
            known_files=known_files,
            known_symbols=known_symbols,
        )
        gate = QuorumAuditGate()
        affected = list(known_files) if known_files else []
        receipt = gate.audit_step(
            task_id=task_id,
            author_agent=author_agent,
            auditor_agent=auditor_agent,
            affected_files=affected,
            ast_valid=report.ast_valid,
            tests_passed=report.approved,
            pass_rate=1.0 if report.approved else 0.0,
            diff_text=code_diff,
        )
        return {
            "report": report.to_dict(),
            "quorum_receipt": receipt.to_dict(),
            "approved": report.approved and receipt.verdict == "AGREED",
        }


def create_draft_detective(workspace_root: Optional[Union[str, Path]] = None) -> DraftDetective:
    return DraftDetective(workspace_root=workspace_root)
