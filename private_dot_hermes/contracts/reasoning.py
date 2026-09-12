#!/usr/bin/env python3
"""
Native Phase 1 Reasoning Amplification Verification Script
==========================================================
Verifies Phase 1 System-2 Reasoning Layer end-to-end:
1. ThinkingBudgetManager 4-tier complexity classification
2. Thinking token budgeting (0 / 512 / 2048 / 8192)
3. Internal CoT Draft -> Critique -> Revise loop
4. Thinking token privacy invariant (zero leakage in final_answer)
5. Dyve ProcessVerifier (System-1 fast + System-2 deep)
6. CogVerifier integration with check_process_reasoning
7. COT RL Buffer recording in cot_rl_buffer.jsonl
"""

import os
import sys
import json
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path.home() / ".hermes/hermes-agent"))
sys.path.insert(0, str(Path.home() / ".hermes/hermes-agent/agent"))
sys.path.insert(0, str(Path.home() / ".hermes/hermes-agent/agent/core"))

from thinking_budget import (
    ThinkingBudgetManager,
    TaskComplexity,
    COTRLBufferCollector,
    get_thinking_budget_manager,
)
from process_verifier import (
    ProcessVerifier,
    System1FastChecker,
    System2DeepVerifier,
    get_process_verifier,
)
from agent import Agent
from cog_verifier import CogVerifier, VerificationChecks

def run_verification():
    print("=" * 70)
    print("PHASE 1: REASONING AMPLIFICATION (SYSTEM-2 LAYER) VERIFICATION")
    print("=" * 70)

    # 1. Test Complexity Classifier
    print("\n[Step 1] Verifying 4-Tier Complexity Classifier & Token Budgets...")
    tb_mgr = get_thinking_budget_manager()
    
    test_cases = [
        ("hi", TaskComplexity.TRIVIAL, 0),
        ("implement a python helper function to format timestamps", TaskComplexity.MODERATE, 512),
        ("solve for roots of polynomial equation 2x^2 - 8x + 6 = 0 and prove invariant", TaskComplexity.HARD, 2048),
        ("research autonomous agent cross-system architecture design and synthesize findings", TaskComplexity.RESEARCH, 8192),
    ]

    for prompt, expected_tier, expected_budget in test_cases:
        tier = tb_mgr.classifier.classify(prompt)
        budget = tb_mgr.get_budget(tier)
        status = "✅" if tier == expected_tier and budget == expected_budget else "❌"
        print(f"  {status} Prompt: '{prompt[:45]}...' -> Tier: {tier.name} (Budget: {budget} tokens, Expected: {expected_budget})")
        assert tier == expected_tier, f"Tier mismatch for '{prompt}': got {tier.name}, expected {expected_tier.name}"
        assert budget == expected_budget, f"Budget mismatch: got {budget}, expected {expected_budget}"

    # 2. Test Thinking Privacy Invariant
    print("\n[Step 2] Verifying Thinking Token Privacy Invariant...")
    leaky_text = "Here is the final answer: 42 <thought>This is secret reasoning that must not leak</thought> <thinking>another internal scratchpad</thinking>"
    filtered = tb_mgr.filter_thinking_tokens(leaky_text)
    assert "<thought>" not in filtered
    assert "<thinking>" not in filtered
    assert "secret reasoning" not in filtered
    assert filtered == "Here is the final answer: 42"
    print("  ✅ Thinking tokens successfully purged from output (zero user-visible leakage)")

    # 3. Test Full CoT Reasoning Cycle
    print("\n[Step 3] Verifying System-2 CoT Reasoning Cycle (Draft -> Critique -> Revise)...")
    buffer_collector = tb_mgr.buffer
    initial_count = buffer_collector.count_records()
    
    math_prompt = "Calculate the maximum area of a rectangle with perimeter 40 and prove optimality."
    trace = tb_mgr.reason(math_prompt)
    
    print(f"  • Complexity detected: {TaskComplexity(trace.complexity).name}")
    print(f"  • Allocated budget: {trace.budget_tokens} tokens")
    print(f"  • Actual thinking tokens: {trace.actual_thinking_tokens} tokens")
    print(f"  • CoT Steps generated: {len(trace.steps)}")
    for s in trace.steps:
        print(f"      - Round {s.step_number} [{s.phase.upper()}]: confidence={s.confidence:.2f}")
    print(f"  • Final Answer: {trace.final_answer[:80]}...")
    print(f"  • Verified: {trace.verified} (Confidence: {trace.confidence:.2f})")
    
    assert trace.complexity == TaskComplexity.HARD
    assert len(trace.steps) >= 3  # Draft, Critique, Revise
    assert trace.verified is True
    print("  ✅ System-2 CoT Reasoning Cycle Certified")

    # 4. Test COT RL Buffer Recording
    print("\n[Step 4] Verifying COT RL Buffer Recording...")
    final_count = buffer_collector.count_records()
    print(f"  • Initial records: {initial_count}")
    print(f"  • Final records: {final_count}")
    assert final_count > initial_count, "No record written to cot_rl_buffer.jsonl"
    
    with open(buffer_collector.buffer_path, "r", encoding="utf-8") as f:
        last_line = [line for line in f if line.strip()][-1]
        record = json.loads(last_line)
        print(f"  • Recorded JSONL: prompt='{record['prompt'][:40]}...', reward={record['reward']}, ts={record['ts']}")
        assert record["prompt"] == math_prompt
        assert record["reward"] == 1.0
    print("  ✅ COT RL Buffer JSONL format verified")

    # 5. Test Dyve Process Verifier
    print("\n[Step 5] Verifying Dyve Dynamic Process Verifier (System-1 + System-2)...")
    pv = get_process_verifier()
    
    # System-1 check on clean vs anomalous input
    s1_clean, s1_conf, s1_anom = System1FastChecker.check("Clean execution step with balanced code: def foo(): return 42")
    assert s1_clean is True and len(s1_anom) == 0
    
    s1_fail, _, s1_fail_anom = System1FastChecker.check("Unbalanced code { def foo(): ( missing right paren")
    assert s1_fail is False and len(s1_fail_anom) > 0
    print(f"  ✅ System-1 detected syntactic anomalies accurately: {s1_fail_anom}")

    # System-2 deep verification on reasoning
    rep = pv.verify_step(
        step_content="Therefore, by arithmetic-geometric mean inequality, the square of sides 10x10 yields maximum area 100. The result is optimal.",
        step_type="math"
    )
    assert rep.passed is True
    assert rep.system_mode == "system_2"
    print(f"  ✅ System-2 Deep Process Verification Certified: mode={rep.system_mode}, conf={rep.confidence:.2f}")

    # 6. Test CogVerifier Native Integration
    print("\n[Step 6] Verifying CogVerifier check_process_reasoning Integration...")
    check_res = VerificationChecks.check_process_reasoning(task_id="TASK-P1-REASONING", content="Execution reasoning verified with strict invariant.")
    print(f"  • Check Name: {check_res.name}")
    print(f"  • Check Status: {check_res.status}")
    print(f"  • Check Message: {check_res.message}")
    assert check_res.status == "PASS"
    print("  ✅ CogVerifier check_process_reasoning returned PASS")

    # 7. Test Agent Primitive Integration
    print("\n[Step 7] Verifying Agent Primitive System-2 Hook...")
    agent = Agent(name="HermesReasoningAgent", model="gemma-4-4b")
    res = agent.execute_reasoning("Solve quadratic equation x^2 - 4 = 0")
    assert "final_answer" in res
    assert res["actual_thinking_tokens"] > 0
    print(f"  • Agent execution output: '{res['final_answer'][:60]}...'")
    print(f"  • Thinking tokens utilized: {res['actual_thinking_tokens']}")
    print("  ✅ Agent primitive System-2 execution hook certified")

    print("\n" + "=" * 70)
    print("PHASE 1 VERIFICATION RESULT: 100% PASS (ALL GATES CERTIFIED)")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
