"""Machine verification gate for Phase 23 Dream-RSI 2.0 Replay Simulator Pool."""

import json
import os
import pathlib
import sys

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from replay_simulator import (
    DoublyRobustEvaluator,
    DreamRSISimulatorPool,
    ReplayTree,
    RRSIStabilityGate,
    StateTransition,
)


def test_dream_rsi2_metrics_and_gate():
    """Validates that dream_rsi2_metrics.json exists and satisfies Phase 23 invariants."""
    metrics_path = testbed_root / "dream_rsi2_metrics.json"
    assert metrics_path.exists(), f"Metrics file {metrics_path} must exist (run benchmark_dream_rsi2.py)"

    metrics = json.loads(metrics_path.read_text())

    # Invariant 1: 0 MiB CUDA VRAM Delta (CPU Replay Trees & Evaluation)
    assert metrics["cuda_vram_delta_mib"] == 0, (
        f"CUDA VRAM delta must be 0, got {metrics['cuda_vram_delta_mib']} MiB"
    )

    # Invariant 2: Call Reduction Ratio >= 2.0x
    assert metrics["call_reduction_ratio"] >= 2.0, (
        f"Call reduction ratio must be >= 2.0, got {metrics['call_reduction_ratio']}x"
    )

    # Invariant 3: RRSI Stability Gate Passed
    assert metrics["rrsi_stability_gate_passed"] is True, "RRSI stability gate must pass"

    # Invariant 4: Dream Evaluation Latency <= 50.0 ms
    assert metrics["dream_eval_latency_ms"] <= 50.0, (
        f"Dream evaluation latency must be <= 50.0 ms, got {metrics['dream_eval_latency_ms']} ms"
    )


def test_live_dream_rsi2_execution(tmp_path):
    """Live functional verification of Dream-RSI 2.0 simulator pool."""
    pool = DreamRSISimulatorPool(cache_dir=str(tmp_path / "dream_cache"))

    transitions = [
        StateTransition(0, "Init", "act_0", 0.9, "s1", 0.5, 0.8),
        StateTransition(1, "Step 1", "act_1", 1.0, "s2", 0.6, 0.9),
    ]
    tree = ReplayTree(
        session_id="test_live_eval",
        task_goal="Evaluate counterfactual branch",
        root_hash="abc123456789",
        transitions=transitions,
    )

    result = pool.evaluate_counterfactual_candidate(
        tree,
        candidate_policy={"act_0": 0.95, "act_1": 0.98},
    )

    assert result["call_reduction_ratio"] >= 2.0
    assert result["dream_eval_latency_ms"] <= 50.0
    assert result["rrsi_stability_gate_passed"] is True
