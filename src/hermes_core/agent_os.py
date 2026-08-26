"""
Phase 7: Persistent Agent OS Daemon & Event-Driven Dispatch Engine
==================================================================
Implements the 7-layer unified Agent OS stack (Julian Goldie architecture):
  Layer 1: Foundation (Workspace, Btrfs NOCOW, /dev/shm)
  Layer 2: Memory (ExperienceStore, TaskDAG SQLite WAL, SymbolGraph)
  Layer 3: Brain (Local 4B SLM on :8138 / OmniRouter)
  Layer 4: Agents (@architect, @coder, @tester, @optimizer)
  Layer 5: Command (Event-driven queue: git, schedule, task, failure)
  Layer 6: Production (Task DAG scheduler, Observer Gate, Live LSP)
  Layer 7: Loop (Metacognitive flywheel & SkillEvaluator)
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from .task_graph import TaskDAG, create_memory_dag
    from .symbol_graph import SymbolGraph, create_memory_graph
    from .experience_store import ExperienceStore, create_experience_store
    from .skill_evaluator import SkillEvaluator, EvaluationEpisode, create_skill_evaluator
    from .lsp_bridge import LiveLSPBridge, create_lsp_bridge
    from .hitl_gateway import HITLSupervisoryGateway, create_hitl_gateway, RiskLevel
except ImportError:
    from hermes_core.task_graph import TaskDAG, create_memory_dag
    from hermes_core.symbol_graph import SymbolGraph, create_memory_graph
    from hermes_core.experience_store import ExperienceStore, create_experience_store
    from hermes_core.skill_evaluator import SkillEvaluator, EvaluationEpisode, create_skill_evaluator
    from hermes_core.lsp_bridge import LiveLSPBridge, create_lsp_bridge
    from hermes_core.hitl_gateway import HITLSupervisoryGateway, create_hitl_gateway, RiskLevel


@dataclass
class AgentEvent:
    event_id: str
    event_type: str  # "TASK_SUBMITTED" | "GIT_EVENT" | "SCHEDULE_TICK" | "TASK_FAILURE"
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class AgentOSDaemon:
    """
    Persistent Agent OS coordination daemon managing the multi-agent lifecycle,
    event queues, memory persistence, and automated optimization loops.
    """

    def __init__(
        self,
        workspace_root: Optional[Union[str, Path]] = None,
        db_path: Optional[Union[str, Path]] = None,
        mode: str = "supervised",
    ):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.mode = mode
        
        # Layer 2: Persistent Memory & State
        self.task_dag: TaskDAG = create_memory_dag()
        self.symbol_graph: SymbolGraph = create_memory_graph()
        self.experience_store: ExperienceStore = create_experience_store(db_path=db_path)
        self.skill_evaluator: SkillEvaluator = create_skill_evaluator()
        self.lsp_bridge: LiveLSPBridge = create_lsp_bridge(workspace_root=self.workspace_root, auto_fallback=True)
        self.hitl_gateway: HITLSupervisoryGateway = create_hitl_gateway(mode=self.mode)

        # Layer 5: Command Event Queue
        self._event_queue: queue.Queue[AgentEvent] = queue.Queue()
        self._processed_events: List[AgentEvent] = []
        self._lock = threading.Lock()
        self._running = False
        self._event_counter = 1

    def submit_task(self, task_id: str, title: str, prompt: str, role: str = "coder") -> AgentEvent:
        """Enqueues a new user task for execution."""
        event = AgentEvent(
            event_id=f"evt_{self._event_counter}",
            event_type="TASK_SUBMITTED",
            payload={"task_id": task_id, "title": title, "prompt": prompt, "role": role},
        )
        self._event_counter += 1
        self.task_dag.add_task(task_id, title, prompt)
        self._event_queue.put(event)
        return event

    def on_git_event(self, event_type: str, commit_hash: str) -> AgentEvent:
        """Handles external git repository triggers."""
        event = AgentEvent(
            event_id=f"evt_{self._event_counter}",
            event_type="GIT_EVENT",
            payload={"git_action": event_type, "commit": commit_hash},
        )
        self._event_counter += 1
        self._event_queue.put(event)
        return event

    def on_schedule_tick(self) -> AgentEvent:
        """Handles periodic cron triggers for memory pruning & optimization."""
        event = AgentEvent(
            event_id=f"evt_{self._event_counter}",
            event_type="SCHEDULE_TICK",
            payload={"tick_time": time.time()},
        )
        self._event_counter += 1
        self._event_queue.put(event)
        return event

    def on_task_failure(self, task_id: str, error_trace: str) -> AgentEvent:
        """Handles task failure, updating task DAG and recording failure constraints."""
        event = AgentEvent(
            event_id=f"evt_{self._event_counter}",
            event_type="TASK_FAILURE",
            payload={"task_id": task_id, "error": error_trace},
        )
        self._event_counter += 1
        self.experience_store.record_episode(
            episode_id=f"ep_fail_{task_id}",
            task_description=f"Task {task_id} failure",
            subsystem="agent_os",
            tool_calls=[],
            outcome="FAILURE",
            token_usage=400,
            duration_sec=15.0,
            error_traces=[error_trace],
        )
        self._event_queue.put(event)
        return event

    def process_next_event(self) -> Optional[AgentEvent]:
        """Pops and processes a single event from the queue."""
        try:
            event = self._event_queue.get_nowait()
        except queue.Empty:
            return None

        with self._lock:
            if event.event_type == "TASK_SUBMITTED":
                task_id = event.payload["task_id"]
                self.task_dag.mark_running(task_id)
            elif event.event_type == "SCHEDULE_TICK":
                # Optimizer pass: detect compute waste
                waste = self.experience_store.detect_compute_waste()
                event.payload["waste_detected"] = len(waste)
            elif event.event_type == "TASK_FAILURE":
                task_id = event.payload["task_id"]
                # Handled via experience store
            
            self._processed_events.append(event)
            self._event_queue.task_done()
            return event

    def process_all_events(self) -> List[AgentEvent]:
        """Drains and executes all pending events in queue."""
        processed = []
        while True:
            ev = self.process_next_event()
            if ev is None:
                break
            processed.append(ev)
        return processed

    def get_system_status(self) -> Dict[str, Any]:
        """Returns consolidated 7-layer Agent OS telemetry."""
        ready_tasks = self.task_dag.get_ready_tasks()
        return {
            "status": "HEALTHY",
            "workspace": str(self.workspace_root),
            "pending_events": self._event_queue.qsize(),
            "processed_events_count": len(self._processed_events),
            "ready_dag_tasks": len(ready_tasks),
            "total_episodes_recorded": len(self.experience_store.episodes),
            "negative_constraints_active": len(self.experience_store.generate_negative_constraints()),
        }


def create_agent_os_daemon(
    workspace_root: Optional[Union[str, Path]] = None,
    db_path: Optional[Union[str, Path]] = None,
    mode: str = "supervised",
) -> AgentOSDaemon:
    return AgentOSDaemon(
        workspace_root=workspace_root,
        db_path=db_path,
        mode=mode,
    )
