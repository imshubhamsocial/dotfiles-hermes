"""Verification test suite for Phase 19 metrics and gate criteria."""

import json
import math
import pathlib
import sys

import pytest

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from latent_solver import LatentAttractorSolver


def test_looped_attractor_metrics():
    """Asserts that benchmark metrics meet all Phase 19 criteria."""
    report_file = testbed_root / "looped_attractor_metrics.json"
    assert report_file.exists(), "looped_attractor_metrics.json must be generated prior to verification"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report.get("cuda_vram_delta_mib") == 0
    assert report.get("attractor_convergence_reached") is True
    assert report.get("prefill_cache_reuse_pct", 0.0) >= 85.0
    assert report.get("deep_loop_accuracy_gain", 0.0) >= 0.15


def test_live_attractor_convergence_enforcement():
    """Directly verifies that LatentAttractorSolver stabilizes residual under iterative loops."""
    solver = LatentAttractorSolver(dim=32, max_loops=6, epsilon=0.01)
    init_state = [math.sin(i * 0.4) for i in range(32)]
    
    res = solver.evaluate_constraint_graph(graph_entropy=0.75, initial_latent=init_state)
    assert res["converged"] is True
    assert res["steps"] > 1
    assert res["residual_diff"] < solver.epsilon
