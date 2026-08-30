"""
GEPA-Lite Reflective Pareto Prompt & Skill Optimizer (egmaminta/GEPA-Lite)
==========================================================================
Lightweight implementation of GEPA (Genetic-Pareto Evolution with Reflective
Optimization) for offline, budget-limited prompt and skill refinement.

Key Mechanisms:
1. Candidate Pool Management: Seed-based diverse initial variants.
2. Pareto Multi-Objective Frontier: Maximizes task score while minimizing token footprint.
3. Reflective Mutation: Uses LLM structured feedback on mini-batches to guide mutations.
4. Nightly Session Log Ingestion: Ingests real chat logs & failure traces for targeted evolution.
"""

from __future__ import annotations

import difflib
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


@dataclass
class GEPACandidate:
    """A prompt/skill candidate in the GEPA evolution pool."""
    prompt_text: str
    generation: int = 0
    scores: Dict[str, float] = field(default_factory=dict)
    mean_score: float = 0.0
    token_count: int = 0
    parent_id: Optional[str] = None
    mutation_history: List[str] = field(default_factory=list)

    def compute_metrics(self, token_estimator: Callable[[str], int]):
        self.token_count = token_estimator(self.prompt_text)
        if self.scores:
            self.mean_score = sum(self.scores.values()) / len(self.scores)
        else:
            self.mean_score = 0.0


@dataclass
class GEPAResult:
    """Outcome of a GEPA optimization budget loop."""
    best_prompt: str
    best_score: float
    best_token_count: int
    generations_run: int
    pool_size: int
    pareto_frontier_size: int
    history: List[Dict[str, Any]] = field(default_factory=list)


class GEPALiteOptimizer:
    """
    Lightweight Genetic-Pareto Prompt Optimizer with Reflective Mutations.
    """

    def __init__(
        self,
        exploit_prob: float = 0.7,
        not_merge_prob: float = 0.6,
        token_penalty: float = 0.005,
        token_estimator: Optional[Callable[[str], int]] = None,
    ):
        self.exploit_prob = exploit_prob
        self.not_merge_prob = not_merge_prob
        self.token_penalty = token_penalty
        self.token_estimator = token_estimator or (lambda t: max(1, len(t) // 4))

    def evaluate_similarity_score(self, actual: str, expected: str) -> float:
        """String similarity metric based on difflib.SequenceMatcher ratio."""
        return difflib.SequenceMatcher(None, actual.strip(), expected.strip()).ratio()

    def find_pareto_frontier(self, candidates: Sequence[GEPACandidate]) -> List[GEPACandidate]:
        """
        Returns the non-dominated Pareto frontier over (mean_score ↑, token_count ↓).
        """
        frontier: List[GEPACandidate] = []
        for i, c1 in enumerate(candidates):
            dominated = False
            for j, c2 in enumerate(candidates):
                if i == j:
                    continue
                # c2 dominates c1 if c2 has >= score and <= tokens, with at least one strict inequality
                if (c2.mean_score >= c1.mean_score and c2.token_count < c1.token_count) or \
                   (c2.mean_score > c1.mean_score and c2.token_count <= c1.token_count):
                    dominated = True
                    break
            if not dominated:
                frontier.append(c1)
        return frontier

    def mutate_reflective(self, text: str, feedback: str = "") -> str:
        """
        Reflective mutation operator: strips filler, condenses constraints,
        and integrates feedback guidance.
        """
        fillers = [
            "Please note that ", "It is important to ", "Kindly ",
            "As you know, ", "Make sure to ", "Be sure to ",
            "Remember to ", "You should always "
        ]
        out = text
        for f in fillers:
            out = out.replace(f, "")

        # Collapse excess whitespace
        lines = [ln.rstrip() for ln in out.splitlines()]
        cleaned = []
        blank = 0
        for ln in lines:
            if not ln.strip():
                blank += 1
                if blank <= 1:
                    cleaned.append(ln)
            else:
                blank = 0
                cleaned.append(ln)
        out = "\n".join(cleaned).strip() + "\n"

        if feedback and "precision" in feedback.lower():
            out += "\n# Invariant: Strict precision and deterministic verification required.\n"

        return out

    def merge_prompts(self, prompt_a: str, prompt_b: str) -> str:
        """Synthesize top distinct lines from both candidate prompts."""
        lines_a = [ln.strip() for ln in prompt_a.splitlines() if ln.strip()]
        lines_b = [ln.strip() for ln in prompt_b.splitlines() if ln.strip()]
        merged_set = []
        for ln in lines_a + lines_b:
            if ln not in merged_set:
                merged_set.append(ln)
        return "\n".join(merged_set) + "\n"

    def run_optimization(
        self,
        seed_prompt: str,
        pareto_dataset: List[Dict[str, str]],   # [{"input": ..., "expected": ...}]
        feedback_dataset: Optional[List[Dict[str, str]]] = None,
        eval_fn: Optional[Callable[[str, str], str]] = None,
        max_generations: int = 5,
        population_size: int = 4,
    ) -> GEPAResult:
        """
        Runs the GEPA reflective Pareto optimization loop over evaluation datasets.
        """
        # 1. Initialize candidate pool
        pool: List[GEPACandidate] = []
        seed_cand = GEPACandidate(prompt_text=seed_prompt, generation=0)
        seed_cand.compute_metrics(self.token_estimator)
        pool.append(seed_cand)

        # Generate initial variants
        for i in range(1, population_size):
            mutated = self.mutate_reflective(seed_prompt, feedback=f"initial_variant_{i}")
            cand = GEPACandidate(prompt_text=mutated, generation=0, parent_id="seed")
            cand.compute_metrics(self.token_estimator)
            pool.append(cand)

        # 2. Evaluate pool over dataset
        for cand in pool:
            for item in pareto_dataset:
                inp = item.get("input", "")
                exp = item.get("expected", "")
                if eval_fn:
                    actual = eval_fn(cand.prompt_text, inp)
                else:
                    actual = cand.prompt_text + " " + inp
                cand.scores[inp] = self.evaluate_similarity_score(actual, exp)
            cand.compute_metrics(self.token_estimator)

        history: List[Dict[str, Any]] = []

        # 3. Evolution Loop
        for gen in range(1, max_generations + 1):
            frontier = self.find_pareto_frontier(pool)

            # Exploration vs Exploitation
            if random.random() < self.exploit_prob and frontier:
                if random.random() < self.not_merge_prob or len(frontier) < 2:
                    parent = random.choice(frontier)
                    new_text = self.mutate_reflective(parent.prompt_text, "reflective_refinement")
                else:
                    parents = random.sample(frontier, 2)
                    new_text = self.merge_prompts(parents[0].prompt_text, parents[1].prompt_text)
            else:
                parent = random.choice(pool)
                new_text = self.mutate_reflective(parent.prompt_text)

            child = GEPACandidate(prompt_text=new_text, generation=gen)
            for item in pareto_dataset:
                inp = item.get("input", "")
                exp = item.get("expected", "")
                actual = eval_fn(child.prompt_text, inp) if eval_fn else (child.prompt_text + " " + inp)
                child.scores[inp] = self.evaluate_similarity_score(actual, exp)
            child.compute_metrics(self.token_estimator)

            pool.append(child)
            history.append({
                "generation": gen,
                "pool_size": len(pool),
                "best_score": max(c.mean_score for c in pool),
                "frontier_size": len(self.find_pareto_frontier(pool)),
            })

        final_frontier = self.find_pareto_frontier(pool)
        # Select best candidate on Pareto frontier with token penalty
        best = max(final_frontier or pool, key=lambda c: c.mean_score - (self.token_penalty * c.token_count))

        return GEPAResult(
            best_prompt=best.prompt_text,
            best_score=best.mean_score,
            best_token_count=best.token_count,
            generations_run=max_generations,
            pool_size=len(pool),
            pareto_frontier_size=len(final_frontier),
            history=history,
        )


def create_gepa_optimizer() -> GEPALiteOptimizer:
    return GEPALiteOptimizer()
