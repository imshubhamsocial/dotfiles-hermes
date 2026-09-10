"""
Google Agent Development Kit (ADK) Custom Agent Wrapper
======================================================
Domain 7 / Milestone D7-13:
Wraps HermesOrchestrator as a Google ADK CustomAgent (subclass of BaseAgent).

Bridges:
  1. Google ADK Session, Runner, InvocationContext, and Event streams.
  2. Hermes multi-agent Swarm engine, role-based capability masks,
     and cognitive governor execution loops.
  3. Seamless functional agent transfers via ADK's transfer_to_agent action.
"""

from __future__ import annotations

import asyncio
import copy
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    from google.adk.agents import BaseAgent
    from google.adk.events import Event, EventActions
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    class BaseAgent:  # type: ignore[no-redef]
        """Fallback when google-adk is not installed."""
        def __init__(self, *args, **kwargs):
            pass
    class Event:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass
    EventActions = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

from pydantic import Field

from .agent import Agent, Response, Result
from .swarm_engine import HermesOrchestrator


def adk_content_to_str(content: Any) -> str:
    """Extract plain text string from an ADK Content object or text part."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if hasattr(content, "parts") and content.parts:
        text_parts = []
        for p in content.parts:
            if hasattr(p, "text") and p.text:
                text_parts.append(p.text)
        return "".join(text_parts)
    return str(content)


def hermes_response_to_adk_event(response: Response, author: str) -> Event:
    """Convert a Hermes Response into an ADK Event."""
    final_content = ""
    if response.messages:
        for msg in reversed(response.messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                final_content = msg["content"]
                break
        if not final_content and response.messages:
            final_content = response.messages[-1].get("content", "")

    actions = EventActions(
        state_delta=copy.deepcopy(response.context_variables or {})
    )
    if response.agent and response.agent.name != author:
        actions.transfer_to_agent = response.agent.name

    return Event(
        author=author,
        message=final_content,
        actions=actions
    )


class HermesADKCustomAgent(BaseAgent):
    """
    Google ADK CustomAgent wrapping HermesOrchestrator.

    Integrates Hermes's local model execution loop, dynamic capability
    filtering, and cognitive governor stack directly into Google ADK workflows,
    Runners, SequentialAgents, and Swarms.
    """

    orchestrator: Optional[Any] = Field(
        default=None,
        description="Underlying HermesOrchestrator instance (calls local llama-server or OpenAI-compatible backend)"
    )
    hermes_agent: Optional[Any] = Field(
        default=None,
        description="Domain-specialized Hermes Agent configuration"
    )
    instructions: Optional[str] = Field(
        default=None,
        description="System prompt / role instructions for the agent"
    )
    preset: Optional[str] = Field(
        default=None,
        description="Optional Hermes execution preset (e.g., 'minimal' for fast bash/patch tool loops)"
    )
    max_turns: int = Field(
        default=25,
        description="Maximum turns permitted in a single orchestrator invocation"
    )
    verbose: bool = Field(
        default=False,
        description="Enable debug printing during model execution"
    )
    auto_handoff: bool = Field(
        default=True,
        description="Automatically propagate Swarm agent transfers to ADK transfer_to_agent actions"
    )

    def _get_or_create_orchestrator(self) -> HermesOrchestrator:
        if self.orchestrator is not None:
            return self.orchestrator
        return HermesOrchestrator()

    def _get_or_create_agent(self) -> Agent:
        if self.hermes_agent is not None:
            if self.instructions and not getattr(self.hermes_agent, "instructions", None):
                self.hermes_agent.instructions = self.instructions
            return self.hermes_agent
        return Agent(
            name=self.name,
            instructions=self.instructions or self.description or "You are an autonomous Hermes engineering agent."
        )

    def _reconstruct_messages(self, ctx: Any) -> List[Dict[str, Any]]:
        """Reconstruct message history from ADK session events and current user content."""
        messages: List[Dict[str, Any]] = []

        # 1. Read prior session history if available
        if hasattr(ctx, "session") and getattr(ctx.session, "events", None):
            for ev in ctx.session.events:
                if not ev.content:
                    continue
                text = adk_content_to_str(ev.content)
                if not text:
                    continue
                role = "user" if ev.author in ("user", "", None) else "assistant"
                messages.append({"role": role, "content": text})

        # 2. Append current user input if present and not duplicate of last message
        current_input = ""
        if hasattr(ctx, "user_content") and ctx.user_content:
            current_input = adk_content_to_str(ctx.user_content)
        elif hasattr(ctx, "message") and ctx.message:
            current_input = adk_content_to_str(ctx.message)

        if current_input:
            if not messages or messages[-1].get("content") != current_input:
                messages.append({"role": "user", "content": current_input})

        # Fallback if empty
        if not messages:
            messages.append({"role": "user", "content": "Execute task."})

        return messages

    def _extract_context_variables(self, ctx: Any) -> Dict[str, Any]:
        """Extract context variables from ADK session state."""
        ctx_vars: Dict[str, Any] = {}
        if hasattr(ctx, "session") and getattr(ctx.session, "state", None):
            ctx_vars.update(ctx.session.state)
        elif hasattr(ctx, "state") and ctx.state:
            ctx_vars.update(dict(ctx.state))
        return ctx_vars

    async def _run_async_impl(self, ctx: Any) -> AsyncGenerator[Event, None]:
        """
        Execute an ADK agent turn backed by HermesOrchestrator.
        Runs asynchronously via to_thread to keep ADK non-blocking.
        """
        messages = self._reconstruct_messages(ctx)
        context_vars = self._extract_context_variables(ctx)
        orch = self._get_or_create_orchestrator()
        active_hermes_agent = self._get_or_create_agent()

        # Run Hermes loop in background thread
        response: Response = await asyncio.to_thread(
            orch.run,
            agent=active_hermes_agent,
            messages=messages,
            context_variables=context_vars,
            max_turns=self.max_turns,
            verbose=self.verbose,
            preset=self.preset
        )

        # Convert Response to ADK Event
        event = hermes_response_to_adk_event(response, author=self.name)
        yield event
