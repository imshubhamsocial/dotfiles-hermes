"""
Hermes Plugin: agent_os
=======================
Two-Tier Agent OS Standards & Plan.json Decomposition Engine.
"""

from .standards import (
    RuleFile,
    CompiledStandards,
    RuleParser,
    TwoTierStandardsEngine,
    build_two_tier_slot3_injection,
    get_standards_engine,
    reset_standards_engine,
)
from .planner import (
    EngineeringSpec,
    PlanStep,
    Plan,
    SpecFirstPlanner,
    inject_plan_into_slot3,
    enforce_plan_gate_before_edit,
    get_spec_first_planner,
    reset_spec_first_planner,
)

def register(ctx=None):
    """Registers plugin agent_os into Hermes runtime."""
    pass

__all__ = [
    "RuleFile",
    "CompiledStandards",
    "RuleParser",
    "TwoTierStandardsEngine",
    "build_two_tier_slot3_injection",
    "get_standards_engine",
    "reset_standards_engine",
    "EngineeringSpec",
    "PlanStep",
    "Plan",
    "SpecFirstPlanner",
    "inject_plan_into_slot3",
    "enforce_plan_gate_before_edit",
    "get_spec_first_planner",
    "reset_spec_first_planner",
    "register",
]
