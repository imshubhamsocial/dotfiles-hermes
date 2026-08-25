"""
Contract Spike: Google Env-Harness Self-Evolution Engine (Capability U30)
=========================================================================
Tests trajectory metrics mining, execution policy bounding/clamping,
stochastic mutations, policy crossover, genetic evolution, and export.
"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.harness_evolution import (
    ExecutionPolicy,
    HarnessEvolutionEngine,
    TrajectoryMetrics,
    TrajectoryTelemetryMiner,
    create_harness_evolution_engine,
)


def test_execution_policy_bounding_and_json():
    # Test valid clamping of out-of-bounds parameters
    p_raw = ExecutionPolicy(
        max_retries_per_node=999,
        context_token_ceiling=10,
        enable_ast_gate=True,
        enable_lsp_diagnostics=True,
        enable_cpu_embeddings=True,
        dag_concurrency=100,
        timeout_sec=9999.0,
    )
    clamped = p_raw.clamp()
    assert clamped.max_retries_per_node <= 10
    assert clamped.context_token_ceiling >= 150
    assert clamped.dag_concurrency <= 8
    assert clamped.timeout_sec <= 300.0
    
    # Test dictionary roundtrip
    d = clamped.to_dict()
    reloaded = ExecutionPolicy.from_dict(d)
    assert reloaded == clamped


def test_trajectory_telemetry_miner():
    with tempfile.TemporaryDirectory() as td:
        tpath = Path(td) / "trajectory.jsonl"
        events = [
            {"event": "turn", "role": "coder", "prompt_tokens": 300},
            {"event": "gate", "gate_status": "PASS"},
            {"event": "tool_result", "result_ok": True},
            {"event": "turn", "role": "coder", "prompt_tokens": 400},
            {"event": "gate", "gate_status": "REJECT"},
            {"event": "tool_result", "result_ok": False},
        ]
        with open(tpath, "w") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")
                
        metrics = TrajectoryTelemetryMiner.extract_metrics(tpath)
        assert metrics.total_turns == 2
        assert metrics.total_tokens == 700
        assert metrics.passed_gates == 1
        assert metrics.rejected_gates == 1
        assert metrics.gate_pass_rate == 0.5
        assert metrics.tool_success_rate == 0.5


def test_genetic_evolution_loop_and_pareto():
    with tempfile.TemporaryDirectory() as td:
        tpath = Path(td) / "trajectory.jsonl"
        events = [
            {"event": "turn", "role": "coder", "prompt_tokens": 250},
            {"event": "gate", "gate_status": "PASS"},
            {"event": "tool_result", "result_ok": True},
        ]
        tpath.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        
        engine = create_harness_evolution_engine(historical_trajectories=[tpath], seed=42)
        initial_policy = ExecutionPolicy(enable_ast_gate=False, enable_lsp_diagnostics=False)
        
        results = engine.evolve(generations=4, population_size=6, initial_policy=initial_policy)
        assert len(results) == 6
        
        best_policy, best_score = results[0]
        # Genetic evolution should favor policies with AST gate & LSP enabled
        assert best_score > 0.0
        
        out_json = Path(td) / "optimized_policy.json"
        saved = engine.export_policy(best_policy, out_json)
        assert saved.exists()
        
        loaded = json.loads(saved.read_text())
        assert "max_retries_per_node" in loaded
        assert "context_token_ceiling" in loaded
