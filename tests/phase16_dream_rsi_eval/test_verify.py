"""Verification test suite for Phase 16 metrics and gate criteria."""

import json
import pathlib
import pytest
from dream_engine import DreamReplayEngine

testbed_root = pathlib.Path(__file__).resolve().parent
cache_dir = testbed_root / ".hermes" / "cache" / "dream_worlds"


def test_dream_engine_two_strike_pruning():
    """Asserts that DreamReplayEngine correctly prunes branches on two consecutive failures."""
    engine = DreamReplayEngine(cache_dir=str(cache_dir))
    trace = [
        {"tool": "A", "pytest_exit_code": 0},
        {"tool": "B", "pytest_exit_code": 1},
        {"tool": "C", "pytest_exit_code": 1},
        # These 2 should be pruned:
        {"tool": "D", "pytest_exit_code": 1},
        {"tool": "E", "pytest_exit_code": 1},
    ]
    ratio, tree = engine.simulate_counterfactual_pruning(trace)
    assert tree["baseline_calls"] == 5
    assert tree["pruned_calls"] == 3
    assert ratio == 5.0 / 3.0
    assert ratio >= 1.40


def test_dream_engine_caches_to_disk():
    """Asserts that simulated dream world trees are persisted to disk."""
    engine = DreamReplayEngine(cache_dir=str(cache_dir))
    trace = [
        {"tool": "A", "pytest_exit_code": 0},
        {"tool": "B", "pytest_exit_code": 1},
        {"tool": "C", "pytest_exit_code": 1},
    ]
    ratio, tree = engine.simulate_counterfactual_pruning(trace)
    task_hash = tree["task_hash"]
    cache_file = cache_dir / f"{task_hash}.json"
    assert cache_file.exists(), f"Expected cache file {cache_file} does not exist"
    loaded = json.loads(cache_file.read_text(encoding="utf-8"))
    assert loaded["task_hash"] == task_hash
    assert loaded["reduction_ratio"] == ratio


def test_dream_replay_results_metrics():
    """Asserts that the DreamRSI results satisfy all Phase 16 criteria."""
    report_file = testbed_root / "dream_replay_results.json"
    assert report_file.exists(), "dream_replay_results.json must be generated prior to verification"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report.get("simulated_calls_reduction_ratio", 0) >= 1.40
    assert report.get("harness2_worktree_compose_gain", 0) > 0.0
    assert report.get("rrsi_stability_margin_exceeded") is True
    assert report.get("held_out_pytest_exit_code") == 0
