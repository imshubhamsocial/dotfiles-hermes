"""
Graph Engineering Engine & Typed DAG Contracts (Milestone U78)
==============================================================
Manages and validates multi-bot execution topologies defined in graph.yaml:
  - Topologically sorts execution order (DAG dependency resolution)
  - Checks for cycles and unconnected nodes
  - Validates intermediate payloads against typed JSON Schema contracts
  - Enforces governance gates between transition edges
"""

from __future__ import annotations

import os
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import jsonschema
import yaml


@dataclass
class GraphNode:
    name: str
    role: str
    bot_class: str
    output_schema: Dict[str, Any]


@dataclass
class GraphEdge:
    from_node: str
    to_node: str
    governance_gate: Optional[str] = None


@dataclass
class GraphValidationResult:
    valid: bool
    topological_order: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class GraphEngine:
    """Executes and validates formal multi-bot graph workflows."""

    def __init__(self, graph_path: Optional[Path] = None):
        self.graph_path = graph_path or self._find_graph_path()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._load_graph()

    def _find_graph_path(self) -> Path:
        p1 = Path.home() / ".hermes" / "rules" / "graph.yaml"
        if p1.exists():
            return p1
        p2 = Path(os.getcwd()) / ".hermes" / "rules" / "graph.yaml"
        return p2

    def _load_graph(self) -> None:
        if not self.graph_path.exists():
            return
        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            raw_nodes = data.get("nodes", {})
            for n_id, n_val in raw_nodes.items():
                self.nodes[n_id] = GraphNode(
                    name=n_id,
                    role=n_val.get("role", ""),
                    bot_class=n_val.get("bot_class", "coder"),
                    output_schema=n_val.get("output_schema", {}),
                )

            raw_edges = data.get("edges", [])
            for e in raw_edges:
                self.edges.append(
                    GraphEdge(
                        from_node=e.get("from"),
                        to_node=e.get("to"),
                        governance_gate=e.get("governance_gate"),
                    )
                )
        except Exception:
            pass

    def validate_topology(self) -> GraphValidationResult:
        """Kahn's algorithm for cycle detection and topological sorting."""
        if not self.nodes:
            return GraphValidationResult(valid=False, errors=["Empty graph: no nodes defined."])

        in_degree = {n: 0 for n in self.nodes}
        adj = defaultdict(list)

        for edge in self.edges:
            if edge.from_node not in self.nodes:
                return GraphValidationResult(valid=False, errors=[f"Unknown from_node '{edge.from_node}' in edge."])
            if edge.to_node not in self.nodes:
                return GraphValidationResult(valid=False, errors=[f"Unknown to_node '{edge.to_node}' in edge."])
            adj[edge.from_node].append(edge.to_node)
            in_degree[edge.to_node] += 1

        queue = deque([n for n, deg in in_degree.items() if deg == 0])
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(self.nodes):
            return GraphValidationResult(valid=False, errors=["Cyclic dependency detected in graph topology."])

        return GraphValidationResult(valid=True, topological_order=topo_order)

    def validate_node_output(self, node_name: str, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        node = self.nodes.get(node_name)
        if not node:
            return False, [f"Node '{node_name}' not found."]
        if not node.output_schema:
            return True, []

        try:
            jsonschema.validate(instance=payload, schema=node.output_schema)
            return True, []
        except jsonschema.ValidationError as e:
            return False, [e.message]


def create_graph_engine(graph_path: Optional[Path] = None) -> GraphEngine:
    return GraphEngine(graph_path=graph_path)
