"""
Contract Tests: Task DAG Engine & Dependency Resolution via NetworkX
====================================================================
Validates:
  1. Linear task sequence (A -> B -> C) dependency resolution.
  2. Diamond DAG task parallelization and fan-in resolution.
  3. Cycle detection and topological ordering.
  4. Dynamic ready-task resolution based on completed dependencies.
"""

from __future__ import annotations

import networkx as nx
import pytest


class TaskEngine:
    """Thin wrapper over upstream networkx.DiGraph for task tracking."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.completed: set[str] = set()

    def add_task(self, task_id: str, label: str = ""):
        self.graph.add_node(task_id, label=label)

    def add_dependency(self, parent_id: str, child_id: str):
        """parent_id must be completed before child_id can start."""
        self.graph.add_edge(parent_id, child_id)
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(parent_id, child_id)
            raise ValueError(f"Cycle detected adding dependency {parent_id} -> {child_id}")

    def get_ready_tasks(self) -> list[str]:
        """Returns tasks whose predecessors are all completed."""
        ready = []
        for node in self.graph.nodes:
            if node in self.completed:
                continue
            predecessors = set(self.graph.predecessors(node))
            if predecessors.issubset(self.completed):
                ready.append(node)
        return sorted(ready)

    def complete_task(self, task_id: str):
        self.completed.add(task_id)


def test_linear_sequence_dependency_resolution():
    engine = TaskEngine()
    engine.add_task("A")
    engine.add_task("B")
    engine.add_task("C")
    engine.add_dependency("A", "B")
    engine.add_dependency("B", "C")

    # Initially only A is ready
    assert engine.get_ready_tasks() == ["A"]

    # Complete A -> B becomes ready
    engine.complete_task("A")
    assert engine.get_ready_tasks() == ["B"]

    # Complete B -> C becomes ready
    engine.complete_task("B")
    assert engine.get_ready_tasks() == ["C"]

    # Complete C -> none left
    engine.complete_task("C")
    assert engine.get_ready_tasks() == []


def test_diamond_dag_parallelization_and_fan_in():
    """Diamond pattern: A -> (B, C) -> D"""
    engine = TaskEngine()
    for t in ["A", "B", "C", "D"]:
        engine.add_task(t)

    engine.add_dependency("A", "B")
    engine.add_dependency("A", "C")
    engine.add_dependency("B", "D")
    engine.add_dependency("C", "D")

    # A is root
    assert engine.get_ready_tasks() == ["A"]

    # Complete A -> B and C both ready (parallelizable)
    engine.complete_task("A")
    assert engine.get_ready_tasks() == ["B", "C"]

    # Complete B only -> D is not ready yet because C is pending
    engine.complete_task("B")
    assert engine.get_ready_tasks() == ["C"]

    # Complete C -> D is now ready
    engine.complete_task("C")
    assert engine.get_ready_tasks() == ["D"]


def test_cycle_detection():
    engine = TaskEngine()
    engine.add_task("A")
    engine.add_task("B")
    engine.add_dependency("A", "B")

    with pytest.raises(ValueError, match="Cycle detected"):
        engine.add_dependency("B", "A")


def test_topological_ordering():
    engine = TaskEngine()
    for t in ["C", "A", "B"]:
        engine.add_task(t)
    engine.add_dependency("A", "B")
    engine.add_dependency("B", "C")

    order = list(nx.topological_sort(engine.graph))
    assert order == ["A", "B", "C"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
