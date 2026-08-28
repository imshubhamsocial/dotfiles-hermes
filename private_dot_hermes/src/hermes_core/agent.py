"""
Hermes Core Agent Primitives (Ground-Up Re-architecture)
=======================================================
Combines:
  1. OpenAI Swarm Type System (Pydantic Agent, Result, Response).
  2. Dynamic callable instructions with context_variables.
  3. Seamless functional agent transfers.
"""

from typing import List, Callable, Union, Optional, Any, Dict
from pydantic import BaseModel, Field

AgentFunction = Callable[..., Union[str, "Agent", "Result", Dict[str, Any]]]


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "qwen3.8-4b"
    instructions: Union[str, Callable[[Dict[str, Any]], str]] = "You are a helpful engineering agent."
    functions: List[AgentFunction] = Field(default_factory=list)
    tool_choice: Optional[str] = None
    parallel_tool_calls: bool = False
    temperature: float = 0.2
    max_tokens: int = 4096

    def get_instructions(self, context: Dict[str, Any]) -> str:
        if callable(self.instructions):
            return self.instructions(context)
        return self.instructions


class Result(BaseModel):
    """Encapsulates the return value of an agent tool execution."""
    value: str = ""
    agent: Optional[Agent] = None
    context_variables: Dict[str, Any] = Field(default_factory=dict)


class Response(BaseModel):
    """Final output emitted from an orchestrated execution turn."""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    agent: Optional[Agent] = None
    context_variables: Dict[str, Any] = Field(default_factory=dict)
