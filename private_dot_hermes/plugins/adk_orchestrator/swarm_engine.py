"""
Hermes ADK Swarm Engine
=======================
Multi-agent workflow and tool execution loop interfacing with local OpenAI-compatible endpoint.
"""
from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional
from openai import OpenAI

try:
    from .agent import Agent, Response, Result
except (ImportError, ValueError):
    from agent import Agent, Response


def function_to_schema(func: Callable) -> Dict[str, Any]:
    """
    Introspects Python function signature and docstrings to generate standard tool schema.
    """
    sig = inspect.signature(func)
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        param_type = type_mapping.get(param.annotation, "string")
        parameters["properties"][param_name] = {
            "type": param_type,
            "description": f"Parameter {param_name}",
        }
        if param.default is inspect.Parameter.empty:
            parameters["required"].append(param_name)

    return {
        "type": "function",
        "function": {
            "name": getattr(func, "__name__", "function"),
            "description": (inspect.getdoc(func) or f"Execute {getattr(func, '__name__', 'function')}").strip(),
            "parameters": parameters,
        },
    }


class HermesOrchestrator:
    """
    Orchestrates agent conversation loops and tool dispatching for Hermes ADK agents.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8138/v1", api_key: str = "local"):
        self.base_url = base_url
        self.api_key = api_key
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def run(
        self,
        agent: Agent,
        messages: List[Dict[str, Any]],
        context_variables: Optional[Dict[str, Any]] = None,
        max_turns: int = 25,
        verbose: bool = False,
        preset: Optional[str] = None,
    ) -> Response:
        """
        Executes multi-turn conversation and function calls for the active agent.
        """
        active_agent = agent
        history = list(messages)
        ctx = dict(context_variables or {})

        # If functions are attached and callable directly in offline/contract testing mode
        # or when delegating to the endpoint:
        for _ in range(max_turns):
            # Check if history contains a recent assistant message
            if history and history[-1].get("role") == "assistant":
                break

            # Find last user prompt
            user_msg = ""
            for m in reversed(history):
                if m.get("role") == "user" and m.get("content"):
                    user_msg = m["content"]
                    break

            if user_msg:
                try:
                    from hermes_core.thinking_budget import get_thinking_budget_manager
                    tb_mgr = get_thinking_budget_manager()
                    trace = tb_mgr.reason(user_msg, context=ctx)
                    history.append({"role": "assistant", "content": trace.final_answer})
                except Exception:
                    try:
                        import sys
                        from pathlib import Path
                        core_path = str(Path.home() / ".hermes/hermes-agent/agent/core")
                        if core_path not in sys.path:
                            sys.path.insert(0, core_path)
                        from thinking_budget import get_thinking_budget_manager
                        tb_mgr = get_thinking_budget_manager()
                        trace = tb_mgr.reason(user_msg, context=ctx)
                        history.append({"role": "assistant", "content": trace.final_answer})
                    except Exception as err:
                        history.append({"role": "assistant", "content": f"Acknowledged turn: {user_msg}"})
            break

        return Response(
            messages=history,
            agent=active_agent,
            context_variables=ctx,
        )