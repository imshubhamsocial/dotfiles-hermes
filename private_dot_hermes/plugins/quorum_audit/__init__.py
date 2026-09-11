"""
Hermes Plugin: quorum_audit (Mixture-of-Agents & Consensus Audit)
================================================================
Phase III.1 implementation of true MoA loop:
  - 3 parallel proposer instances (Analytical, Creative, Red-Team Critic)
  - Logprob-based confidence estimation & disagreement scoring
  - Aggregator synthesis into unified consensus response
  - Disagreement escalation to HITL gateway
  - Invariant preservation: Maker != Verifier (Author != Auditor)
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

from .hooks.pre_tool_call import pre_tool_call

# Dynamically ensure hermes-agent/agent/core is in python path
core_dir = os.path.expanduser("~/.hermes/hermes-agent/agent/core")
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

try:
    from quorum_moa import MoAEngine, MoAResult, run_moa_debate, get_moa_engine
    from agent_protocol import AgentMessage
except ImportError:
    try:
        from hermes_agent.agent.core.quorum_moa import MoAEngine, MoAResult, run_moa_debate, get_moa_engine
        from hermes_agent.agent.core.agent_protocol import AgentMessage
    except ImportError:
        pass


def run_moa_consensus(query: str, context: Optional[str] = None) -> MoAResult:
    """Plugin entrypoint for executing Mixture-of-Agents consensus deliberation."""
    engine = get_moa_engine()
    return engine.run_moa(query=query, context=context)


def register(ctx=None):
    """Registers plugin quorum_audit into Hermes runtime."""
    if ctx and hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_tool_call", pre_tool_call)
        if hasattr(ctx, "register_capability"):
            ctx.register_capability("moa_consensus", run_moa_consensus)


__all__ = [
    "pre_tool_call",
    "run_moa_consensus",
    "run_moa_debate",
    "MoAEngine",
    "MoAResult",
    "get_moa_engine",
    "register",
]
