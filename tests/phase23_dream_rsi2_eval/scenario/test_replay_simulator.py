"""Unit tests for Dream-RSI 2.0 Replay Simulator Pool."""

import hashlib
import json
import math

import pytest
from replay_simulator import (
    DoublyRobustEvaluator,
    DreamRSISimulatorPool,
    ReplayTree,
    RRSIStabilityGate,
    StateTransition,
)


@pytest.fixture
def sample_transitions():
    return [
        StateTransition(
            step=0,
            state_desc="AST root inspection",
            action="ast_grep_outline",
            reward=0.8,
            next_state="outline_ready",
            baseline_prob=0.6,
            q_estimate=0.75,
        ),
        StateTransition(
            step=1,
            state_desc="Surgical code edit",
            action="apply_surgical_diff",
            reward=0.9,
            next_state="diff_applied",
            baseline_prob=0.5,
            q_estimate=0.85,
        ),
        StateTransition(
            step=2,
            state_desc="Compiler gate",
            action="run_pytest_gate",
            reward=1.0,
            next_state="tests_passed",
            baseline_prob=0.7,
            q_estimate=0.95,
        ),
        StateTransition(
            step=3,
            state_desc="Distill rule",
            action="distill_learned_rule",
            reward=0.85,
            next_state="rule_persisted",
            baseline_prob=0.4,
            q_estimate=0.8,
        ),
    ]


@pytest.fixture
def sample_replay_tree(sample_transitions):
    content = json.dumps([t.action for t in sample_transitions])
    root_hash = hashlib.sha256(content.encode()).hexdigest()
    return ReplayTree(
        session_id="session_test_42",
        task_goal="Repair concurrency lock deadlock",
        root_hash=root_hash,
        transitions=sample_transitions,
        metadata={"phase": 23, "testbed": "dream_rsi2"},
    )


def test_replay_tree_serialization_and_hash(sample_replay_tree, tmp_path):
    """Asserts that replay trees serialize, content-address, and deserialize without loss."""
    raw_json = sample_replay_tree.to_json()
    reloaded = ReplayTree.from_json(raw_json)

    assert reloaded.session_id == sample_replay_tree.session_id
    assert reloaded.root_hash == sample_replay_tree.root_hash
    assert len(reloaded.transitions) == 4
    assert reloaded.transitions[1].action == "apply_surgical_diff"

    # Test file persistence
    pool = DreamRSISimulatorPool(cache_dir=str(tmp_path / "dream_worlds"))
    persisted_path = pool.persist_tree(sample_replay_tree)
    assert persisted_path.exists()
    assert persisted_path.name == f"{sample_replay_tree.root_hash}.json"


def test_doubly_robust_value_estimation(sample_transitions):
    """Asserts Doubly Robust estimator scores high-reward policies higher."""
    evaluator = DoublyRobustEvaluator(gamma=0.95)

    # Superior candidate policy: increases likelihood of optimal actions
    improved_policy = {
        "ast_grep_outline": 0.9,
        "apply_surgical_diff": 0.9,
        "run_pytest_gate": 0.95,
        "distill_learned_rule": 0.8,
    }
    # Inferior candidate policy: shifts probability to sub-optimal steps
    degraded_policy = {
        "ast_grep_outline": 0.1,
        "apply_surgical_diff": 0.1,
        "run_pytest_gate": 0.1,
        "distill_learned_rule": 0.1,
    }

    v_high = evaluator.evaluate(sample_transitions, improved_policy)
    v_low = evaluator.evaluate(sample_transitions, degraded_policy)

    assert v_high > v_low, f"Expected v_high ({v_high}) > v_low ({v_low})"


def test_importance_weight_clipping(sample_transitions):
    """Asserts that extreme importance ratios are bounded by max_importance_weight."""
    evaluator = DoublyRobustEvaluator(gamma=0.95, max_importance_weight=5.0)

    # Extreme discrepancy: pi=1.0 vs mu=0.001 -> ratio would be 1000 without clipping
    skewed_policy = {"ast_grep_outline": 1.0}
    val = evaluator.evaluate(sample_transitions, skewed_policy)

    # Should compute without math overflow or NaN
    assert not math.isnan(val)
    assert not math.isinf(val)
    assert val > 0.0


def test_rrsi_stability_gate_pass():
    """Asserts that statistically significant performance lift passes RRSI gate."""
    gate = RRSIStabilityGate(confidence_k=1.645)

    # Stable baseline rewards: low variance (sigma_0 ~ 0.08)
    baseline_rewards = [0.85, 0.90, 0.88, 0.82, 0.95, 0.87]
    v_baseline = 2.5
    v_candidate = 3.2  # Delta = 0.7 >> 1.645 * 0.08 ~ 0.13

    passed, lift, margin = gate.check_stability(v_candidate, v_baseline, baseline_rewards)

    assert passed is True
    assert lift > margin
    assert lift == pytest.approx(0.7, 0.01)


def test_rrsi_stability_gate_rejection():
    """Asserts that spurious mutations within noise margin are rejected."""
    gate = RRSIStabilityGate(confidence_k=1.645)

    # High-variance baseline: sigma_0 ~ 0.35
    baseline_rewards = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7]
    v_baseline = 2.0
    v_noisy_candidate = 2.1  # Delta = 0.1 < 1.645 * 0.35 ~ 0.57

    passed, lift, margin = gate.check_stability(v_noisy_candidate, v_baseline, baseline_rewards)

    assert passed is False
    assert lift < margin


def test_call_reduction_ratio_and_latency(sample_replay_tree, tmp_path):
    """Asserts counterfactual evaluation achieves >= 2.0x call reduction in <= 50.0 ms."""
    pool = DreamRSISimulatorPool(cache_dir=str(tmp_path / "dream_worlds"))

    candidate_policy = {
        "ast_grep_outline": 0.85,
        "apply_surgical_diff": 0.90,
        "run_pytest_gate": 0.95,
        "distill_learned_rule": 0.80,
    }

    result = pool.evaluate_counterfactual_candidate(sample_replay_tree, candidate_policy)

    assert result["call_reduction_ratio"] >= 2.0, (
        f"Call reduction ratio must be >= 2.0, got {result['call_reduction_ratio']}"
    )
    assert result["dream_eval_latency_ms"] <= 50.0, (
        f"Evaluation latency must be <= 50.0 ms, got {result['dream_eval_latency_ms']} ms"
    )
    assert result["rrsi_stability_gate_passed"] is True
