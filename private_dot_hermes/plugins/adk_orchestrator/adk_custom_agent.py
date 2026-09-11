from __future__ import annotations
import asyncio
import copy
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import Field

try:
    from google.adk.agents import BaseAgent
    from google.adk.events import Event, EventActions
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    class BaseAgent:
        def __init__(self, *args, **kwargs): pass
    class Event:
        def __init__(self, *args, **kwargs): pass
    EventActions = None
    types = None

try:
    from .agent import Agent, Response, Result
    from .swarm_engine import HermesOrchestrator
except (ImportError, ValueError):
    from agent import Agent, Response, Result
    from swarm_engine import HermesOrchestrator

def adk_content_to_str(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if hasattr(content, "parts") and content.parts:
        text_parts = []
        for p in content.parts:
            if hasattr(p, "text") and p.text:
                text_parts.append(str(p.text))
        if text_parts:
            return "".join(text_parts)
    return str(content)

def hermes_response_to_adk_event(response: Response, author: str) -> Event:
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
    if response.agent and getattr(response.agent, "name", None) != author:
        actions.transfer_to_agent = response.agent.name

    return Event(
        author=author,
        message=final_content,
        actions=actions
    )

class HermesADKCustomAgent(BaseAgent):
    orchestrator: Optional[Any] = Field(default=None)
    hermes_agent: Optional[Any] = Field(default=None)
    instructions: Optional[str] = Field(default=None)
    preset: Optional[str] = Field(default=None)
    max_turns: int = Field(default=25)
    verbose: bool = Field(default=False)
    auto_handoff: bool = Field(default=True)

    hermes_response_to_adk_event = staticmethod(hermes_response_to_adk_event)
    adk_content_to_str = staticmethod(adk_content_to_str)

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
        messages: List[Dict[str, Any]] = []
        if hasattr(ctx, "session") and getattr(ctx.session, "events", None):
            for ev in ctx.session.events:
                if not ev.content:
                    continue
                text = adk_content_to_str(ev.content)
                if not text:
                    continue
                role = "user" if ev.author in ("user", "", None) else "assistant"
                messages.append({"role": role, "content": text})
        current_input = ""
        if hasattr(ctx, "user_content") and ctx.user_content:
            current_input = adk_content_to_str(ctx.user_content)
        elif hasattr(ctx, "message") and ctx.message:
            current_input = adk_content_to_str(ctx.message)
        if current_input:
            if not messages or messages[-1].get("content") != current_input:
                messages.append({"role": "user", "content": current_input})
        if not messages:
            messages.append({"role": "user", "content": "Execute task."})
        return messages

    def _extract_context_variables(self, ctx: Any) -> Dict[str, Any]:
        ctx_vars: Dict[str, Any] = {}
        if isinstance(ctx, dict):
            if "state" in ctx and isinstance(ctx["state"], dict):
                ctx_vars.update(ctx["state"])
            elif "context_variables" in ctx and isinstance(ctx["context_variables"], dict):
                ctx_vars.update(ctx["context_variables"])
        if hasattr(ctx, "session") and getattr(ctx.session, "state", None):
            ctx_vars.update(ctx.session.state)
        elif hasattr(ctx, "state") and ctx.state:
            ctx_vars.update(dict(ctx.state))
        return ctx_vars

    async def _run_async_impl(self, ctx: Any) -> AsyncGenerator[Event, None]:
        messages = self._reconstruct_messages(ctx)
        context_vars = self._extract_context_variables(ctx)
        orch = self._get_or_create_orchestrator()
        active_hermes_agent = self._get_or_create_agent()
        response: Response = await asyncio.to_thread(
            orch.run,
            agent=active_hermes_agent,
            messages=messages,
            context_variables=context_vars,
            max_turns=self.max_turns,
            verbose=self.verbose,
            preset=self.preset
        )
        event = hermes_response_to_adk_event(response, author=self.name)
        yield event