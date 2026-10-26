"""Tests for LatentAttractorSolver (Phase 19)."""

import math
import pathlib
import sys

import pytest

scenario_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(scenario_dir))

from latent_solver import LatentAttractorSolver


def test_attractor_convergence_high_entropy():
    """Validates that high-entropy graphs deliberate until attractor convergence."""
    solver = LatentAttractorSolver(dim=32, max_loops=6, epsilon=0.01)
    init_state = [math.sin(i * 0.3) for i in range(32)]
    
    res = solver.evaluate_constraint_graph(graph_entropy=0.85, initial_latent=init_state)
    
    assert res["converged"] is True, f"Attractor must converge on high-entropy graphs (diff={res['residual_diff']})"
    assert res["steps"] > 1, f"Must iterate deeper than 1 step for high-entropy graphs (got {res['steps']})"
    assert res["residual_diff"] < solver.epsilon, f"Residual displacement must be < {solver.epsilon}"
    assert res["success"] is True


def test_low_entropy_fast_exit():
    """Validates that low-entropy graphs can stabilize with low loop count."""
    solver = LatentAttractorSolver(dim=32, max_loops=6, epsilon=0.05)
    init_state = [0.05] * 32
    
    res = solver.evaluate_constraint_graph(graph_entropy=0.2, initial_latent=init_state)
    assert res["success"] is True
