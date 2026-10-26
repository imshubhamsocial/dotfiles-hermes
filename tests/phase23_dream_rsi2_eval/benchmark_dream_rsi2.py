"""Benchmark runner for Phase 23 Dream-RSI 2.0 Open-World Replay Simulator Pool."""

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

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


def get_cuda_vram_used() -> int:
    """Returns current GPU memory used in MiB via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return int(out.splitlines()[0])
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return 0


def run_benchmark():
    print("=" * 70)
    print("🚀 Running Phase 23 Benchmark: Dream-RSI 2.0 Replay Simulator Pool")
    print("=" * 70)

    vram_start = get_cuda_vram_used()

    # 1. Populate persistent simulator pool
    cache_dir = testbed_root / "data" / "dream_worlds"
    cache_dir.mkdir(parents=True, exist_ok=True)
    pool = DreamRSISimulatorPool(cache_dir=str(cache_dir))

    transitions = [
        StateTransition(0, "AST Outline Scan", "ast_grep_outline", 0.85, "outline_ready", 0.60, 0.80),
        StateTransition(1, "Declarative Focus Scope", "declare_focus_scope", 0.90, "scope_locked", 0.55, 0.85),
        StateTransition(2, "Surgical Code Diff", "apply_surgical_diff", 0.95, "diff_applied", 0.50, 0.90),
        StateTransition(3, "Pytest Compiler Gate", "run_pytest_gate", 1.00, "tests_passed", 0.70, 0.95),
        StateTransition(4, "Chezmoi Sync & Learn", "distill_learned_rule", 0.88, "knowledge_persisted", 0.45, 0.85),
    ]

    content = json.dumps([t.action for t in transitions])
    root_hash = hashlib.sha256(content.encode()).hexdigest()
    tree = ReplayTree(
        session_id="session_live_phase23",
        task_goal="Topological taskDAG dispatch with AST failure annealing",
        root_hash=root_hash,
        transitions=transitions,
        metadata={"phase": 23, "eval": "dream_rsi2"},
    )

    print(f"\n[Step 1] Persisting Content-Addressed World Tree: {root_hash[:16]}...")
    tree_path = pool.persist_tree(tree)
    print(f"  * Saved to: {tree_path}")

    # 2. Counterfactual Candidate Evaluation
    print("\n[Step 2] Executing Doubly Robust Off-Policy 'Dreaming' across Pool...")
    candidate_policy = {
        "ast_grep_outline": 0.90,
        "declare_focus_scope": 0.92,
        "apply_surgical_diff": 0.95,
        "run_pytest_gate": 0.98,
        "distill_learned_rule": 0.85,
    }

    eval_result = pool.evaluate_counterfactual_candidate(tree, candidate_policy)

    print(f"  * Baseline Policy Value  : {eval_result['v_baseline']}")
    print(f"  * Candidate Policy Value : {eval_result['v_candidate']}")
    print(f"  * Performance Lift       : {eval_result['performance_lift']}")
    print(f"  * Required RRSI Margin   : {eval_result['required_margin']}")
    print(f"  * RRSI Gate Passed       : {eval_result['rrsi_stability_gate_passed']}")
    print(f"  * Call Reduction Ratio   : {eval_result['call_reduction_ratio']}x (Target: >= 2.0x)")
    print(f"  * Evaluation Latency     : {eval_result['dream_eval_latency_ms']} ms (Target: <= 50.0 ms)")

    vram_end = get_cuda_vram_used()
    vram_delta = max(0, vram_end - vram_start)
    print(f"\n[Hardware Boundary] Start VRAM: {vram_start} MiB, End VRAM: {vram_end} MiB, Delta: {vram_delta} MiB")

    metrics = {
        "cuda_vram_delta_mib": vram_delta,
        "call_reduction_ratio": eval_result["call_reduction_ratio"],
        "rrsi_stability_gate_passed": eval_result["rrsi_stability_gate_passed"],
        "dream_eval_latency_ms": eval_result["dream_eval_latency_ms"],
        "performance_lift": eval_result["performance_lift"],
        "tree_root_hash": root_hash,
    }

    metrics_file = testbed_root / "dream_rsi2_metrics.json"
    metrics_file.write_text(json.dumps(metrics, indent=2))
    print(f"\n✅ Metrics persisted to {metrics_file}")
    return metrics


if __name__ == "__main__":
    run_benchmark()
