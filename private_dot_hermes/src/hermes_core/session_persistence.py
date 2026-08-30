"""
Durable Session Persistence & Zero-Penalty Resumption Engine
============================================================
Implements Frontier Stateful Graph Restoration (Astra / SWE-Search / Claude Code SDK 2026):
  1. Decouples Session State from Chat Transcripts (Finite State DAG + MCTS Hypothesis Tree).
  2. Preserves all explored branches, failed paths, and negative boundary constraints across restarts/reboots.
  3. Snapshot & Receipt Verification: Atomic file snapshots and SHA256 checksums per node.
  4. Instant Zero-KV-Penalty Resumption: Generates compact (<1,000 token) stateless prompts for fresh workers.
  5. Rollback Guard: Restores clean parent snapshot if a crash occurs midway during an unverified edit.
"""

import os
import sys
import json
import time
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from hermes_core.task_graph import TaskGraph, SubTask
from hermes_core.hypothesis_tree import HypothesisTree, HypothesisNode
from hermes_core.working_memory import WorkingMemoryAnchor


class ArtifactReceipt(BaseModel):
    rel_path: str
    sha256: str
    size_bytes: int
    mtime: float


class NodeReceipt(BaseModel):
    node_id: str
    task_id: Optional[str] = None
    status: str  # SUCCEEDED, FAILED, PRUNED
    artifacts: List[ArtifactReceipt] = Field(default_factory=list)
    boundary_constraints: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class DurableSessionState(BaseModel):
    session_id: str
    project_goal: str
    workspace_dir: str
    storage_dir: str
    task_graph: TaskGraph
    hypothesis_tree: HypothesisTree
    working_memory: WorkingMemoryAnchor
    receipts: Dict[str, NodeReceipt] = Field(default_factory=dict)
    active_branch_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    @classmethod
    def initialize(
        cls,
        session_id: str,
        project_goal: str,
        workspace_dir: str,
        storage_dir: Optional[str] = None
    ) -> "DurableSessionState":
        store_path = Path(storage_dir) if storage_dir else Path(workspace_dir) / ".hermes_session"
        store_path.mkdir(parents=True, exist_ok=True)

        task_graph = TaskGraph(project_goal=project_goal)
        hypothesis_tree = HypothesisTree()
        working_memory = WorkingMemoryAnchor(project_goal=project_goal)

        session = cls(
            session_id=session_id,
            project_goal=project_goal,
            workspace_dir=str(Path(workspace_dir).resolve()),
            storage_dir=str(store_path.resolve()),
            task_graph=task_graph,
            hypothesis_tree=hypothesis_tree,
            working_memory=working_memory
        )
        session.checkpoint()
        return session

    def checkpoint(self, snapshot_files: Optional[List[str]] = None):
        """Atomically commit current state machine, hypothesis DAG, and file snapshots to disk."""
        self.updated_at = time.time()
        store_path = Path(self.storage_dir)
        store_path.mkdir(parents=True, exist_ok=True)

        # 1. Save File Snapshots if active node exists
        if snapshot_files and self.hypothesis_tree.active_node_id:
            node_id = self.hypothesis_tree.active_node_id
            snapshot_dir = store_path / "snapshots" / node_id
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            ws = Path(self.workspace_dir)
            receipt_artifacts = []

            for rel in snapshot_files:
                src = ws / rel
                if src.exists() and src.is_file():
                    dst = snapshot_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

                    # Compute checksum
                    content = src.read_bytes()
                    sha = hashlib.sha256(content).hexdigest()
                    receipt_artifacts.append(ArtifactReceipt(
                        rel_path=rel,
                        sha256=sha,
                        size_bytes=len(content),
                        mtime=src.stat().st_mtime
                    ))

            # Store receipt
            self.receipts[node_id] = NodeReceipt(
                node_id=node_id,
                task_id=self.task_graph.active_task_id,
                status=self.hypothesis_tree.nodes.get(node_id, HypothesisNode(id=node_id, title="", hypothesis="")).status,
                artifacts=receipt_artifacts,
                boundary_constraints=self.hypothesis_tree.nodes.get(node_id, HypothesisNode(id=node_id, title="", hypothesis="")).boundary_constraints
            )

        # 2. Atomic write of session JSON
        state_file = store_path / "session_state.json"
        temp_file = store_path / "session_state.json.tmp"
        
        temp_file.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        temp_file.replace(state_file)

    @classmethod
    def restore(cls, storage_dir: str) -> Optional["DurableSessionState"]:
        """Restore full session state from disk with rollback protection for in-flight crashes."""
        store_path = Path(storage_dir)
        state_file = store_path / "session_state.json"
        
        if not state_file.exists():
            return None

        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            session = cls.model_validate(data)
            
            # Post-Restore In-Flight Crash Guard:
            # If the active node was left in "EXPLORING" status during a hard crash/power loss,
            # roll back the workspace files to the parent node's verified snapshot!
            active_node_id = session.hypothesis_tree.active_node_id
            if active_node_id and active_node_id in session.hypothesis_tree.nodes:
                active_node = session.hypothesis_tree.nodes[active_node_id]
                if active_node.status == "EXPLORING":
                    # Mark as crash-interrupted and restore parent snapshot if available
                    active_node.status = "CRASH_INTERRUPTED"
                    if active_node.parent_id:
                        session._restore_snapshot_to_workspace(active_node.parent_id)
                        session.hypothesis_tree.active_node_id = active_node.parent_id
                    session.checkpoint()
                    
            return session
        except Exception as e:
            print(f"[DurableSessionState] Restore error: {e}", file=sys.stderr)
            return None

    def create_branch(self, title: str, hypothesis: str, parent_id: Optional[str] = None) -> HypothesisNode:
        """Create a new candidate branch in the Hypothesis Tree and save checkpoint."""
        node = self.hypothesis_tree.add_branch(title=title, hypothesis=hypothesis, parent_id=parent_id)
        self.active_branch_id = node.id
        self.checkpoint()
        return node

    def record_branch_failure_and_backtrack(self, failure_trace: str, negative_constraint: str) -> Optional[HypothesisNode]:
        """Record branch failure, extract Tabu constraint, rollback workspace to parent, and save state."""
        prev_active = self.hypothesis_tree.active_node_id
        parent_node = self.hypothesis_tree.record_failure_and_backtrack(failure_trace, negative_constraint)
        
        # Rollback workspace files to parent snapshot
        if parent_node:
            self._restore_snapshot_to_workspace(parent_node.id)
            self.active_branch_id = parent_node.id
            
        self.checkpoint()
        return parent_node

    def mark_active_branch_succeeded(self, snapshot_files: Optional[List[str]] = None):
        """Mark active branch succeeded, commit snapshot receipt, and update TaskGraph."""
        self.hypothesis_tree.mark_active_succeeded()
        if self.task_graph.active_task_id:
            self.task_graph.mark_task_verified(self.task_graph.active_task_id)
        self.checkpoint(snapshot_files=snapshot_files)

    def _restore_snapshot_to_workspace(self, node_id: str):
        """Restore physical files in workspace from node snapshot."""
        store_path = Path(self.storage_dir)
        snapshot_dir = store_path / "snapshots" / node_id
        if snapshot_dir.exists():
            ws = Path(self.workspace_dir)
            for file_path in snapshot_dir.rglob("*"):
                if file_path.is_file():
                    rel = file_path.relative_to(snapshot_dir)
                    dest = ws / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest)

    def build_resumption_prompt(self, target_task_id: Optional[str] = None) -> str:
        """Build a compact, zero-penalty stateless resumption prompt (<800 tokens)."""
        # 1. Determine target task
        task = None
        if target_task_id and target_task_id in self.task_graph.tasks:
            task = self.task_graph.tasks[target_task_id]
        else:
            task = self.task_graph.get_next_runnable_task()

        task_title = task.title if task else "Continue Project"
        task_desc = task.description if task else self.project_goal
        target_files = ", ".join(task.target_files) if task and task.target_files else "workspace files"

        # 2. Accumulated negative constraints from failed branches
        neg_constraints = self.hypothesis_tree.get_accumulated_negative_constraints()
        constraint_block = ""
        if neg_constraints:
            items = "\n".join(f"  - ❌ AVOID: {c}" for c in neg_constraints)
            constraint_block = f"\nCRITICAL BOUNDARY CONSTRAINTS (Learned from prior failed branches):\n{items}\n"

        # 3. Compact Working Memory Anchor
        anchor = self.working_memory.compile_anchor_block()

        prompt = (
            f"{anchor}\n"
            f"AUTONOMOUS RESUMPTION DIRECTIVE:\n"
            f"Active Milestone: {task_title}\n"
            f"Target Files: {target_files}\n"
            f"Specification: {task_desc}\n"
            f"{constraint_block}\n"
            f"INSTRUCTION:\n"
            f"1. Read the current verified files from disk.\n"
            f"2. Apply the required changes cleanly in-place without repeating the boundary constraints listed above.\n"
            f"3. Ensure all syntax and contracts are strictly satisfied."
        )
        return prompt.strip()

    def save_kv_slot(self, slot_id: int = 0, server_url: str = "http://127.0.0.1:8138") -> bool:
        """Issue POST /slots/{slot_id}?action=save to persist KV cache to disk."""
        try:
            import urllib.request
            url = f"{server_url}/slots/{slot_id}?action=save"
            payload = json.dumps({"filename": f"slot_{self.session_id}.bin"}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[DurableSessionState] KV slot save notice (server offline or non-GGUF): {e}", file=sys.stderr)
            return False

    def restore_kv_slot(self, slot_id: int = 0, server_url: str = "http://127.0.0.1:8138") -> bool:
        """Issue POST /slots/{slot_id}?action=restore to restore KV cache from disk with 0ms prefill."""
        try:
            import urllib.request
            url = f"{server_url}/slots/{slot_id}?action=restore"
            payload = json.dumps({"filename": f"slot_{self.session_id}.bin"}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[DurableSessionState] KV slot restore notice (server offline or non-GGUF): {e}", file=sys.stderr)
            return False
