"""
Shannon Entropy Execution Rail & Deterministic Process Reward Model (PRM).
Enterprise safety and verification:
1. Shannon Entropy Guard: Filters context bloat (H < 1.2) and obfuscation/exfiltration (H > 6.5).
2. Deterministic AST PRM: Evaluates code modifications at 0 VRAM cost before bash execution.
"""

from __future__ import annotations

import ast
import math
from collections import Counter
from typing import Tuple


class ShannonEntropyRail:
    """Evaluates payload information density to prevent context degradation and obfuscation."""

    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Calculates Shannon entropy H = -sum(p * log2(p)) in bits/char."""
        if not text:
            return 0.0
        counts = Counter(text)
        length = len(text)
        return -sum((c / length) * math.log2(c / length) for c in counts.values())

    @classmethod
    def evaluate_payload(cls, content: str, min_h: float = 1.2, max_h: float = 6.5) -> Tuple[bool, str]:
        """
        Validates payload against entropy safety envelope.
        Short strings (<64 chars) are exempted to prevent false positives.
        """
        if len(content) < 64:
            return True, "Payload within length bypass threshold."

        h = cls.calculate_entropy(content)
        if h < min_h:
            return False, f"Entropy Rail Violation: Low entropy detected ({h:.2f} < {min_h}). Context bloat rejected."
        if h > max_h:
            return False, f"Entropy Rail Violation: High entropy detected ({h:.2f} > {max_h}). Obfuscation rejected."
        return True, f"Entropy nominal ({h:.2f})."


class DeterministicCodePRM:
    """Zero-VRAM Process Reward Model validating intermediate code edit steps."""

    @staticmethod
    def score_diff_step(
        patch_block: str,
        max_lines: int = 80,
    ) -> Tuple[float, str]:
        """
        Evaluates step quality and safety:
        - Format validity (SEARCH/REPLACE)
        - Diff size bound (minimal invasiveness)
        - AST parse validation on replacement code
        Returns score (0.0 to 1.0) and diagnostic message.
        """
        lines = patch_block.splitlines()
        if len(lines) > max_lines:
            return 0.2, f"PRM Penalty: Diff exceeds {max_lines} lines ({len(lines)} lines). Decompose into smaller step."

        if "<<<<<<< SEARCH" not in patch_block or "=======" not in patch_block:
            return 0.1, "PRM Penalty: Malformed SEARCH/REPLACE syntax."

        # Extract replacement content
        parts = patch_block.split("=======")
        if len(parts) < 2:
            return 0.1, "PRM Penalty: Missing replacement block."

        replace_part = parts[1].split(">>>>>>> REPLACE")[0]

        # Verify AST syntax if python code is present
        try:
            ast.parse(replace_part)
        except SyntaxError as e:
            # Check if this might be partial code block or invalid syntax
            # If it cannot parse standalone and doesn't look like indented block, flag it
            return 0.4, f"PRM Warning: Replacement code contains syntax errors: {e}"

        return 1.0, "PRM Passed: Code edit syntactically sound and bounded."
