"""
Milestone U59: Autonomous Reflective Skill Evolution Substrate
==============================================================
Implements Autonomous Self-Improvement & Skill Evolution:
  - User correction & failure reflection capture (ReflectiveLearner)
  - Automatic candidate OpenSkills SKILL.md draft synthesis
  - Dual-arm empirical A/B lift evaluation (SkillEvaluator >= +15% Lift Gate)
  - Automatic promotion into active OpenSkills library (~/.hermes/skills/)
  - Zero GPU VRAM overhead (pure CPU RAMDisk execution)
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

from hermes_core.openskills_manager import OpenSkillsManager, get_openskills_manager
from hermes_core.reflective_learner import CorrectionEvent, ReflectiveLearner, create_reflective_learner
from hermes_core.skill_evaluator import EvaluationEpisode, SkillEvaluator, SkillLiftReport, create_skill_evaluator


@dataclass
class EvolutionCycleResult:
    """Outcome of an autonomous reflective skill evolution cycle."""
    skill_name: str
    candidate_path: str
    lift_report: SkillLiftReport
    promoted: bool
    rejection_reason: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "candidate_path": self.candidate_path,
            "lift_report": self.lift_report.to_dict(),
            "promoted": self.promoted,
            "rejection_reason": self.rejection_reason,
            "duration_ms": round(self.duration_ms, 3),
        }


class SkillEvolutionSubstrate:
    """
    Autonomous Self-Evolving Skill Engine.
    Converts reflection events into empirically tested and certified OpenSkills packages.
    """

    MIN_LIFT_PCT: float = 15.0
    MAX_PROMPT_BLOAT_TOKENS: int = 150

    def __init__(
        self,
        skills_manager: Optional[OpenSkillsManager] = None,
        learner: Optional[ReflectiveLearner] = None,
        evaluator: Optional[SkillEvaluator] = None,
    ):
        self.skills_manager = skills_manager or get_openskills_manager()
        self.learner = learner or create_reflective_learner()
        self.evaluator = evaluator or create_skill_evaluator()

    @property
    def primary_skills_dir(self) -> Path:
        dirs = getattr(self.skills_manager, "skills_dirs", None)
        if dirs and len(dirs) > 0:
            return Path(dirs[0])
        return Path.home() / ".hermes" / "skills"

    def synthesize_candidate_skill(
        self,
        skill_name: str,
        reflection_events: List[CorrectionEvent],
        description: str = "",
        tools: Optional[List[str]] = None,
    ) -> Path:
        """Synthesizes a clean candidate SKILL.md package with YAML frontmatter."""
        target_dir = self.primary_skills_dir / skill_name
        target_dir.mkdir(parents=True, exist_ok=True)
        skill_file = target_dir / "SKILL.md"

        desc = description or f"Expert guidance for {skill_name} workflows."
        tool_list = tools or ["patch_file", "read_file", "execute_command"]
        tool_str = "[" + ", ".join(tool_list) + "]"
        rules_body = "\n".join(f"* {evt.inferred_rule}" for evt in reflection_events)

        content = f"""---
name: {skill_name}
description: {desc}
version: 1.0.0
author: hermes-agent-evolution
license: MIT
platforms: [linux, macos]
tags: [autonomous, evolution, {reflection_events[0].category if reflection_events else 'general'}]
dependencies: []
tools: {tool_str}
---

# {skill_name.replace('_', ' ').title()}

## Operational Mandates
{rules_body}

## Standard Operating Procedure
1. Verify system environment before applying changes.
2. Follow strict behavioral invariants.
3. Validate output through observer gates.
"""
        skill_file.write_text(content, encoding="utf-8")
        return skill_file

    def evaluate_and_promote(
        self,
        skill_name: str,
        baseline_episodes: List[EvaluationEpisode],
        candidate_episodes: List[EvaluationEpisode],
        candidate_prompt_tokens: int = 80,
    ) -> EvolutionCycleResult:
        """Runs A/B benchmark evaluation and promotes or prunes candidate skill."""
        t0 = time.perf_counter()
        candidate_file = self.primary_skills_dir / skill_name / "SKILL.md"

        # Run statistical lift evaluation
        lift_report = self.evaluator.evaluate_skill_lift(
            skill_name=skill_name,
            baseline_episodes=baseline_episodes,
            candidate_episodes=candidate_episodes,
            min_lift_pct=self.MIN_LIFT_PCT,
            max_prompt_bloat=self.MAX_PROMPT_BLOAT_TOKENS,
        )

        promoted = lift_report.certified
        rejection_reason = None if promoted else lift_report.certification_reason

        # If rejected, prune candidate directory to prevent prompt bloat / drift
        if not promoted and candidate_file.parent.exists():
            import shutil
            shutil.rmtree(candidate_file.parent, ignore_errors=True)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return EvolutionCycleResult(
            skill_name=skill_name,
            candidate_path=str(candidate_file),
            lift_report=lift_report,
            promoted=promoted,
            rejection_reason=rejection_reason,
            duration_ms=elapsed_ms,
        )


def create_skill_evolution_substrate(
    skills_manager: Optional[OpenSkillsManager] = None,
    learner: Optional[ReflectiveLearner] = None,
    evaluator: Optional[SkillEvaluator] = None,
) -> SkillEvolutionSubstrate:
    return SkillEvolutionSubstrate(
        skills_manager=skills_manager,
        learner=learner,
        evaluator=evaluator,
    )
