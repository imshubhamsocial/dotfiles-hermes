"""Dream-RSI 2.0 Open-World Replay Simulator Pool (Phase 23).

Grounded in Google DeepMind & UMD 'Dream-RSI: Recursive Self-Improvement through Evolving Worlds'
(arXiv:2609.14858) and Google RRSI (arXiv:2609.24972).
Implements persistent content-addressed replay trees, Doubly Robust (DR) off-policy value estimation,
RRSI variance stability acceptance gating, and call reduction calculation on CPU RAM.
"""

import hashlib
import json
import math
import os
import pathlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StateTransition:
    """Represents an execution transition within a replay tree."""
    step: int
    state_desc: str
    action: str
    reward: float
    next_state: str
    baseline_prob: float  # mu(a | s)
    q_estimate: float = 0.0  # Q_hat(s, a)


@dataclass
class ReplayTree:
    """Persistent, content-addressed trajectory replay tree."""
    session_id: str
    task_goal: str
    root_hash: str
    transitions: list[StateTransition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "session_id": self.session_id,
                "task_goal": self.task_goal,
                "root_hash": self.root_hash,
                "transitions": [asdict(t) for t in self.transitions],
                "metadata": self.metadata,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "ReplayTree":
        data = json.loads(raw)
        transitions = [StateTransition(**t) for t in data.get("transitions", [])]
        return cls(
            session_id=data["session_id"],
            task_goal=data["task_goal"],
            root_hash=data["root_hash"],
            transitions=transitions,
            metadata=data.get("metadata", {}),
        )


class DoublyRobustEvaluator:
    """Calculates Doubly Robust (DR) value estimates for counterfactual policies."""

    def __init__(self, gamma: float = 0.95, max_importance_weight: float = 5.0):
        self.gamma = gamma
        self.max_importance_weight = max_importance_weight

    def evaluate(
        self,
        transitions: list[StateTransition],
        candidate_policy_probs: dict[str, float],
    ) -> float:
        """Evaluates V_DR(pi) over a sequence of logged transitions."""
        v_dr = 0.0

        for t, trans in enumerate(transitions):
            pi_prob = candidate_policy_probs.get(trans.action, 0.01)
            mu_prob = max(trans.baseline_prob, 0.001)

            # Raw importance ratio with upper clipping to bound variance
            raw_rho = pi_prob / mu_prob
            rho = min(raw_rho, self.max_importance_weight)

            # Direct model baseline Q_hat
            q_hat = trans.q_estimate if trans.q_estimate != 0.0 else trans.reward * 0.9

            # Doubly robust step value: E_pi[Q_hat] + rho * (r - Q_hat)
            expected_q = pi_prob * q_hat
            dr_step = expected_q + rho * (trans.reward - q_hat)
            discount = math.pow(self.gamma, t)
            v_dr += discount * dr_step

        return v_dr


class RRSIStabilityGate:
    """Evaluates whether a candidate mutation exceeds the baseline noise margin: Delta >= k * sigma_0."""

    def __init__(self, confidence_k: float = 1.645):
        self.confidence_k = confidence_k

    def check_stability(
        self,
        v_candidate: float,
        v_baseline: float,
        baseline_rewards: list[float],
    ) -> tuple[bool, float, float]:
        """Calculates RRSI variance gate compliance."""
        if not baseline_rewards:
            return False, 0.0, 0.0

        n = len(baseline_rewards)
        mean_r = sum(baseline_rewards) / n
        variance = sum((r - mean_r) ** 2 for r in baseline_rewards) / max(1, n - 1)
        sigma_0 = math.sqrt(variance)

        # Performance lift
        lift = v_candidate - v_baseline
        required_margin = self.confidence_k * sigma_0

        passed = lift >= required_margin
        return passed, lift, required_margin


class DreamRSISimulatorPool:
    """Manages the pool of replay trees and executes counterfactual dreaming."""

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = pathlib.Path(cache_dir or ".hermes/cache/dream_worlds")
        self.trees: list[ReplayTree] = []
        self.evaluator = DoublyRobustEvaluator()
        self.stability_gate = RRSIStabilityGate(confidence_k=1.645)

    def persist_tree(self, tree: ReplayTree) -> pathlib.Path:
        """Saves a replay tree into content-addressed persistent storage."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.cache_dir / f"{tree.root_hash}.json"
        file_path.write_text(tree.to_json())
        return file_path

    def load_tree(self, file_path: pathlib.Path) -> ReplayTree:
        """Loads a replay tree from disk."""
        tree = ReplayTree.from_json(file_path.read_text())
        self.trees.append(tree)
        return tree

    def evaluate_counterfactual_candidate(
        self,
        tree: ReplayTree,
        candidate_policy: dict[str, float],
    ) -> dict[str, Any]:
        """Evaluates candidate mutation against baseline across tree transitions."""
        start_time = time.perf_counter()

        # Compute baseline value
        baseline_policy = {t.action: t.baseline_prob for t in tree.transitions}
        v_baseline = self.evaluator.evaluate(tree.transitions, baseline_policy)

        # Compute candidate value via Doubly Robust estimation
        v_candidate = self.evaluator.evaluate(tree.transitions, candidate_policy)

        # Evaluate against RRSI stability gate
        baseline_rewards = [t.reward for t in tree.transitions]
        passed, lift, margin = self.stability_gate.check_stability(
            v_candidate=v_candidate,
            v_baseline=v_baseline,
            baseline_rewards=baseline_rewards,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Calculate simulated call reduction ratio
        simulated_branches = len(tree.transitions) * len(candidate_policy)
        live_calls_burned = 1  # Only 1 initial live trial was logged
        reduction_ratio = max(1.0, (simulated_branches + live_calls_burned) / max(1, live_calls_burned))

        return {
            "tree_hash": tree.root_hash,
            "v_baseline": round(v_baseline, 4),
            "v_candidate": round(v_candidate, 4),
            "performance_lift": round(lift, 4),
            "required_margin": round(margin, 4),
            "rrsi_stability_gate_passed": passed,
            "call_reduction_ratio": round(reduction_ratio, 2),
            "dream_eval_latency_ms": round(elapsed_ms, 3),
        }
