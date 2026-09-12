"""
Phase 9: Continual Harness with Automated /refine Loop
======================================================
Automated post-execution trajectory evaluator and rule extractor.
Analyzes execution outcomes, extracts new negative constraints and playbooks,
and updates the durable ExperienceStore without base prompt drift.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from .experience_store import ExperienceStore, create_experience_store
except ImportError:
    from hermes_core.experience_store import ExperienceStore, create_experience_store


@dataclass
class RefineVerdict:
    task_id: str
    passed: bool
    new_negative_constraints: List[str]
    new_playbooks: List[str]
    compute_efficiency_notes: List[str]
    duration_ms: float


class ContinualRefineLoop:
    """
    Evaluates completed task trajectories and refines the active knowledge state.
    """

    def __init__(self, experience_store: Optional[ExperienceStore] = None):
        self.experience_store = experience_store or create_experience_store()

    def refine_turn(
        self,
        task_id: str,
        task_description: str,
        tool_calls: List[Dict[str, Any]],
        outcome: str,
        token_usage: int,
        duration_sec: float,
        error_traces: Optional[List[str]] = None,
    ) -> RefineVerdict:
        """Processes a finished execution turn and automatically refines rules."""
        t0 = time.perf_counter()

        # 1. Record episode
        self.experience_store.record_episode(
            episode_id=f"refine_{task_id}",
            task_description=task_description,
            subsystem="continual_harness",
            tool_calls=tool_calls,
            outcome=outcome,
            token_usage=token_usage,
            duration_sec=duration_sec,
            error_traces=error_traces or [],
        )

        # 2. Extract refined constraints and playbooks
        constraints = self.experience_store.generate_negative_constraints(max_constraints=3)
        playbooks = self.experience_store.generate_positive_playbooks(max_playbooks=2)
        waste = self.experience_store.detect_compute_waste()

        waste_notes = [w["recommendation"] for w in waste]
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return RefineVerdict(
            task_id=task_id,
            passed=(outcome == "SUCCESS"),
            new_negative_constraints=constraints,
            new_playbooks=playbooks,
            compute_efficiency_notes=waste_notes,
            duration_ms=round(elapsed_ms, 2),
        )


def create_continual_refine_loop(
    experience_store: Optional[ExperienceStore] = None,
) -> ContinualRefineLoop:
    return ContinualRefineLoop(experience_store=experience_store)
