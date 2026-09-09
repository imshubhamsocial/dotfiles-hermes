"""
Cactus Hybrid Uncertainty Detection & Autonomous Clarification Gate (Track 4 - Phase 4.1)
==========================================================================================
Google Gemma & Agent OS calibration pattern:
Combines verbalized self-confidence / linguistic hedging markers with empirical
action risk (destructive tool blast radius) and trajectory failure streaks to detect
high-uncertainty states BEFORE catastrophic execution.

When hybrid uncertainty crosses the safety threshold, the agent autonomously halts
execution, prevents destructive edits, and solicits targeted clarifying questions
from human-in-the-loop (HiTL) or user oversight.

Zero VRAM Law: 100% CPU-bound, deterministic execution, 0 MiB GPU VRAM contention.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# High-uncertainty verbalized linguistic hedges
UNCERTAINTY_HEDGES: Set[str] = {
    "unsure",
    "not sure",
    "might break",
    "might not work",
    "probably",
    "perhaps",
    "speculative",
    "guess",
    "unclear",
    "ambiguous",
    "assume without verifying",
    "could fail",
    "untested hypothesis",
    "risky",
    "conflicted",
    "doubtful",
    "tentative",
    "hesitant",
    "unverified assumption",
}

# High-certainty affirmative anchors (counter-evidence against uncertainty)
CERTAINTY_ANCHORS: Set[str] = {
    "verified",
    "proven",
    "asserted",
    "deterministic",
    "confirmed",
    "guaranteed",
    "passed tests",
    "formally proved",
}

# Mutating & potentially destructive tools
MUTATING_TOOLS: Set[str] = {
    "write_file",
    "patch_file",
    "rm_file",
    "delete_file",
    "apply_diff",
    "modify_file",
}

CRITICAL_SYSTEM_PATH_PATTERNS: List[str] = [
    r"hermes_core/",
    r"\.hermes/src/",
    r"Makefile$",
    r"sys-deps",
    r"pyproject\.toml$",
    r"config\.yaml$",
    r"settings\.json$",
]

DESTRUCTIVE_COMMAND_PATTERNS: List[str] = [
    r"\brm\s+-[rf]{1,2}\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[xfd]{1,3}\b",
    r"\bdrop\s+database\b",
    r"\bdrop\s+table\b",
    r"\btruncate\s+table\b",
    r"\bmkfs\b",
    r"\bkill\s+-9\b",
]


@dataclass
class CactusUncertaintyScore:
    """Unified hybrid uncertainty evaluation report."""
    score: float                         # 0.0 (certain) to 1.0 (extreme uncertainty)
    verbalized_uncertainty: float        # 0.0 to 1.0 from verbalized markers / confidence
    risk_score: float                    # 0.0 to 1.0 from tool blast radius / file criticality
    history_score: float                 # 0.0 to 1.0 from failure streaks
    is_destructive: bool                 # whether candidate action mutates system/repo state
    is_uncertain: bool                   # whether score >= threshold
    hedging_markers: List[str] = field(default_factory=list)
    clarification_questions: List[str] = field(default_factory=list)
    recommendation: str = "PROCEED"      # "PROCEED", "HALT_FOR_CLARIFICATION", "ABORT_DESTRUCTIVE_ACTION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "verbalized_uncertainty": round(self.verbalized_uncertainty, 4),
            "risk_score": round(self.risk_score, 4),
            "history_score": round(self.history_score, 4),
            "is_destructive": self.is_destructive,
            "is_uncertain": self.is_uncertain,
            "hedging_markers": self.hedging_markers,
            "clarification_questions": self.clarification_questions,
            "recommendation": self.recommendation,
        }


class CactusHybridDetector:
    """
    Cactus Hybrid Uncertainty Detector.
    Synthesizes model self-reported calibration with deterministic structural safeguards.
    """

    def __init__(
        self,
        uncertainty_threshold: float = 0.70,
        abort_threshold: float = 0.85,
        weight_verbalized: float = 0.50,
        weight_risk: float = 0.30,
        weight_history: float = 0.20,
    ):
        self.uncertainty_threshold = uncertainty_threshold
        self.abort_threshold = abort_threshold
        self.w_verbalized = weight_verbalized
        self.w_risk = weight_risk
        self.w_history = weight_history

    def extract_verbalized_uncertainty(
        self,
        text: Optional[str] = None,
        explicit_confidence: Optional[float] = None,
    ) -> Tuple[float, List[str]]:
        """
        Calculates verbalized uncertainty score [0.0, 1.0] and identifies hedging markers.
        If explicit_confidence in [0.0, 1.0] is provided: uncertainty = (1.0 - explicit_confidence).
        If thought text is present: scans for lexical hedges and certainty anchors.
        """
        markers_found: List[str] = []
        text_uncertainty = 0.0

        if text:
            lower_text = text.lower()
            for hedge in UNCERTAINTY_HEDGES:
                if re.search(r"\b" + re.escape(hedge) + r"\b", lower_text):
                    markers_found.append(hedge)

            anchor_count = 0
            for anchor in CERTAINTY_ANCHORS:
                if re.search(r"\b" + re.escape(anchor) + r"\b", lower_text):
                    anchor_count += 1

            # Base score from hedging frequency
            if markers_found:
                raw_score = min(1.0, 0.35 + (len(markers_found) - 1) * 0.20)
                # Dampen if strong affirmative verification anchors present
                text_uncertainty = max(0.0, raw_score - (anchor_count * 0.20))
            elif anchor_count > 0:
                text_uncertainty = 0.05
            else:
                text_uncertainty = 0.20  # Neutral baseline when unstated

        if explicit_confidence is not None:
            clamped_conf = max(0.0, min(1.0, float(explicit_confidence)))
            conf_uncertainty = 1.0 - clamped_conf
            if text:
                # Blend explicit confidence with linguistic markers
                return round(0.6 * conf_uncertainty + 0.4 * text_uncertainty, 4), markers_found
            return round(conf_uncertainty, 4), markers_found

        return round(text_uncertainty, 4), markers_found

    def assess_action_risk(
        self,
        tool: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, bool]:
        """
        Assesses structural blast radius and whether the tool is destructive.
        Returns: (risk_score [0.0, 1.0], is_destructive)
        """
        args = args or {}
        tool_lower = (tool or "").lower()

        # Check mutating file tools
        if tool_lower in MUTATING_TOOLS:
            filepath = str(args.get("filepath") or args.get("path") or args.get("file") or "")
            # Check critical core system file
            is_critical = any(re.search(pat, filepath) for pat in CRITICAL_SYSTEM_PATH_PATTERNS)
            if is_critical:
                return 0.90, True
            return 0.60, True

        # Check bash execution
        if tool_lower in ("bash", "execute_bash", "shell", "run_command"):
            cmd = str(args.get("command") or args.get("cmd") or args.get("command_line") or "")
            is_destructive_cmd = any(re.search(pat, cmd, re.IGNORECASE) for pat in DESTRUCTIVE_COMMAND_PATTERNS)
            if is_destructive_cmd:
                return 0.95, True
            return 0.30, False

        # Safe read-only / introspection tools
        if tool_lower in ("read_file", "view_file", "grep_search", "find_by_name", "list_dir", "cat"):
            return 0.05, False

        return 0.20, False

    def assess_history_risk(
        self,
        consecutive_failures: int = 0,
        recent_failures_count: int = 0,
    ) -> float:
        """Computes trajectory risk from consecutive failure streaks."""
        if consecutive_failures >= 2:
            return 1.0  # 2-Strike Tabu ceiling
        if consecutive_failures == 1:
            return 0.50
        return min(0.80, recent_failures_count * 0.20)

    def generate_clarification_questions(
        self,
        tool: str,
        args: Dict[str, Any],
        hedging_markers: List[str],
        consecutive_failures: int,
    ) -> List[str]:
        """Synthesizes deterministic, targeted questions when uncertainty halts execution."""
        questions: List[str] = []
        filepath = str(args.get("filepath") or args.get("path") or args.get("file") or "")

        if filepath:
            is_critical = any(re.search(pat, filepath) for pat in CRITICAL_SYSTEM_PATH_PATTERNS)
            if is_critical:
                questions.append(
                    f"Target '{filepath}' is a core system component. Should a clean branch or backup be created before applying modifications?"
                )
            else:
                questions.append(
                    f"Confirm if overwriting/patching '{filepath}' with the proposed diff is intended."
                )

        if hedging_markers:
            hedges_str = ", ".join(f"'{h}'" for h in hedging_markers[:3])
            questions.append(
                f"Agent expressed hesitation ({hedges_str}). Please clarify requirements or provide expected inputs before proceeding."
            )

        if consecutive_failures >= 1:
            questions.append(
                f"Prior attempt failed ({consecutive_failures} failure streak). Would you prefer to rollback to the last known-good ancestor node or switch operator?"
            )

        if not questions:
            questions.append(
                f"Uncertainty detected before executing '{tool}'. Please confirm permission to proceed."
            )

        return questions

    def evaluate_action(
        self,
        tool: str,
        args: Optional[Dict[str, Any]] = None,
        thought: Optional[str] = None,
        verbalized_confidence: Optional[float] = None,
        consecutive_failures: int = 0,
        recent_failures_count: int = 0,
    ) -> CactusUncertaintyScore:
        """
        Executes full hybrid evaluation over an agent's candidate action.
        Synthesizes verbalized confidence + blast radius + failure history.
        """
        args = args or {}
        v_unc, markers = self.extract_verbalized_uncertainty(thought, verbalized_confidence)
        risk_score, is_destructive = self.assess_action_risk(tool, args)
        hist_score = self.assess_history_risk(consecutive_failures, recent_failures_count)

        # Weighted hybrid uncertainty calculation
        hybrid_score = (
            self.w_verbalized * v_unc
            + self.w_risk * risk_score
            + self.w_history * hist_score
        )
        clamped_score = max(0.0, min(1.0, round(hybrid_score, 4)))

        is_uncertain = (clamped_score >= self.uncertainty_threshold)

        # Recommendation and clarification generation
        clarification_qs: List[str] = []
        if is_uncertain and is_destructive:
            if clamped_score >= self.abort_threshold:
                recommendation = "ABORT_DESTRUCTIVE_ACTION"
            else:
                recommendation = "HALT_FOR_CLARIFICATION"
            clarification_qs = self.generate_clarification_questions(
                tool, args, markers, consecutive_failures
            )
        elif is_uncertain:
            recommendation = "FLAG_CAUTION"
        else:
            recommendation = "PROCEED"

        return CactusUncertaintyScore(
            score=clamped_score,
            verbalized_uncertainty=v_unc,
            risk_score=risk_score,
            history_score=hist_score,
            is_destructive=is_destructive,
            is_uncertain=is_uncertain,
            hedging_markers=markers,
            clarification_questions=clarification_qs,
            recommendation=recommendation,
        )
