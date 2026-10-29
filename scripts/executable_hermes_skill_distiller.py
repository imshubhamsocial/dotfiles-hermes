#!/usr/bin/env python3
"""
Hermes Closed-Loop AGI Gate: Non-Parametric Contrastive Skill Distillation
Extracts Minimal Contrastive Repair Tuples <sigma, a_failed, e_trace, a_verified, delta_diff>
from verified execution receipts and indexes into OpenViking TrieHI (viking://skills/).
Enforces 3-Gate Epistemic Quarantine (0.0 MiB GPU VRAM, zero backpropagation).
"""
import difflib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MinimalContrastiveTuple:
    """Represents a contrastive problem-failure-repair learning unit."""

    problem_sig: str
    failed_action: str
    error_trace: str
    verified_resolution: str
    unified_diff: str


class ContrastiveSkillDistiller:
    """
    Distills and crystallizes procedural skills into ~/.hermes/skills/ and OpenViking TrieHI.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir:
            self.skills_dir = Path(base_dir)
        else:
            self.skills_dir = Path(os.path.expanduser("~/.hermes/skills"))
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_minimal_contrastive_tuple(
        problem_sig: str,
        failed_code: str,
        error_trace: str,
        verified_code: str,
    ) -> MinimalContrastiveTuple:
        """Extract minimal diff and error signature."""
        diff_lines = list(
            difflib.unified_diff(
                failed_code.splitlines(keepends=True),
                verified_code.splitlines(keepends=True),
                fromfile="failed_action.py",
                tofile="verified_resolution.py",
                n=3,
            )
        )
        unified_diff = "".join(diff_lines)
        # Head-tail truncation of error trace to bottom 600 bytes
        concise_trace = error_trace[-600:].strip() if len(error_trace) > 600 else error_trace.strip()

        return MinimalContrastiveTuple(
            problem_sig=problem_sig.strip(),
            failed_action=failed_code.strip(),
            error_trace=concise_trace,
            verified_resolution=verified_code.strip(),
            unified_diff=unified_diff.strip(),
        )

    @staticmethod
    def verify_epistemic_quarantine(receipt: dict) -> bool:
        """
        Verify Epistemic Quarantine Gate:
        1. exitstatus == 0
        2. epistemic_score == 1.0 (or not flagged false positive)
        3. Zero prompt-injection / role-override tokens.
        """
        if receipt.get("exitstatus") != 0:
            return False

        if receipt.get("false_positive_detected") is True:
            return False

        # Check for injection patterns
        receipt_str = json.dumps(receipt).lower()
        injection_patterns = [
            "ignore previous instructions",
            "system override",
            "<script>",
            "drop table",
        ]
        return not any(p in receipt_str for p in injection_patterns)

    def crystallize_skill_md(
        self,
        domain: str,
        skill_slug: str,
        contrastive_data: MinimalContrastiveTuple,
    ) -> Path:
        """
        Crystallize skill into ~/.hermes/skills/<domain>/<skill_slug>/SKILL.md
        with progressive L0 / L1 / L2 TrieHI structure.
        """
        target_dir = self.skills_dir / domain / skill_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        skill_file = target_dir / "SKILL.md"

        # L0 Abstract (<= 256 chars)
        clean_slug = skill_slug.replace("_", " ")
        l0_abstract = f"Skill {clean_slug} resolves {contrastive_data.problem_sig[:80]} by correcting failure pattern."[:250]

        # L1 Overview (Trigger Signature, Known Failure Trap, Resolution Contract)
        l1_overview = (
            f"### Trigger Signature\n"
            f"- Problem Pattern: `{contrastive_data.problem_sig}`\n\n"
            f"### Known 4B Failure Trap\n"
            f"```python\n{contrastive_data.failed_action[:500]}\n```\n"
            f"Exception Encountered: `{contrastive_data.error_trace[:200]}`\n\n"
            f"### Canonical Resolution Contract\n"
            f"- Apply verified structural repair:\n"
            f"```python\n{contrastive_data.verified_resolution[:500]}\n```"
        )

        # L2 Details (Full Unified Diff and Trace)
        l2_details = (
            f"### Minimal Contrastive Diff\n"
            f"```diff\n{contrastive_data.unified_diff}\n```\n\n"
            f"### Full Error Traceback\n"
            f"```text\n{contrastive_data.error_trace}\n```"
        )

        content = (
            f"# Skill: {clean_slug.title()}\n\n"
            f"<!-- L0_ABSTRACT_START -->\n{l0_abstract}\n<!-- L0_ABSTRACT_END -->\n\n"
            f"<!-- L1_OVERVIEW_START -->\n{l1_overview}\n<!-- L1_OVERVIEW_END -->\n\n"
            f"<!-- L2_DETAILS_START -->\n{l2_details}\n<!-- L2_DETAILS_END -->\n"
        )

        skill_file.write_text(content)
        return skill_file

    @staticmethod
    def extract_triehi_tiers(skill_file: Path) -> dict[str, str]:
        """Extract progressive L0, L1, L2 context tiers for OpenViking mounting."""
        text = skill_file.read_text()
        l0_match = re.search(r"<!-- L0_ABSTRACT_START -->(.*?)<!-- L0_ABSTRACT_END -->", text, re.DOTALL)
        l1_match = re.search(r"<!-- L1_OVERVIEW_START -->(.*?)<!-- L1_OVERVIEW_END -->", text, re.DOTALL)
        l2_match = re.search(r"<!-- L2_DETAILS_START -->(.*?)<!-- L2_DETAILS_END -->", text, re.DOTALL)

        return {
            "l0_abstract": l0_match.group(1).strip() if l0_match else text[:256],
            "l1_overview": l1_match.group(1).strip() if l1_match else text[:4000],
            "l2_details": l2_match.group(1).strip() if l2_match else text,
        }


if __name__ == "__main__":
    distiller = ContrastiveSkillDistiller(base_dir="/tmp/test_skills")
    sample_tuple = distiller.extract_minimal_contrastive_tuple(
        problem_sig="HumanEval/130 Tribonacci",
        failed_code="def tri(n):\n    while True:\n        yield 1",
        error_trace="TimeoutError: Runaway generation exceeded token limit",
        verified_code="def tri(n):\n    if n == 0: return [1]\n    return [1, 3]",
    )
    receipt = {"exitstatus": 0, "epistemic_score": 1.0}
    assert distiller.verify_epistemic_quarantine(receipt) is True
    file_path = distiller.crystallize_skill_md("algorithms", "tribonacci_loop_repair", sample_tuple)
    tiers = distiller.extract_triehi_tiers(file_path)
    print("Skill crystallized successfully at:", file_path)
    print("L0 Abstract:", tiers["l0_abstract"])
    sys.exit(0)
