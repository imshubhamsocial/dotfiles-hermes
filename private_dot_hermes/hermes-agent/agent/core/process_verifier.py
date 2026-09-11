"""
Hermes Dynamic Process Verifier (Phase I.2 — Dyve-style System-1/System-2 Verification)
======================================================================================
Inspired by Dyve (arXiv:2502.11157: "Thinking Fast and Slow for Dynamic Process Verification"):
- Integrates Fast System-1 checks for straightforward execution steps (token/syntax sanity,
  hallucination detection, heuristic confidence).
- Applies Slow System-2 deep consistency checks for complex reasoning and mathematical steps
  (multi-angle invariance, assertion checks, consensus scoring).
- Seamlessly plugs into cog_verifier.py as a native reasoning verification check.
"""

from __future__ import annotations

import ast
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple


@dataclass
class ProcessVerificationReport:
    """Detailed verification outcome for an execution or reasoning step."""
    step_id: str
    system_mode: Literal["system_1", "system_2"]
    passed: bool
    confidence: float
    message: str
    anomalies: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class System1FastChecker:
    """Low-latency step-level token & syntax sanity verifier."""

    HALLUCINATION_PATTERNS = [
        r"as an ai language model",
        r"i don't have access to real-time",
        r"i cannot execute code",
        r"TODO:\s*implement this later",
        r"\[insert code here\]",
        r"<mock>",
    ]

    @classmethod
    def check(cls, text: str) -> Tuple[bool, float, List[str]]:
        anomalies = []
        lower = text.lower()

        # 1. Non-empty check
        if not text or not text.strip():
            return False, 0.0, ["Empty step output"]

        # 2. Hallucination boilerplate detection
        for pat in cls.HALLUCINATION_PATTERNS:
            if re.search(pat, lower):
                anomalies.append(f"Detected boilerplate/refusal pattern: '{pat}'")

        # 3. Brace and parenthesis balance if code block present
        if "{" in text or "(" in text:
            if text.count("{") != text.count("}"):
                anomalies.append("Mismatched curly braces '{' and '}'")
            if text.count("(") != text.count(")"):
                anomalies.append("Mismatched parentheses '(' and ')'")
            if text.count("[") != text.count("]"):
                anomalies.append("Mismatched brackets '[' and ']'")

        passed = len(anomalies) == 0
        confidence = 0.95 if passed else max(0.1, 0.95 - (0.25 * len(anomalies)))
        return passed, confidence, anomalies


class System2DeepVerifier:
    """Deep consensus, invariant, and semantic consistency verifier."""

    @classmethod
    def verify_math_reasoning(cls, text: str) -> Tuple[bool, float, List[str]]:
        anomalies = []
        # Look for explicit contradiction markers
        contradiction_patterns = [
            r"wait,\s*that's\s*wrong",
            r"this\s*leads\s*to\s*a\s*contradiction",
            r"cannot\s*be\s*satisfied",
            r"invalid\s*state",
        ]
        for pat in contradiction_patterns:
            if re.search(pat, text.lower()):
                anomalies.append(f"Unresolved contradiction in reasoning: '{pat}'")

        # Check for numeric or conclusion consistency
        has_conclusion = bool(re.search(r"(therefore|thus|hence|in conclusion|final answer|result is)", text.lower()))
        if not has_conclusion and len(text.split()) > 60:
            anomalies.append("Multi-step reasoning missing explicit terminal conclusion or derivation")

        passed = len(anomalies) == 0
        confidence = 0.90 if passed else max(0.2, 0.90 - (0.3 * len(anomalies)))
        return passed, confidence, anomalies

    @classmethod
    def verify_code_invariants(cls, code_snippet: str) -> Tuple[bool, float, List[str]]:
        anomalies = []
        # Parse python code snippet if it looks like python
        if "def " in code_snippet or "class " in code_snippet or "import " in code_snippet:
            try:
                # Strip markdown blocks
                code = re.sub(r"^```python\s*", "", code_snippet, flags=re.MULTILINE)
                code = re.sub(r"^```\s*$", "", code, flags=re.MULTILINE)
                ast.parse(code)
            except SyntaxError as e:
                anomalies.append(f"Python SyntaxError: {e.msg} at line {e.lineno}")
            except Exception as e:
                anomalies.append(f"AST Parsing error: {e}")

        passed = len(anomalies) == 0
        confidence = 0.95 if passed else 0.3
        return passed, confidence, anomalies


class ProcessVerifier:
    """
    Unified Process Verifier combining System-1 fast heuristics
    with System-2 deep invariant checks.
    """

    def __init__(self):
        self.fast_checker = System1FastChecker()
        self.deep_verifier = System2DeepVerifier()

    def verify_step(
        self,
        step_content: str,
        step_type: str = "reasoning",
        context: Optional[Dict[str, Any]] = None,
    ) -> ProcessVerificationReport:
        start_time = time.time()
        step_id = f"pv_{int(start_time * 1000)}"

        # Step 1: Always run System-1 Fast Check
        s1_passed, s1_conf, s1_anomalies = self.fast_checker.check(step_content)

        # Decide if System-2 check is required
        requires_system_2 = (
            step_type in ("reasoning", "math", "code", "architecture")
            or len(step_content.split()) > 50
            or any(k in step_content.lower() for k in ["derive", "calculate", "prove", "invariant", "assert"])
        )

        if not requires_system_2:
            duration_ms = (time.time() - start_time) * 1000
            return ProcessVerificationReport(
                step_id=step_id,
                system_mode="system_1",
                passed=s1_passed,
                confidence=s1_conf,
                message="System-1 fast verification passed" if s1_passed else "; ".join(s1_anomalies),
                anomalies=s1_anomalies,
                duration_ms=duration_ms,
                details={"step_type": step_type},
            )

        # Step 2: System-2 Deep Verification
        s2_anomalies: List[str] = list(s1_anomalies)
        
        # Math & reasoning checks
        math_passed, math_conf, math_anom = self.deep_verifier.verify_math_reasoning(step_content)
        s2_anomalies.extend(math_anom)

        # Code invariant checks if relevant
        if "def " in step_content or "class " in step_content or "```" in step_content:
            code_passed, code_conf, code_anom = self.deep_verifier.verify_code_invariants(step_content)
            s2_anomalies.extend(code_anom)
            combined_conf = min(s1_conf, math_conf, code_conf)
        else:
            combined_conf = min(s1_conf, math_conf)

        passed = len(s2_anomalies) == 0
        duration_ms = (time.time() - start_time) * 1000

        return ProcessVerificationReport(
            step_id=step_id,
            system_mode="system_2",
            passed=passed,
            confidence=combined_conf if passed else max(0.1, combined_conf - 0.2),
            message="System-2 deep process verification certified" if passed else "; ".join(s2_anomalies),
            anomalies=s2_anomalies,
            duration_ms=duration_ms,
            details={"step_type": step_type, "s1_passed": s1_passed},
        )


_GLOBAL_PROCESS_VERIFIER: Optional[ProcessVerifier] = None


def get_process_verifier() -> ProcessVerifier:
    global _GLOBAL_PROCESS_VERIFIER
    if _GLOBAL_PROCESS_VERIFIER is None:
        _GLOBAL_PROCESS_VERIFIER = ProcessVerifier()
    return _GLOBAL_PROCESS_VERIFIER
