"""
Hermes Native Contract Gate (Phase 3 of Closed-Loop Runtime)
============================================================
Combines:
  1. ProcessVerifier (System-1 Fast Heuristics + System-2 Deep Invariants)
  2. SymPy Symbolic Verifier (Algebraic Equivalence, Invariant Conservation, Non-Drift Derivations)
  3. AST Structural & Simplicity Verifier (Python Syntax, YAGNI Ponytail Anti-Bloat, Security Boundaries)
Delivers unified, deterministic verdicts (ContractGateVerdict) and diagnostic traces for self-repair.
"""

from __future__ import annotations

import ast
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Set, Tuple, Union

import sympy

# Integration with Phase 1 Ponytail Ladder and ProcessVerifier
try:
    from .ponytail_ladder import BloatSeverity, PonytailDiffPruner, audit_code_simplicity
    from .process_verifier import ProcessVerifier, ProcessVerificationReport, get_process_verifier
    from .mrp_planner import TaskNode
except ImportError:
    from ponytail_ladder import BloatSeverity, PonytailDiffPruner, audit_code_simplicity
    from process_verifier import ProcessVerifier, ProcessVerificationReport, get_process_verifier
    from mrp_planner import TaskNode

logger = logging.getLogger("hermes.core.contract_gate")


class ContractCategory(str, Enum):
    AST_SYNTAX = "AST_SYNTAX"
    SIMPLICITY_YAGNI = "SIMPLICITY_YAGNI"
    SYMBOLIC_MATH = "SYMBOLIC_MATH"
    REASONING_CONSISTENCY = "REASONING_CONSISTENCY"
    RUNTIME_CONTRACT = "RUNTIME_CONTRACT"
    SECURITY_INVARIANT = "SECURITY_INVARIANT"


@dataclass
class ContractViolation:
    category: ContractCategory
    rule: str
    message: str
    severity: Literal["CRITICAL", "WARNING"] = "CRITICAL"
    remediation_hint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
            "remediation_hint": self.remediation_hint,
        }


@dataclass
class ContractGateVerdict:
    passed: bool
    confidence: float
    verdict_id: str
    violations: List[ContractViolation] = field(default_factory=list)
    remediation_hints: List[str] = field(default_factory=list)
    ast_score: float = 1.0
    symbolic_verified: bool = False
    process_mode: str = "system_1"
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "confidence": round(self.confidence, 3),
            "verdict_id": self.verdict_id,
            "violations": [v.to_dict() for v in self.violations],
            "remediation_hints": self.remediation_hints,
            "ast_score": round(self.ast_score, 3),
            "symbolic_verified": self.symbolic_verified,
            "process_mode": self.process_mode,
            "duration_ms": round(self.duration_ms, 2),
            "details": self.details,
        }

    def to_diagnostic_trace(self) -> str:
        """Render a structured diagnostic trace for self-repair and rollback."""
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"[ContractGate:{self.verdict_id}] Status: {status} (Confidence: {self.confidence:.2f}, AST Score: {self.ast_score:.2f})",
            f"Execution Duration: {self.duration_ms:.1f}ms | Mode: {self.process_mode}",
        ]
        if self.violations:
            lines.append("Violations Detected:")
            for v in self.violations:
                lines.append(f"  - [{v.severity}] {v.category.value}::{v.rule}: {v.message}")
                if v.remediation_hint:
                    lines.append(f"    Remediation: {v.remediation_hint}")
        if self.remediation_hints:
            lines.append("Remediation Plan:")
            for h in self.remediation_hints:
                lines.append(f"  * {h}")
        return "\n".join(lines)


# =============================================================================
# 1. SymPy Symbolic Invariant Verifier
# =============================================================================

class SymPyContractVerifier:
    """
    Mathematical and symbolic engine verifying equations, identities, and derivations.
    Prevents algebraic drift and hallucinated symbolic calculations.
    """

    @classmethod
    def verify_equation(cls, lhs_str: str, rhs_str: str) -> Tuple[bool, str]:
        """
        Verify algebraic equivalence: simplify(lhs - rhs) == 0.
        Supports powers, fractions, trigonometric, and polynomial expressions.
        """
        try:
            # Parse symbolic expressions with SymPy
            lhs = sympy.sympify(lhs_str, evaluate=False)
            rhs = sympy.sympify(rhs_str, evaluate=False)
            diff = sympy.simplify(lhs - rhs)
            if diff == 0:
                return True, f"Identity holds: {lhs_str} == {rhs_str}"
            else:
                return False, f"Algebraic discrepancy: ({lhs_str}) - ({rhs_str}) simplifies to '{diff}', expected 0"
        except Exception as e:
            return False, f"SymPy parsing or evaluation failed on '{lhs_str} == {rhs_str}': {e}"

    @classmethod
    def verify_derivation_chain(cls, steps: List[str]) -> Tuple[bool, List[str]]:
        """
        Verify that each successive step in a derivation is algebraically equivalent.
        E.g., [E_0, E_1, ..., E_k] where E_i == E_{i+1}.
        """
        anomalies = []
        if len(steps) < 2:
            return True, []

        for i in range(len(steps) - 1):
            s_curr = steps[i].strip()
            s_next = steps[i + 1].strip()
            ok, msg = cls.verify_equation(s_curr, s_next)
            if not ok:
                anomalies.append(f"Derivation step {i} -> {i+1} broken: {msg}")

        return len(anomalies) == 0, anomalies

    @classmethod
    def verify_numeric_bounds(
        cls,
        expr_str: str,
        min_bound: Optional[float] = None,
        max_bound: Optional[float] = None,
        substitutions: Optional[Dict[str, float]] = None,
    ) -> Tuple[bool, float, str]:
        """Verify that an expression evaluates within target numerical boundaries."""
        try:
            expr = sympy.sympify(expr_str)
            if substitutions:
                sym_subs = {sympy.Symbol(k): v for k, v in substitutions.items()}
                expr = expr.subs(sym_subs)
            val = float(expr.evalf())
            if min_bound is not None and val < min_bound:
                return False, val, f"Value {val} below minimum bound {min_bound}"
            if max_bound is not None and val > max_bound:
                return False, val, f"Value {val} exceeds maximum bound {max_bound}"
            return True, val, f"Value {val} within bounds [{min_bound}, {max_bound}]"
        except Exception as e:
            return False, 0.0, f"Failed to evaluate expression '{expr_str}': {e}"


# =============================================================================
# 2. AST Structural & Simplicity Verifier
# =============================================================================

class ASTContractVerifier:
    """
    Performs deterministic AST validation, anti-bloat audits, and security invariant checks.
    """

    FORBIDDEN_CALLS: Set[str] = {"eval", "exec", "__import__"}

    @classmethod
    def verify_python_syntax(cls, code_snippet: str) -> Tuple[bool, Optional[ast.AST], List[ContractViolation]]:
        """Verify strict Python AST parsing with line/col precision."""
        violations: List[ContractViolation] = []
        # Strip markdown fences if present
        clean_code = re.sub(r"^```python\s*", "", code_snippet, flags=re.MULTILINE)
        clean_code = re.sub(r"^```\s*$", "", clean_code, flags=re.MULTILINE).strip()

        if not clean_code:
            violations.append(
                ContractViolation(
                    category=ContractCategory.AST_SYNTAX,
                    rule="empty_code_payload",
                    message="Code snippet is empty.",
                    severity="CRITICAL",
                    remediation_hint="Provide non-empty implementation code.",
                )
            )
            return False, None, violations

        try:
            tree = ast.parse(clean_code)
            return True, tree, []
        except SyntaxError as e:
            violations.append(
                ContractViolation(
                    category=ContractCategory.AST_SYNTAX,
                    rule="python_syntax_error",
                    message=f"SyntaxError: {e.msg} at line {e.lineno}, col {e.offset}",
                    severity="CRITICAL",
                    remediation_hint=f"Fix syntax at line {e.lineno}: '{e.text.strip() if e.text else ''}'",
                )
            )
            return False, None, violations
        except Exception as e:
            violations.append(
                ContractViolation(
                    category=ContractCategory.AST_SYNTAX,
                    rule="ast_parse_failure",
                    message=f"AST parsing error: {e}",
                    severity="CRITICAL",
                    remediation_hint="Ensure code is valid Python syntax.",
                )
            )
            return False, None, violations

    @classmethod
    def verify_simplicity(cls, code_snippet: str, strict: bool = True) -> Tuple[bool, float, List[ContractViolation]]:
        """Audit against over-engineering using Phase 1 PonytailDiffPruner rules."""
        report = audit_code_simplicity(code_snippet, strict=strict)
        violations: List[ContractViolation] = []

        for v in report.violations:
            sev = "CRITICAL" if v.severity == BloatSeverity.CRITICAL_OVERENGINEERING else "WARNING"
            violations.append(
                ContractViolation(
                    category=ContractCategory.SIMPLICITY_YAGNI,
                    rule=v.rule,
                    message=f"Line {v.line_number} ({v.entity_name}): {v.rationale}",
                    severity=sev,
                    remediation_hint=v.simplification,
                )
            )

        passed = report.passed
        return passed, report.simplicity_score, violations

    @classmethod
    def verify_security_invariants(
        cls,
        tree: ast.AST,
        forbidden_calls: Optional[Set[str]] = None,
    ) -> List[ContractViolation]:
        """Check for unsafe constructs like unapproved eval/exec or naked except clauses."""
        violations: List[ContractViolation] = []
        banned = forbidden_calls or cls.FORBIDDEN_CALLS

        for node in ast.walk(tree):
            # Check forbidden function calls
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in banned:
                    violations.append(
                        ContractViolation(
                            category=ContractCategory.SECURITY_INVARIANT,
                            rule="forbidden_function_call",
                            message=f"Line {getattr(node, 'lineno', '?')}: Forbidden dangerous call '{func_name}' detected.",
                            severity="CRITICAL",
                            remediation_hint=f"Remove '{func_name}' and use safe standard library equivalents.",
                        )
                    )

            # Check bare except clauses without re-raise or logging
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    # Check if body is just 'pass'
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        violations.append(
                            ContractViolation(
                                category=ContractCategory.SECURITY_INVARIANT,
                                rule="naked_except_pass",
                                message=f"Line {getattr(node, 'lineno', '?')}: Naked 'except:' with 'pass' suppresses all exceptions.",
                                severity="WARNING",
                                remediation_hint="Catch specific exceptions and log or raise.",
                            )
                        )

        return violations

    @classmethod
    def verify_required_exports(cls, tree: ast.AST, required_symbols: List[str]) -> List[ContractViolation]:
        """Verify that mandatory symbols (functions, classes, or module variables) exist in AST."""
        violations: List[ContractViolation] = []
        defined_symbols: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_symbols.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_symbols.add(target.id)

        for req in required_symbols:
            if req not in defined_symbols:
                violations.append(
                    ContractViolation(
                        category=ContractCategory.AST_SYNTAX,
                        rule="missing_required_symbol",
                        message=f"Required export '{req}' is not defined in the module AST.",
                        severity="CRITICAL",
                        remediation_hint=f"Implement and export '{req}'.",
                    )
                )

        return violations


# =============================================================================
# 3. Native Contract Gate Engine
# =============================================================================

class NativeContractGate:
    """
    Phase 3 Native Contract Gate.
    Aggregates ProcessVerifier (System-1/2), SymPy (Symbolic Invariants),
    and AST Check (Syntax, Simplicity, and Safety) into a single gate.
    """

    def __init__(self, process_verifier: Optional[ProcessVerifier] = None):
        self.process_verifier = process_verifier or get_process_verifier()
        self.sympy_verifier = SymPyContractVerifier()
        self.ast_verifier = ASTContractVerifier()

    def verify_code(
        self,
        code: str,
        required_symbols: Optional[List[str]] = None,
        strict_simplicity: bool = True,
        forbidden_calls: Optional[Set[str]] = None,
    ) -> ContractGateVerdict:
        """Audit Python code against AST syntax, YAGNI simplicity, and security invariants."""
        t0 = time.time()
        verdict_id = f"cg-code-{uuid.uuid4().hex[:8]}"
        violations: List[ContractViolation] = []
        remediation_hints: List[str] = []

        # 1. AST Syntax Parsing
        syntax_ok, tree, syntax_violations = self.ast_verifier.verify_python_syntax(code)
        violations.extend(syntax_violations)

        ast_score = 1.0
        if not syntax_ok or tree is None:
            duration_ms = (time.time() - t0) * 1000.0
            remediation_hints.extend([v.remediation_hint for v in syntax_violations if v.remediation_hint])
            return ContractGateVerdict(
                passed=False,
                confidence=0.1,
                verdict_id=verdict_id,
                violations=violations,
                remediation_hints=remediation_hints,
                ast_score=0.0,
                symbolic_verified=False,
                process_mode="ast_syntax",
                duration_ms=duration_ms,
            )

        # 2. Simplicity & YAGNI Audit
        simp_ok, ast_score, simp_violations = self.ast_verifier.verify_simplicity(code, strict=strict_simplicity)
        violations.extend(simp_violations)

        # 3. Security & Safety Invariants
        sec_violations = self.ast_verifier.verify_security_invariants(tree, forbidden_calls=forbidden_calls)
        violations.extend(sec_violations)

        # 4. Required Exports Check
        if required_symbols:
            exp_violations = self.ast_verifier.verify_required_exports(tree, required_symbols)
            violations.extend(exp_violations)

        critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
        passed = critical_count == 0
        confidence = ast_score if passed else max(0.1, ast_score - (0.2 * critical_count))

        for v in violations:
            if v.remediation_hint and v.remediation_hint not in remediation_hints:
                remediation_hints.append(v.remediation_hint)

        duration_ms = (time.time() - t0) * 1000.0
        return ContractGateVerdict(
            passed=passed,
            confidence=confidence,
            verdict_id=verdict_id,
            violations=violations,
            remediation_hints=remediation_hints,
            ast_score=ast_score,
            symbolic_verified=False,
            process_mode="ast_security_simplicity",
            duration_ms=duration_ms,
            details={"critical_violations": critical_count, "warning_violations": len(violations) - critical_count},
        )

    def verify_math_reasoning(
        self,
        reasoning_text: str,
        symbolic_equations: Optional[List[Tuple[str, str]]] = None,
        derivation_steps: Optional[List[str]] = None,
        numeric_bounds: Optional[List[Tuple[str, Optional[float], Optional[float]]]] = None,
    ) -> ContractGateVerdict:
        """Audit reasoning text and symbolic mathematical claims."""
        t0 = time.time()
        verdict_id = f"cg-math-{uuid.uuid4().hex[:8]}"
        violations: List[ContractViolation] = []
        remediation_hints: List[str] = []

        # 1. ProcessVerifier System-1 & System-2 checks
        pv_report = self.process_verifier.verify_step(reasoning_text, step_type="math")
        if not pv_report.passed:
            for anom in pv_report.anomalies:
                violations.append(
                    ContractViolation(
                        category=ContractCategory.REASONING_CONSISTENCY,
                        rule="reasoning_anomaly",
                        message=anom,
                        severity="CRITICAL",
                        remediation_hint="Resolve contradictions or add explicit terminal conclusion.",
                    )
                )

        symbolic_verified = False

        # 2. SymPy Explicit Equation Equivalence Checks
        if symbolic_equations:
            all_eq_ok = True
            for lhs, rhs in symbolic_equations:
                ok, msg = self.sympy_verifier.verify_equation(lhs, rhs)
                if not ok:
                    all_eq_ok = False
                    violations.append(
                        ContractViolation(
                            category=ContractCategory.SYMBOLIC_MATH,
                            rule="algebraic_identity_violation",
                            message=msg,
                            severity="CRITICAL",
                            remediation_hint=f"Check algebraic simplification of '{lhs}' vs '{rhs}'.",
                        )
                    )
            symbolic_verified = all_eq_ok

        # 3. SymPy Derivation Chain Checks (Anti-algebraic drift)
        if derivation_steps:
            deriv_ok, deriv_anomalies = self.sympy_verifier.verify_derivation_chain(derivation_steps)
            if not deriv_ok:
                for a in deriv_anomalies:
                    violations.append(
                        ContractViolation(
                            category=ContractCategory.SYMBOLIC_MATH,
                            rule="derivation_drift",
                            message=a,
                            severity="CRITICAL",
                            remediation_hint="Ensure each successive derivation step is symbolically equivalent.",
                        )
                    )
            symbolic_verified = symbolic_verified and deriv_ok

        # 4. Numeric Bounds Checks
        if numeric_bounds:
            for expr_str, min_b, max_b in numeric_bounds:
                b_ok, val, b_msg = self.sympy_verifier.verify_numeric_bounds(expr_str, min_b, max_b)
                if not b_ok:
                    violations.append(
                        ContractViolation(
                            category=ContractCategory.SYMBOLIC_MATH,
                            rule="numerical_boundary_violation",
                            message=b_msg,
                            severity="CRITICAL",
                            remediation_hint=f"Evaluate '{expr_str}' within bounds [{min_b}, {max_b}].",
                        )
                    )

        critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
        passed = critical_count == 0
        confidence = pv_report.confidence if passed else max(0.1, pv_report.confidence - (0.25 * critical_count))

        for v in violations:
            if v.remediation_hint and v.remediation_hint not in remediation_hints:
                remediation_hints.append(v.remediation_hint)

        duration_ms = (time.time() - t0) * 1000.0
        return ContractGateVerdict(
            passed=passed,
            confidence=confidence,
            verdict_id=verdict_id,
            violations=violations,
            remediation_hints=remediation_hints,
            ast_score=1.0,
            symbolic_verified=symbolic_verified,
            process_mode=pv_report.system_mode,
            duration_ms=duration_ms,
            details={"process_verifier_confidence": pv_report.confidence},
        )

    def verify_task_execution(self, task: TaskNode, execution_output: str) -> ContractGateVerdict:
        """
        Closed-loop audit of a completed TaskNode execution output.
        Inspects task.metadata and verification_contract to apply appropriate checks.
        """
        # If task explicitly specifies a code contract
        meta = task.metadata or {}
        contract_type = meta.get("contract_type", "auto")

        # Auto-detection
        if contract_type == "code" or ("def " in execution_output or "class " in execution_output):
            req_symbols = meta.get("required_symbols", [])
            strict_simplicity = meta.get("strict_simplicity", True)
            return self.verify_code(
                code=execution_output,
                required_symbols=req_symbols,
                strict_simplicity=strict_simplicity,
            )

        if contract_type == "math" or "symbolic_equations" in meta:
            equations = meta.get("symbolic_equations", [])
            steps = meta.get("derivation_steps", [])
            bounds = meta.get("numeric_bounds", [])
            return self.verify_math_reasoning(
                reasoning_text=execution_output,
                symbolic_equations=equations,
                derivation_steps=steps,
                numeric_bounds=bounds,
            )

        # General step verification through ProcessVerifier
        t0 = time.time()
        verdict_id = f"cg-step-{uuid.uuid4().hex[:8]}"
        pv_report = self.process_verifier.verify_step(execution_output, step_type="execution")

        violations: List[ContractViolation] = []
        if not pv_report.passed:
            for a in pv_report.anomalies:
                violations.append(
                    ContractViolation(
                        category=ContractCategory.RUNTIME_CONTRACT,
                        rule="process_verifier_failure",
                        message=a,
                        severity="CRITICAL",
                        remediation_hint="Rectify output format and eliminate refusal or incomplete markers.",
                    )
                )

        duration_ms = (time.time() - t0) * 1000.0
        return ContractGateVerdict(
            passed=pv_report.passed,
            confidence=pv_report.confidence,
            verdict_id=verdict_id,
            violations=violations,
            remediation_hints=[v.remediation_hint for v in violations if v.remediation_hint],
            ast_score=1.0,
            symbolic_verified=False,
            process_mode=pv_report.system_mode,
            duration_ms=duration_ms,
            details=pv_report.details,
        )


_GLOBAL_CONTRACT_GATE: Optional[NativeContractGate] = None


def get_native_contract_gate() -> NativeContractGate:
    """Singleton getter for NativeContractGate."""
    global _GLOBAL_CONTRACT_GATE
    if _GLOBAL_CONTRACT_GATE is None:
        _GLOBAL_CONTRACT_GATE = NativeContractGate()
    return _GLOBAL_CONTRACT_GATE
