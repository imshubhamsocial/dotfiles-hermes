"""
Loop Engineering: Machine-Checkable Stop Conditions (Milestone U77)
===================================================================
Provides deterministic termination contracts for autonomous agent loops:
  - max_iterations (bounds unbounded execution)
  - success_signal (evaluates machine-checkable success criteria)
  - vram_sentinel (terminates if VRAM exceeds 4,812 MiB safety guard)
  - tabu_failure_limit (enforces 2-Strike Tabu reset upon repeated failure)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LoopControlSignal:
    action: str  # "CONTINUE", "STOP_SUCCESS", "STOP_MAX_ITER", "STOP_VRAM_BREACH", "STOP_TABU_TRIP", "STOP_UNCERTAINTY_BREACH"
    reason: str
    iteration: int
    should_halt: bool = False
    clarification_questions: List[str] = field(default_factory=list)


@dataclass
class LoopContract:
    max_iterations: int = 5
    vram_ceiling_mib: int = 4812
    consecutive_failure_limit: int = 2
    uncertainty_ceiling: float = 0.70
    enable_cactus_uncertainty: bool = True
    required_success_signals: List[str] = field(default_factory=lambda: ["pytest_pass"])


class LoopController:
    """Evaluates agent iteration states against strict loop contracts."""

    def __init__(self, contract: Optional[LoopContract] = None):
        self.contract = contract or LoopContract()
        self.current_iteration = 0
        self.consecutive_failures = 0
        self.history: List[Dict[str, Any]] = []

    def evaluate_step(
        self,
        vram_usage_mib: Optional[int] = None,
        step_success: bool = True,
        signals: Optional[Dict[str, Any]] = None,
        uncertainty_score: Optional[float] = None,
        is_destructive: bool = False,
        clarification_questions: Optional[List[str]] = None,
    ) -> LoopControlSignal:
        self.current_iteration += 1
        signals = signals or {}

        # 1. Hardware VRAM Sentinel Check (Hard Ceiling <= 4,812 MiB)
        if vram_usage_mib is not None and vram_usage_mib > self.contract.vram_ceiling_mib:
            return LoopControlSignal(
                action="STOP_VRAM_BREACH",
                reason=f"VRAM sentinel breached: {vram_usage_mib} MiB > {self.contract.vram_ceiling_mib} MiB ceiling.",
                iteration=self.current_iteration,
                should_halt=True,
            )

        # 2. Tabu Failure Counter
        if not step_success:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        if self.consecutive_failures >= self.contract.consecutive_failure_limit:
            return LoopControlSignal(
                action="STOP_TABU_TRIP",
                reason=f"2-Strike Tabu rule tripped ({self.consecutive_failures} consecutive failures).",
                iteration=self.current_iteration,
                should_halt=True,
            )

        # 3. Cactus Hybrid Uncertainty Guard (Phase 4.1)
        if (
            self.contract.enable_cactus_uncertainty
            and uncertainty_score is not None
            and uncertainty_score >= self.contract.uncertainty_ceiling
            and is_destructive
        ):
            return LoopControlSignal(
                action="STOP_UNCERTAINTY_BREACH",
                reason=(
                    f"Cactus hybrid uncertainty ceiling breached ({uncertainty_score:.2f} >= "
                    f"{self.contract.uncertainty_ceiling:.2f}) before destructive action; "
                    f"halting for clarification."
                ),
                iteration=self.current_iteration,
                should_halt=True,
                clarification_questions=clarification_questions or [],
            )

        # 4. Success Signal Verification
        all_signals_satisfied = True
        for req in self.contract.required_success_signals:
            if not signals.get(req, False):
                all_signals_satisfied = False
                break

        if all_signals_satisfied and self.contract.required_success_signals:
            return LoopControlSignal(
                action="STOP_SUCCESS",
                reason="All machine-checkable success signals satisfied.",
                iteration=self.current_iteration,
                should_halt=True,
            )

        # 4. Max Iteration Boundary Check
        if self.current_iteration >= self.contract.max_iterations:
            return LoopControlSignal(
                action="STOP_MAX_ITER",
                reason=f"Reached maximum iteration ceiling ({self.contract.max_iterations}).",
                iteration=self.current_iteration,
                should_halt=True,
            )

        return LoopControlSignal(
            action="CONTINUE",
            reason=f"Iteration {self.current_iteration} within bounds.",
            iteration=self.current_iteration,
            should_halt=False,
        )


def create_loop_controller(contract: Optional[LoopContract] = None) -> LoopController:
    return LoopController(contract=contract)
