"""
Hooks Inventory & Intent-Based Lifecycle Router (Milestone U74)
===============================================================
Manages dynamic registration and execution of lifecycle event hooks:
  - pre_turn: Invoked before intent routing and context assembly
  - post_intent_route: Invoked after bot class selection
  - pre_observer_gate: Invoked before AST verification
  - post_commit: Invoked after successful filesystem mutation
  - on_error: Invoked upon tool or assertion failure
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


HOOK_EVENTS = {"pre_turn", "post_intent_route", "pre_observer_gate", "post_commit", "on_error"}


@dataclass
class HookExecutionContext:
    event_name: str
    session_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    aborted: bool = False
    abort_reason: Optional[str] = None


class HookRouter:
    """Dispatches lifecycle events to registered script or callable hooks."""

    def __init__(self, hooks_dir: Optional[Path] = None):
        self.hooks_dir = hooks_dir or (Path.home() / ".hermes" / "hooks")
        self._handlers: Dict[str, List[Callable[[HookExecutionContext], None]]] = {
            ev: [] for ev in HOOK_EVENTS
        }
        self._ensure_hooks_dir()

    def _ensure_hooks_dir(self) -> None:
        self.hooks_dir.mkdir(parents=True, exist_ok=True)
        for ev in HOOK_EVENTS:
            (self.hooks_dir / ev).mkdir(exist_ok=True)

    def register_handler(self, event_name: str, handler: Callable[[HookExecutionContext], None]) -> None:
        if event_name not in HOOK_EVENTS:
            raise ValueError(f"Invalid hook event '{event_name}'. Must be one of {HOOK_EVENTS}")
        self._handlers[event_name].append(handler)

    def trigger(self, event_name: str, session_id: str = "default", payload: Optional[Dict[str, Any]] = None) -> HookExecutionContext:
        ctx = HookExecutionContext(
            event_name=event_name,
            session_id=session_id,
            payload=payload or {},
        )

        for handler in self._handlers.get(event_name, []):
            try:
                handler(ctx)
                if ctx.aborted:
                    break
            except Exception as e:
                ctx.payload["error"] = str(e)

        return ctx


def create_hook_router(hooks_dir: Optional[Path] = None) -> HookRouter:
    return HookRouter(hooks_dir=hooks_dir)
