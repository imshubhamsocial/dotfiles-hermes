from typing import Callable, Union, List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Define core types as requested
AgentFunction = Callable[..., Union[str, "Agent", "Result", Dict[str, Any]]]

class Result(BaseModel):
    value: str = ""
    agent: Optional["Agent"] = None
    context_variables: Dict[str, Any] = Field(default_factory=dict)

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "qwen3.8-4b"
    instructions: Union[str, Callable[[Dict[str, Any]], str]] = "You are a helpful agent."
    functions: List[AgentFunction] = Field(default_factory=list)
    tool_choice: Union[str, None] = None
    parallel_tool_calls: bool = False
    temperature: float = 0.2
    max_tokens: int = 4096

    
    def get_instructions(self, context: Dict[str, Any]) -> str:
        if callable(self.instructions):
            return self.instructions(context)
        return self.instructions

class Response(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    agent: Optional["Agent"] = None
    context_variables: Dict[str, Any] = Field(default_factory=dict)