"""Hermes Plugin: capability_guard"""

from .capability_masks import (
    ROLE_POLICIES,
    ROLE_SCHEMAS,
    ROLE_CAPABILITIES,
    get_tool_schema,
    resolve_role,
    allowed_for,
    check_tool,
    mask_functions,
    apply_to_agent,
    validate_security_policy_path,
    validate_security_policy_command,
    get_schema_for_role,
)

def register(ctx=None):
    """Registers plugin capability_guard into Hermes runtime."""
    pass

__all__ = [
    "ROLE_POLICIES",
    "ROLE_SCHEMAS",
    "ROLE_CAPABILITIES",
    "get_tool_schema",
    "resolve_role",
    "allowed_for",
    "check_tool",
    "mask_functions",
    "apply_to_agent",
    "validate_security_policy_path",
    "validate_security_policy_command",
    "get_schema_for_role",
    "register",
]
