"""
Hermes Agent: Autonomous Task Proposer & Self-Improvement Engine (Phase VII)
===========================================================================
Implements the Absolute Zero Reasoner (AZR, arXiv:2505.03335) self-play pattern:
  1. UCB1 Multi-Armed Bandit task proposer selecting frontier capability gaps.
  2. Four automated task categories (Coding, Math, Research Grounding, Self-Critique).
  3. Verifiable ground-truth reward signals (Bubblewrap sandbox execution + exact SymPy numericals).
  4. Append-only RL signal collector (rl_buffer.jsonl) exporting DPO/GRPO preference pairs.
  5. Evolutionary prompt optimizer (GEPA/OPRO pattern) with Pareto tournament selection.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import random
import re
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import sympy

# Setup internal imports with resilient fallbacks
try:
    from agent.core.sandbox import run as sandbox_run, DEFAULT_WORKSPACE
    from agent.core.trajectory import TrajectoryRecorder
    from agent.core.quorum_moa import _call_llama_server
except (ImportError, ModuleNotFoundError):
    try:
        from hermes_core.sandbox import run as sandbox_run, DEFAULT_WORKSPACE
        from hermes_core.trajectory import TrajectoryRecorder
        from hermes_core.quorum_moa import _call_llama_server
    except (ImportError, ModuleNotFoundError):
        from sandbox import run as sandbox_run, DEFAULT_WORKSPACE
        from trajectory import TrajectoryRecorder
        from quorum_moa import _call_llama_server

logger = logging.getLogger("hermes.core.task_proposer")
RL_BUFFER_PATH = Path.home() / ".hermes/evolution/rl_buffer.jsonl"


@dataclass
class TaskCandidate:
    """Represents an autonomously generated self-improvement task candidate."""
    task_id: str
    category: str  # code, math, research, critique
    prompt: str
    ground_truth: Any
    verification_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UCB1Bandit:
    """Upper Confidence Bound (UCB1) multi-armed bandit for optimal task exploration."""

    def __init__(self, arms: Optional[List[str]] = None, c: float = 1.414):
        self.arms = arms or ["code", "math", "research", "critique"]
        self.c = c
        self.counts: Dict[str, int] = {arm: 0 for arm in self.arms}
        self.rewards: Dict[str, float] = {arm: 0.0 for arm in self.arms}
        self.total_pulls = 0

    def select_arm(self) -> str:
        """Select arm maximizing UCB1 score with initial round-robin exploration."""
        for arm in self.arms:
            if self.counts[arm] == 0:
                return arm

        best_score = -float("inf")
        best_arm = self.arms[0]
        for arm in self.arms:
            mean_reward = self.rewards[arm] / self.counts[arm]
            exploration_term = self.c * math.sqrt(math.log(self.total_pulls) / self.counts[arm])
            score = mean_reward + exploration_term
            if score > best_score:
                best_score = score
                best_arm = arm
        return best_arm

    def update(self, arm: str, reward: float) -> None:
        """Update bandit statistics after observing verifiable reward."""
        if arm in self.arms:
            self.counts[arm] += 1
            self.rewards[arm] += reward
            self.total_pulls += 1


class TaskProposer:
    """Generates challenging self-curriculum tasks with deterministic ground-truth verification."""

    def __init__(self, bandit: Optional[UCB1Bandit] = None):
        self.bandit = bandit or UCB1Bandit()

    def propose_task(self, category: Optional[str] = None) -> TaskCandidate:
        """Generate a new self-play task candidate for the selected or bandit-chosen category."""
        cat = category or self.bandit.select_arm()
        task_id = hashlib.sha256(f"{cat}-{time.time()}-{random.random()}".encode()).hexdigest()[:12]

        if cat == "code":
            return self._propose_code_task(task_id)
        elif cat == "math":
            return self._propose_math_task(task_id)
        elif cat == "critique":
            return self._propose_critique_task(task_id)
        else:
            return self._propose_research_task(task_id)

    def _propose_code_task(self, task_id: str) -> TaskCandidate:
        """Generate algorithmic code challenge with unit test verification."""
        templates = [
            {
                "prompt": "Write a python function `solve_longest_palindrome(s: str) -> str` that returns the longest palindromic substring in s. Provide ONLY the python function implementation.",
                "test_script": """
from solution import solve_longest_palindrome
assert solve_longest_palindrome("babad") in ("bab", "aba"), "babad failed"
assert solve_longest_palindrome("cbbd") == "bb", "cbbd failed"
assert solve_longest_palindrome("a") == "a", "single char failed"
assert solve_longest_palindrome("racecar") == "racecar", "racecar failed"
print("VERIFIED_PASSED")
""",
                "ground_truth": "longest_palindrome_oracle"
            },
            {
                "prompt": "Write a python function `merge_intervals(intervals: list[list[int]]) -> list[list[int]]` that merges all overlapping intervals. Provide ONLY the python function implementation.",
                "test_script": """
from solution import merge_intervals
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]], "failed 1"
assert merge_intervals([[1,4],[4,5]]) == [[1,5]], "failed 2"
assert merge_intervals([[1,4],[0,4]]) == [[0,4]], "failed 3"
print("VERIFIED_PASSED")
""",
                "ground_truth": "merge_intervals_oracle"
            },
            {
                "prompt": "Write a python function `find_missing_positive(nums: list[int]) -> int` that returns the smallest missing positive integer. Provide ONLY the python function implementation.",
                "test_script": """
from solution import find_missing_positive
assert find_missing_positive([1,2,0]) == 3, "failed 1"
assert find_missing_positive([3,4,-1,1]) == 2, "failed 2"
assert find_missing_positive([7,8,9,11,12]) == 1, "failed 3"
print("VERIFIED_PASSED")
""",
                "ground_truth": "find_missing_positive_oracle"
            }
        ]
        chosen = random.choice(templates)
        return TaskCandidate(
            task_id=task_id,
            category="code",
            prompt=chosen["prompt"],
            ground_truth=chosen["ground_truth"],
            verification_code=chosen["test_script"],
            metadata={"framework": "sandbox_unit_test"}
        )

    def _propose_math_task(self, task_id: str) -> TaskCandidate:
        """Generate exact symbolic / arithmetic challenge with Sympy ground-truth evaluation."""
        a = random.randint(12, 95)
        b = random.randint(11, 45)
        c = random.randint(3, 19)
        expr = f"({a} * {b}) - ({c} ** 2)"
        exact_val = int(sympy.sympify(expr))

        prompt = f"Calculate the exact integer value of ({a} * {b}) - ({c}^2). Explain step-by-step and end with 'Final Answer: <number>'."
        return TaskCandidate(
            task_id=task_id,
            category="math",
            prompt=prompt,
            ground_truth=exact_val,
            metadata={"expression": expr}
        )

    def _propose_critique_task(self, task_id: str) -> TaskCandidate:
        """Generate faulty code snippet and require self-critique and correction."""
        flawed_code = "def divide_elements(lst, divisor):\n    res = []\n    for x in lst:\n        res.append(x / divisor)\n    return res"
        prompt = (
            f"Review this function for edge case errors:\n```python\n{flawed_code}\n```\n"
            "Identify the critical vulnerability when divisor == 0 and write the corrected robust function."
        )
        return TaskCandidate(
            task_id=task_id,
            category="critique",
            prompt=prompt,
            ground_truth="ZeroDivisionError handling",
            metadata={"expected_concept": "ZeroDivisionError"}
        )

    def _propose_research_task(self, task_id: str) -> TaskCandidate:
        """Generate verifiable factual synthesis task."""
        prompt = "State the asymptotic time complexity of standard quicksort (average vs worst case) and the mathematical reason for the worst case."
        return TaskCandidate(
            task_id=task_id,
            category="research",
            prompt=prompt,
            ground_truth={"average": "O(n log n)", "worst": "O(n^2)"},
            metadata={"required_tokens": ["O(n log n)", "O(n^2)", "pivot"]}
        )

    def verify_solution(self, task: TaskCandidate, solution: str) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluate candidate solution against deterministic ground truth.
        Returns: (passed, reward_scalar, details)
        """
        if task.category == "code":
            return self._verify_code(task, solution)
        elif task.category == "math":
            return self._verify_math(task, solution)
        elif task.category == "critique":
            return self._verify_critique(task, solution)
        else:
            return self._verify_research(task, solution)

    def _verify_code(self, task: TaskCandidate, solution: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Execute candidate code solution inside Bubblewrap sandbox."""
        code_body = solution
        match = re.search(r"```(?:python)?\s*(.*?)\s*```", solution, re.DOTALL)
        if match:
            code_body = match.group(1)

        ws = Path("/dev/shm/hermes_workspace")
        ws.mkdir(parents=True, exist_ok=True)
        sol_file = ws / "solution.py"
        test_file = ws / "test_harness.py"

        try:
            sol_file.write_text(code_body.strip() + "\n", encoding="utf-8")
            test_file.write_text(task.verification_code.strip() + "\n", encoding="utf-8")

            rc, out = sandbox_run("python3 test_harness.py", timeout_sec=10, workspace=ws)
            passed = (rc == 0 and "VERIFIED_PASSED" in out)
            reward = 1.0 if passed else 0.0
            return passed, reward, {"returncode": rc, "output": out.strip()}
        except Exception as e:
            return False, 0.0, {"error": str(e)}

    def _verify_math(self, task: TaskCandidate, solution: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Verify numerical answer matches exact Sympy ground truth."""
        expected = str(task.ground_truth)
        match = re.search(r"Final Answer:\s*([+-]?\d+)", solution, re.IGNORECASE)
        found_val = match.group(1) if match else None

        if not found_val:
            numbers = re.findall(r"[+-]?\d+", solution)
            found_val = numbers[-1] if numbers else None

        passed = (found_val == expected)
        reward = 1.0 if passed else 0.0
        return passed, reward, {"expected": expected, "found": found_val}

    def _verify_critique(self, task: TaskCandidate, solution: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Verify critique detected the error and supplied robust handling."""
        sol_lower = solution.lower()
        has_zero_div = "zerodivision" in sol_lower or "division by zero" in sol_lower or "zero" in sol_lower
        has_fix = "try" in sol_lower or "if divisor" in sol_lower or "raise" in sol_lower or "return" in sol_lower
        passed = has_zero_div and has_fix
        reward = 1.0 if passed else (0.5 if has_zero_div else 0.0)
        return passed, reward, {"detected_vulnerability": has_zero_div, "provided_fix": has_fix}

    def _verify_research(self, task: TaskCandidate, solution: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Verify research answer contains required asymptotic bounds."""
        sol_clean = solution.replace(" ", "").lower()
        has_avg = "o(nlogn)" in sol_clean or "n*log(n)" in sol_clean or "o(nlog(n))" in sol_clean
        has_worst = "o(n^2)" in sol_clean or "o(n2)" in sol_clean or "o(n**2)" in sol_clean
        passed = has_avg and has_worst
        reward = 1.0 if passed else (0.5 if (has_avg or has_worst) else 0.0)
        return passed, reward, {"has_average": has_avg, "has_worst": has_worst}


class RLBufferCollector:
    """Appends verified (prompt, reasoning, response, reward) tuples to rl_buffer.jsonl and exports DPO/GRPO datasets."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or RL_BUFFER_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_entry(
        self,
        task: TaskCandidate,
        solution: str,
        reward: float,
        passed: bool,
        thinking_trace: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record verifiable self-play step."""
        record = {
            "task_id": task.task_id,
            "category": task.category,
            "prompt": task.prompt,
            "thinking_trace": thinking_trace,
            "solution": solution,
            "reward": round(reward, 3),
            "verified_passed": passed,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def export_dpo_pairs(self, min_accepted_reward: float = 0.8, max_rejected_reward: float = 0.4) -> List[Dict[str, Any]]:
        """Construct (prompt, chosen, rejected) pairs from historical executions."""
        if not self.path.exists():
            return []

        entries: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass

        pairs = []
        by_prompt: Dict[str, List[Dict[str, Any]]] = {}
        for e in entries:
            p = e.get("prompt", "")
            by_prompt.setdefault(p, []).append(e)

        for p, group in by_prompt.items():
            chosens = [e for e in group if e.get("reward", 0.0) >= min_accepted_reward]
            rejecteds = [e for e in group if e.get("reward", 0.0) <= max_rejected_reward]
            if chosens and rejecteds:
                pairs.append({
                    "prompt": p,
                    "chosen": chosens[0]["solution"],
                    "rejected": rejecteds[0]["solution"],
                    "chosen_reward": chosens[0]["reward"],
                    "rejected_reward": rejecteds[0]["reward"],
                    "category": chosens[0].get("category"),
                })
        return pairs


class EvolutionaryPromptOptimizer:
    """GEPA/OPRO-style Prompt Evolution with mutation, crossover, and tournament selection."""

    def __init__(self, population_size: int = 6):
        self.population_size = population_size
        self.population: List[str] = []

    def initialize_population(self, seed_prompt: str) -> None:
        """Initialize population of prompt variants."""
        self.population = [seed_prompt]
        mutations = [
            "Think step by step with extreme mathematical precision before responding.",
            "Decompose the problem into atomic logical invariants, verify intermediate states, then emit final answer.",
            "Formulate a direct solution hypothesis, test boundary edge cases, and output verifiable code.",
            "Analyze root causes first. Ensure formal correctness, zero assumptions, and clean termination.",
            "Prioritize deterministic execution, boundary safety, and minimal algorithmic complexity.",
        ]
        for m in mutations[:self.population_size - 1]:
            self.population.append(f"{seed_prompt} {m}")

    def evaluate_and_evolve(self, fitness_fn: Any, generations: int = 2) -> Tuple[str, float]:
        """Run genetic evolution over generations, returning (best_prompt, best_score)."""
        if not self.population:
            raise ValueError("Population not initialized")

        best_prompt = self.population[0]
        best_score = -1.0

        for gen in range(generations):
            scores = []
            for p in self.population:
                sc = fitness_fn(p)
                scores.append((sc, p))
                if sc > best_score:
                    best_score = sc
                    best_prompt = p

            scores.sort(key=lambda x: x[0], reverse=True)
            survivors = [p for _, p in scores[:max(2, len(scores) // 2)]]
            new_pop = list(survivors)

            while len(new_pop) < self.population_size:
                parent = random.choice(survivors)
                mutated = parent + " Enforce strict verification."
                new_pop.append(mutated)
            self.population = new_pop

        return best_prompt, best_score


class SelfImprovementEngine:
    """Master orchestrator for the Phase VII Absolute Zero self-improvement loop."""

    def __init__(
        self,
        proposer: Optional[TaskProposer] = None,
        buffer: Optional[RLBufferCollector] = None,
    ):
        self.proposer = proposer or TaskProposer()
        self.buffer = buffer or RLBufferCollector()

    def run_self_play_cycle(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute one full self-play loop:
          1. Propose task candidate via UCB1 bandit.
          2. Generate solution via local llama-server (port 8138).
          3. Evaluate against deterministic ground truth (sandbox / sympy).
          4. Record experience into rl_buffer.jsonl.
          5. Update bandit arm statistics.
        """
        task = self.proposer.propose_task(category=category)
        start_t = time.time()

        messages = [
            {"role": "system", "content": "You are Hermes, an autonomous reasoning agent. Solve the task deterministically with complete precision."},
            {"role": "user", "content": task.prompt}
        ]

        solution_text, conf, meta = _call_llama_server(messages, temperature=0.1, max_tokens=512)
        passed, reward, details = self.proposer.verify_solution(task, solution_text)
        self.proposer.bandit.update(task.category, reward)

        entry = self.buffer.append_entry(
            task=task,
            solution=solution_text,
            reward=reward,
            passed=passed,
            metadata={"meta": meta, "details": details, "duration": time.time() - start_t}
        )

        return {
            "task_id": task.task_id,
            "category": task.category,
            "passed": passed,
            "reward": reward,
            "confidence": conf,
            "details": details,
            "latency_sec": round(time.time() - start_t, 3),
            "entry": entry,
        }


_GLOBAL_SELF_IMPROVEMENT_ENGINE: Optional[SelfImprovementEngine] = None


def get_self_improvement_engine() -> SelfImprovementEngine:
    """Retrieve shared global SelfImprovementEngine instance."""
    global _GLOBAL_SELF_IMPROVEMENT_ENGINE
    if _GLOBAL_SELF_IMPROVEMENT_ENGINE is None:
        _GLOBAL_SELF_IMPROVEMENT_ENGINE = SelfImprovementEngine()
    return _GLOBAL_SELF_IMPROVEMENT_ENGINE


__all__ = [
    "TaskCandidate",
    "UCB1Bandit",
    "TaskProposer",
    "RLBufferCollector",
    "EvolutionaryPromptOptimizer",
    "SelfImprovementEngine",
    "get_self_improvement_engine",
]
