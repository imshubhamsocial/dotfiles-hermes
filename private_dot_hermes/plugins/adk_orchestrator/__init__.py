"""Hermes Plugin: adk_orchestrator"""

from .agent import Agent, Response, Result, AgentFunction
from .adk_custom_agent import (
    HermesADKCustomAgent,
    adk_content_to_str,
    hermes_response_to_adk_event,
)
from .swarm_engine import HermesOrchestrator, function_to_schema

def register(ctx=None):
    """Registers plugin adk_orchestrator into Hermes runtime."""
    pass

__all__ = [
    "Agent",
    "Response",
    "Result",
    "AgentFunction",
    "HermesADKCustomAgent",
    "adk_content_to_str",
    "hermes_response_to_adk_event",
    "HermesOrchestrator",
    "function_to_schema",
    "register",
]
