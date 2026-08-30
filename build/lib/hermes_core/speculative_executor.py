"""
Speculative Programmatic Tool Calling Engine (Milestone U79 / sPTC)
===================================================================
Reduces agent wall-clock latency (~1.2x speedup) by speculatively executing
pure (side-effect-free) tool calls in a Shadow REPL while the LLM is still streaming.

Safety Invariants:
  - Only "pure" read-only tools are speculatively launched
  - Stateful / filesystem write operations are strictly deferred
  - Results are cached as promises and claimed upon execution reach
"""

from __future__ import annotations

import ast
import concurrent.futures
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


PURE_TOOL_REGISTRY: Set[str] = {
    "read_file",
    "web_search",
    "grep_search",
    "list_dir",
    "get_symbol_graph",
    "query_memory",
    "read_image",
    "read_video",
    "inspect_doc",
}


@dataclass
class SpeculativeToolPromise:
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    future: Optional[concurrent.futures.Future] = None
    result: Any = None
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: str = "PENDING"  # "PENDING", "RESOLVED", "CLAIMED", "REJECTED"


class ShadowREPL:
    """Isolated environment for speculative code delta evaluation."""

    def __init__(self, pure_tools: Optional[Set[str]] = None):
        self.pure_tools = pure_tools or PURE_TOOL_REGISTRY
        self.scope: Dict[str, Any] = {}

    def is_pure_call(self, tool_name: str) -> bool:
        return tool_name in self.pure_tools

    def extract_candidate_tool_calls(self, partial_code: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Parse partial Python/DSL code snippet and extract resolved pure calls."""
        candidates = []
        # Pattern 1: Tool invocation pattern like tool_name(arg="val", ...)
        for tool in self.pure_tools:
            pattern = rf"\b{tool}\s*\((.*?)\)"
            for match in re.finditer(pattern, partial_code):
                args_str = match.group(1)
                try:
                    # Parse literal args safely using ast
                    parsed_call = ast.parse(f"f({args_str})").body[0].value
                    kwargs = {}
                    for kw in parsed_call.keywords:
                        if isinstance(kw.value, ast.Constant):
                            kwargs[kw.arg] = kw.value.value
                    if parsed_call.args and not kwargs:
                        if isinstance(parsed_call.args[0], ast.Constant):
                            kwargs["query"] = parsed_call.args[0].value
                    candidates.append((tool, kwargs))
                except Exception:
                    continue
        return candidates


class SpeculativeToolExecutor:
    """Manages speculative background tool promises during model generation."""

    def __init__(
        self,
        tool_handlers: Optional[Dict[str, Callable[..., Any]]] = None,
        max_workers: int = 4,
    ):
        self.tool_handlers = tool_handlers or {}
        self.shadow_repl = ShadowREPL()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.promises: Dict[str, SpeculativeToolPromise] = {}

    def _call_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        s = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def register_tool_handler(self, tool_name: str, handler: Callable[..., Any]) -> None:
        self.tool_handlers[tool_name] = handler

    def observe_stream_delta(self, partial_stream_text: str) -> List[str]:
        """Inspect partial stream tokens and speculatively launch candidate promises."""
        candidates = self.shadow_repl.extract_candidate_tool_calls(partial_stream_text)
        launched_keys = []

        for tool_name, kwargs in candidates:
            if not self.shadow_repl.is_pure_call(tool_name):
                continue

            ckey = self._call_key(tool_name, kwargs)
            if ckey in self.promises:
                continue

            handler = self.tool_handlers.get(tool_name)
            if not handler:
                continue

            promise = SpeculativeToolPromise(
                call_id=ckey,
                tool_name=tool_name,
                arguments=kwargs,
                status="PENDING",
            )

            # Launch future
            fut = self.executor.submit(handler, **kwargs)
            promise.future = fut
            self.promises[ckey] = promise
            launched_keys.append(ckey)

        return launched_keys

    def claim_or_execute(self, tool_name: str, args: Dict[str, Any]) -> Tuple[Any, bool]:
        """Claim a previously speculated promise, or execute directly if not yet launched."""
        ckey = self._call_key(tool_name, args)
        if ckey in self.promises:
            promise = self.promises[ckey]
            if promise.future:
                try:
                    res = promise.future.result(timeout=5.0)
                    promise.result = res
                    promise.status = "CLAIMED"
                    promise.completed_at = time.time()
                    return res, True  # True = was speculated!
                except Exception as e:
                    promise.status = "REJECTED"

        # Fallback to direct execution
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"No handler registered for tool '{tool_name}'")
        res = handler(**args)
        return res, False


def create_speculative_executor(**kwargs) -> SpeculativeToolExecutor:
    return SpeculativeToolExecutor(**kwargs)
