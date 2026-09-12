"""
Hermes Plugin Submodule: hypothesis_tree
========================================
Branching & Hypothesis Tree Search Engine (SWE-Search / Arbor / MCTS Style).
Enforces Two-Strike Tabu search, automatic backtracking, and negative boundary constraint accumulation.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

STORAGE_PATH = Path("/dev/shm/hypothesis_tree.json")


class HypothesisNode(BaseModel):
    id: str
    parent_id: Optional[str] = None
    title: str
    hypothesis: str
    status: str = "EXPLORING"  # EXPLORING, SUCCEEDED, FAILED, PRUNED
    boundary_constraints: List[str] = Field(default_factory=list)
    failure_trace: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class HypothesisTree(BaseModel):
    root_id: Optional[str] = None
    nodes: Dict[str, HypothesisNode] = Field(default_factory=dict)
    active_node_id: Optional[str] = None

    def add_branch(self, title: str, hypothesis: str, parent_id: Optional[str] = None) -> HypothesisNode:
        p_id = parent_id or self.active_node_id
        node_id = hashlib.md5(f"{p_id}:{title}:{time.time()}".encode()).hexdigest()[:10]
        node = HypothesisNode(id=node_id, parent_id=p_id, title=title, hypothesis=hypothesis)
        self.nodes[node_id] = node
        self.active_node_id = node_id
        if not self.root_id:
            self.root_id = node_id
        return node

    def record_failure_and_backtrack(self, failure_trace: str, constraint: str) -> Optional[HypothesisNode]:
        """Mark active branch as failed, extract boundary constraint, and backtrack to parent."""
        if self.active_node_id and self.active_node_id in self.nodes:
            curr = self.nodes[self.active_node_id]
            curr.status = "FAILED"
            curr.failure_trace = failure_trace[:400]
            curr.boundary_constraints.append(constraint)

            # Backtrack to parent
            self.active_node_id = curr.parent_id
            return self.nodes.get(self.active_node_id) if self.active_node_id else None
        return None

    def mark_active_succeeded(self):
        if self.active_node_id and self.active_node_id in self.nodes:
            self.nodes[self.active_node_id].status = "SUCCEEDED"

    def get_accumulated_negative_constraints(self) -> List[str]:
        """Gather all boundary constraints discovered across all failed branches."""
        constraints = []
        for n in self.nodes.values():
            if n.status == "FAILED":
                constraints.extend(n.boundary_constraints)
        return list(set(constraints))

    def save_state(self, filepath: Optional[str] = None):
        p = Path(filepath) if filepath else STORAGE_PATH
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load_state(cls, filepath: Optional[str] = None) -> "HypothesisTree":
        p = Path(filepath) if filepath else STORAGE_PATH
        if p.exists():
            try:
                return cls.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        return cls()


_GLOBAL_TREE: Optional[HypothesisTree] = None


def get_hypothesis_tree() -> HypothesisTree:
    global _GLOBAL_TREE
    if _GLOBAL_TREE is None:
        _GLOBAL_TREE = HypothesisTree.load_state()
    return _GLOBAL_TREE
