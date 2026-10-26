"""Unit tests for DreamReplayEngine (Phase 16)."""

import json
import pathlib
import pytest
from dream_engine import DreamReplayEngine

testbed_root = pathlib.Path(__file__).resolve().parents[1]
cache_dir = testbed_root / ".hermes" / "cache" / "dream_worlds"


def sample_trace_with_dead_end():
    """Generates a synthetic trace with 7 tool actions and a dead-end branch."""
    return [
        {"tool_name": "read_file", "focus_regime": "<global>", "pytest_exit_code": 0},
        {"tool_name": "ast_outline", "focus_regime": "<focus>", "pytest_exit_code": 0},
        {"tool_name": "apply_diff", "focus_regime": "<focus>", "pytest_exit_code": 1},
        {"tool_name": "apply_diff", "focus_regime": "<focus>", "pytest_exit_code": 1},
        # These 3 should be pruned by Two-Strike rollback:
        {"tool_name": "terminal_retry", "focus_regime": "<focus>", "pytest_exit_code": 1},
        {"tool_name": "terminal_retry", "focus_regime": "<focus>", "pytest_exit_code": 1},
        {"tool_name": "terminal_retry", "focus_regime": "<focus>", "pytest_exit_code": 1},
    ]


def test_reduction_ratio_and_pruning():
    engine = DreamReplayEngine(cache_dir=str(cache_dir))
    trace = sample_trace_with_dead_end()
    ratio, tree = engine.simulate_counterfactual_pruning(trace)

    assert tree["baseline_calls"] == 7
    assert tree["pruned_calls"] == 4
    assert ratio == 7.0 / 4.0
    assert ratio >= 1.40


def test_disk_cache_persistence():
    engine = DreamReplayEngine(cache_dir=str(cache_dir))
    trace = sample_trace_with_dead_end()
    ratio, tree = engine.simulate_counterfactual_pruning(trace)

    task_hash = tree["task_hash"]
    cache_file = cache_dir / f"{task_hash}.json"
    assert cache_file.exists(), f"Cached dream world tree missing: {cache_file}"

    data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert data["task_hash"] == task_hash
    assert data["reduction_ratio"] == ratio
    assert len(data["nodes"]) == 4


def test_recovery_after_single_failure():
    engine = DreamReplayEngine(cache_dir=str(cache_dir))
    trace = [
        {"tool_name": "read_file", "pytest_exit_code": 0},
        {"tool_name": "apply_diff", "pytest_exit_code": 1},  # Single failure
        {"tool_name": "read_file", "pytest_exit_code": 0},   # Recovery!
        {"tool_name": "apply_diff", "pytest_exit_code": 0},
    ]
    ratio, tree = engine.simulate_counterfactual_pruning(trace)
    assert tree["pruned_calls"] == 4
    assert ratio == 1.0
