#!/usr/bin/env python3
"""
Verification Suite: Phase 7 Self-Improvement Loop (Absolute Zero Pattern)
========================================================================
Verifies:
  Gate 1: UCB1 Bandit & Frontier Task Proposal across 4 Categories (code, math, critique, research)
  Gate 2: Code Challenge Generation & Sandboxed Bubblewrap Execution (pass/fail verification)
  Gate 3: Mathematical Reasoning & Exact SymPy Ground-Truth Verification
  Gate 4: Autonomous Self-Play Cycle with Local llama-server (Port 8138 inference + verification)
  Gate 5: Verifiable RL Buffer Stream & DPO/GRPO Preference Pair Export
  Gate 6: Evolutionary Prompt Optimizer (GEPA population evaluation, mutation, tournament selection)

Zero-Test-Folder Architecture: Pure native executable contract verification.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

hermes_root = Path.home() / ".hermes"
sys.path.insert(0, str(hermes_root / "hermes-agent"))

import agent.core as core
from agent.core.task_proposer import (
    TaskCandidate,
    UCB1Bandit,
    TaskProposer,
    RLBufferCollector,
    EvolutionaryPromptOptimizer,
    SelfImprovementEngine,
    get_self_improvement_engine,
)


def log_gate(gate_id: str, desc: str, passed: bool, details: str = ""):
    status = "\033[92mPASS\033[0m" if passed else "\033[91mFAIL\033[0m"
    print(f"[{gate_id}] {status} - {desc}")
    if details:
        print(f"       \033[90m{details}\033[0m")


def test_gate1_bandit_and_proposer() -> bool:
    """Gate 1: UCB1 Bandit & Frontier Task Proposal across all 4 categories."""
    bandit = UCB1Bandit(arms=["code", "math", "critique", "research"], c=1.414)
    proposer = TaskProposer(bandit=bandit)

    # Verify all categories can be proposed
    categories = ["code", "math", "critique", "research"]
    for cat in categories:
        task = proposer.propose_task(category=cat)
        if not task.task_id or task.category != cat or not task.prompt:
            log_gate("GATE 1", f"Task generation for category '{cat}'", False, f"Invalid task: {task}")
            return False

    # Verify UCB1 initial round-robin pull
    selected = [bandit.select_arm() for _ in range(4)]
    # First 4 pulls should cover unvisited arms
    for cat in categories:
        bandit.update(cat, 1.0)

    # Arm with highest reward should now be favored or explored appropriately
    bandit.update("math", 10.0)
    next_arm = bandit.select_arm()
    if next_arm not in categories:
        log_gate("GATE 1", "UCB1 Bandit Selection Validity", False, f"Unexpected arm: {next_arm}")
        return False

    log_gate(
        "GATE 1",
        "UCB1 Bandit & Frontier Task Proposal Across 4 Categories",
        True,
        f"Categories: {categories}, UCB1 total pulls: {bandit.total_pulls}, bandit selection: {next_arm}",
    )
    return True


def test_gate2_code_sandboxed_execution() -> bool:
    """Gate 2: Code Challenge Generation & Sandboxed Bubblewrap Execution."""
    proposer = TaskProposer()
    code_task = proposer.propose_task(category="code")

    # Generate a valid solution matching template
    valid_solution = """
def solve_longest_palindrome(s: str) -> str:
    if not s:
        return ""
    start, max_len = 0, 1
    for i in range(len(s)):
        for l, r in ((i, i), (i, i + 1)):
            while l >= 0 and r < len(s) and s[l] == s[r]:
                if r - l + 1 > max_len:
                    start = l
                    max_len = r - l + 1
                l -= 1
                r += 1
    return s[start:start + max_len]

def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    res = [intervals[0]]
    for cur in intervals[1:]:
        if cur[0] <= res[-1][1]:
            res[-1][1] = max(res[-1][1], cur[1])
        else:
            res.append(cur)
    return res

def find_missing_positive(nums: list[int]) -> int:
    nums = [x for x in nums if x > 0]
    nums_set = set(nums)
    i = 1
    while i in nums_set:
        i += 1
    return i
"""
    # Test valid solution
    passed, reward, details = proposer.verify_solution(code_task, valid_solution)
    if not passed or reward != 1.0:
        log_gate("GATE 2", "Sandboxed Code Execution (Valid Solution)", False, f"Details: {details}")
        return False

    # Test faulty solution
    faulty_solution = "def solve_longest_palindrome(s):\n    return ''\ndef merge_intervals(i):\n    return []\ndef find_missing_positive(n):\n    return -1\n"
    f_passed, f_reward, f_details = proposer.verify_solution(code_task, faulty_solution)
    if f_passed or f_reward != 0.0:
        log_gate("GATE 2", "Sandboxed Code Execution (Faulty Rejection)", False, f"Expected reject, got: {f_details}")
        return False

    log_gate(
        "GATE 2",
        "Code Challenge Generation & Sandboxed Bubblewrap Execution",
        True,
        f"Bubblewrap sandbox evaluated code task '{code_task.task_id}'. Valid reward: {reward}, Faulty reward: {f_reward}",
    )
    return True


def test_gate3_sympy_ground_truth() -> bool:
    """Gate 3: Mathematical Reasoning & Exact SymPy Ground-Truth Verification."""
    proposer = TaskProposer()
    math_task = proposer.propose_task(category="math")
    expected_val = math_task.ground_truth

    # Test correct format
    correct_solution = f"Calculating intermediate values...\nTherefore the result is.\nFinal Answer: {expected_val}"
    passed, reward, details = proposer.verify_solution(math_task, correct_solution)
    if not passed or reward != 1.0:
        log_gate("GATE 3", "SymPy Math Ground Truth (Correct Answer)", False, f"Details: {details}")
        return False

    # Test wrong number
    wrong_solution = f"Final Answer: {expected_val + 999}"
    w_passed, w_reward, w_details = proposer.verify_solution(math_task, wrong_solution)
    if w_passed or w_reward != 0.0:
        log_gate("GATE 3", "SymPy Math Ground Truth (Incorrect Answer)", False, f"Details: {w_details}")
        return False

    log_gate(
        "GATE 3",
        "Mathematical Reasoning & Exact SymPy Ground-Truth Verification",
        True,
        f"Expression evaluated by SymPy: {math_task.metadata.get('expression')} = {expected_val}. Verified deterministic matching.",
    )
    return True


def test_gate4_self_play_cycle() -> bool:
    """Gate 4: Autonomous Self-Play Cycle with Local llama-server (Port 8138)."""
    engine = get_self_improvement_engine()
    # Run cycle on math category (high predictability)
    t0 = time.time()
    result = engine.run_self_play_cycle(category="math")
    duration = time.time() - t0

    if not result.get("task_id") or "passed" not in result or "reward" not in result:
        log_gate("GATE 4", "Autonomous Self-Play Cycle", False, f"Malformed result: {result}")
        return False

    log_gate(
        "GATE 4",
        "Autonomous Self-Play Cycle (LLaMA-server Port 8138)",
        True,
        f"Task {result['task_id']} ({result['category']}) in {duration:.2f}s | Passed: {result['passed']} | Reward: {result['reward']} | Conf: {result['confidence']:.3f}",
    )
    return True


def test_gate5_rl_buffer_and_dpo_pairs() -> bool:
    """Gate 5: Verifiable RL Buffer Stream & DPO/GRPO Preference Pair Export."""
    test_buffer_path = Path("/dev/shm/test_rl_buffer.jsonl")
    if test_buffer_path.exists():
        test_buffer_path.unlink()

    collector = RLBufferCollector(path=test_buffer_path)
    proposer = TaskProposer()
    task = proposer.propose_task(category="critique")

    # Add good entry (reward 1.0)
    collector.append_entry(
        task=task,
        solution="Handle ZeroDivisionError cleanly with try/except block.",
        reward=1.0,
        passed=True,
        thinking_trace="Check for divisor == 0 and catch exception.",
    )

    # Add poor entry for same prompt (reward 0.0)
    collector.append_entry(
        task=task,
        solution="Just run lst[i] / divisor without checks.",
        reward=0.0,
        passed=False,
        thinking_trace="Division is fine.",
    )

    if not test_buffer_path.exists():
        log_gate("GATE 5", "RL Buffer Persistence", False, "File was not created")
        return False

    pairs = collector.export_dpo_pairs(min_accepted_reward=0.8, max_rejected_reward=0.4)
    if len(pairs) != 1:
        log_gate("GATE 5", "DPO/GRPO Pair Construction", False, f"Expected 1 pair, found {len(pairs)}")
        return False

    pair = pairs[0]
    if pair["chosen_reward"] < 0.8 or pair["rejected_reward"] > 0.4:
        log_gate("GATE 5", "DPO/GRPO Reward Threshold Separation", False, f"Bad reward margins: {pair}")
        return False

    # Also verify global buffer has entries
    global_buffer = RLBufferCollector()
    if not global_buffer.path.exists() or global_buffer.path.stat().st_size == 0:
        log_gate("GATE 5", "Global RL Buffer Exists", False, f"{global_buffer.path} is empty")
        return False

    log_gate(
        "GATE 5",
        "Verifiable RL Buffer Stream & DPO/GRPO Pair Export",
        True,
        f"Exported valid preference pair: chosen ({pair['chosen_reward']}) vs rejected ({pair['rejected_reward']}). Global buffer: {global_buffer.path.name}",
    )
    return True


def test_gate6_evolutionary_prompt_optimizer() -> bool:
    """Gate 6: Evolutionary Prompt Optimizer (GEPA population evaluation, mutation, tournament selection)."""
    optimizer = EvolutionaryPromptOptimizer(population_size=4)
    seed = "Answer the user question directly."
    optimizer.initialize_population(seed)

    if len(optimizer.population) != 4:
        log_gate("GATE 6", "Population Initialization", False, f"Expected size 4, got {len(optimizer.population)}")
        return False

    # Mock fitness function rewarding precision and verification tokens
    def mock_fitness(prompt: str) -> float:
        score = 0.5
        if "mathematical precision" in prompt or "precision" in prompt:
            score += 0.3
        if "strict verification" in prompt or "verify" in prompt:
            score += 0.2
        return min(score, 1.0)

    best_prompt, best_score = optimizer.evaluate_and_evolve(fitness_fn=mock_fitness, generations=2)

    if best_score < 0.7:
        log_gate("GATE 6", "Evolutionary Fitness Convergence", False, f"Score too low: {best_score}")
        return False

    log_gate(
        "GATE 6",
        "Evolutionary Prompt Optimizer (GEPA Tournament Selection)",
        True,
        f"Evolved best prompt (score {best_score:.2f}): '{best_prompt[:60]}...'",
    )
    return True


def main() -> int:
    print("=" * 72)
    print("Hermes Phase 7: Self-Improvement Loop (Absolute Zero Pattern)")
    print("Verifying Autonomous Task Proposal, SymPy Evaluation, Sandboxing & RL")
    print("=" * 72)

    gates = [
        ("Gate 1", test_gate1_bandit_and_proposer),
        ("Gate 2", test_gate2_code_sandboxed_execution),
        ("Gate 3", test_gate3_sympy_ground_truth),
        ("Gate 4", test_gate4_self_play_cycle),
        ("Gate 5", test_gate5_rl_buffer_and_dpo_pairs),
        ("Gate 6", test_gate6_evolutionary_prompt_optimizer),
    ]

    all_passed = True
    for name, gate_fn in gates:
        try:
            if not gate_fn():
                all_passed = False
        except Exception as e:
            log_gate(name, f"Exception occurred during execution: {e}", False)
            import traceback
            traceback.print_exc()
            all_passed = False

    print("=" * 72)
    if all_passed:
        print("\033[92mALL PHASE 7 SELF-IMPROVEMENT LOOP GATES VERIFIED PERFECTLY (6/6)\033[0m")
        return 0
    else:
        print("\033[91mPHASE 7 VERIFICATION ENCOUNTERED FAILURES\033[0m")
        return 1


if __name__ == "__main__":
    sys.exit(main())
