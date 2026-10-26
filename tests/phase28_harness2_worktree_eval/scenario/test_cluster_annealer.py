"""Unit test suite for ClusterAnnealer (Phase 28 scenario)."""

import pytest
from scenario.cluster_annealer import ClusterAnnealer


def test_schedule_dag_linear():
    annealer = ClusterAnnealer("LinearPipeline")
    tasks = ["architect", "coder", "tester", "critic"]
    edges = [("architect", "coder"), ("coder", "tester"), ("tester", "critic")]
    order = annealer.schedule_dag(tasks, edges)
    assert order == ["architect", "coder", "tester", "critic"]
    assert annealer.annealed_count == 1


def test_schedule_dag_with_unregistered_edge():
    """Validates that edges referencing unregistered tasks do not raise KeyError."""
    annealer = ClusterAnnealer("ExternalBoundaryPipeline")
    tasks = ["architect", "coder", "tester", "critic"]
    # Edge ("external_repo", "tester") references external node not in tasks
    edges = [("architect", "coder"), ("external_repo", "tester"), ("tester", "critic")]
    order = annealer.schedule_dag(tasks, edges)
    assert "architect" in order
    assert "critic" in order
    assert annealer.annealed_count == 1


def test_schedule_dag_diamond():
    annealer = ClusterAnnealer("DiamondDAG")
    tasks = ["A", "B", "C", "D"]
    edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]
    order = annealer.schedule_dag(tasks, edges)
    assert len(order) == 4
    assert order[0] == "A"
    assert order[-1] == "D"
