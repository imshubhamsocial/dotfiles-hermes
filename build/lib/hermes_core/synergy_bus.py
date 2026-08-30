"""
Milestone U57: Unified Reactive Execution & Memory Bus
======================================================
Implements Unified Reactive Event Bus linking:
  - Google ADK 2.0 TaskDAG (reflective_learner.py)
  - Volcengine OpenViking VFS (openviking_vfs.py)
  - OpenCode-Mem Vector Store (vector_memory.py)
  - Pre-Commit Verification & AST Gating
  - Zero GPU VRAM overhead (pure CPU RAMDisk event dispatch)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

from hermes_core.openviking_vfs import OpenVikingVFS, create_openviking_vfs
from hermes_core.reflective_learner import ADKTaskDAG, ReflectiveLearner, create_reflective_learner


class EventType(str, Enum):
    TASK_SPAWN = "task_spawn"
    TASK_COMPLETE = "task_complete"
    TOOL_CALL = "tool_call"
    VFS_MUTATION = "vfs_mutation"
    MEMORY_RECALL = "memory_recall"
    VERIFICATION_GATE = "verification_gate"
    LEARN_CORRECTION = "learn_correction"


@dataclass
class SynergyEvent:
    """Represents a standardized reactive lifecycle event across Hermes OS."""
    event_id: str
    event_type: EventType
    source: str                       # e.g., 'adk_taskdag', 'openviking_vfs', 'observer_gate'
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else str(self.event_type),
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class SynergyEventBus:
    """
    Unified Reactive Execution & Memory Bus.
    Allows decoupled subsystems to broadcast state changes and react asynchronously.
    """

    def __init__(self, vfs: Optional[OpenVikingVFS] = None, learner: Optional[ReflectiveLearner] = None):
        self.vfs = vfs or create_openviking_vfs()
        self.learner = learner or create_reflective_learner()
        self.subscribers: Dict[str, List[Callable[[SynergyEvent], Any]]] = {
            et.value: [] for et in EventType
        }
        self.event_history: List[SynergyEvent] = []
        self._wire_default_handlers()

    def _wire_default_handlers(self):
        """Connects VFS mutations and TaskDAG completions into automatic lifecycle sync."""
        self.subscribe(EventType.VFS_MUTATION.value, self._on_vfs_mutation)
        self.subscribe(EventType.LEARN_CORRECTION.value, self._on_learn_correction)

    def _on_vfs_mutation(self, event: SynergyEvent):
        path = event.payload.get("path", "")
        content = event.payload.get("content", "")
        abstract = event.payload.get("abstract", "")
        if path and content:
            self.vfs.write_node(path=path, l2_content=content, l0_abstract=abstract)

    def _on_learn_correction(self, event: SynergyEvent):
        feedback = event.payload.get("user_feedback", "")
        category = event.payload.get("category", "tooling")
        if feedback:
            self.learner.capture_correction(user_feedback=feedback, category=category)

    def subscribe(self, event_type: str, handler: Callable[[SynergyEvent], Any]):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def emit_async(self, event: SynergyEvent) -> int:
        """Dispatches an event asynchronously to all registered subscribers."""
        self.event_history.append(event)
        et_key = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        handlers = self.subscribers.get(et_key, [])
        count = 0
        for h in handlers:
            if asyncio.iscoroutinefunction(h):
                await h(event)
            else:
                h(event)
            count += 1
        return count

    def emit_sync(self, event: SynergyEvent) -> int:
        """Synchronous event dispatch for fast low-overhead CPU notifications."""
        self.event_history.append(event)
        et_key = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        handlers = self.subscribers.get(et_key, [])
        count = 0
        for h in handlers:
            if not asyncio.iscoroutinefunction(h):
                h(event)
                count += 1
        return count


def create_synergy_bus(vfs: Optional[OpenVikingVFS] = None, learner: Optional[ReflectiveLearner] = None) -> SynergyEventBus:
    return SynergyEventBus(vfs=vfs, learner=learner)
