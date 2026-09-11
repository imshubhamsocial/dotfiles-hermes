"""
Hermes Plugin: capability_guard
==============================
Role-Based Capability Masks and Tool Security Policy Enforcement,
tightly integrated with NVIDIA NeMo Guardrails execution rails and Google ADK.
"""

from __future__ import annotations

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
    if not ctx:
        return True

    if hasattr(ctx, "register_hook"):
        def capability_pre_tool_call(tool_name: str, args: dict | None = None, **kwargs):
            # 1. Shell command safety via NeMo input rails
            if tool_name in ("execute_command", "terminal", "bash", "execute"):
                cmd = (args or {}).get("command") or (args or {}).get("cmd") or ""
                if cmd:
                    valid, reason = validate_security_policy_command(cmd)
                    if not valid:
                        return {"action": "block", "message": f"Execution blocked: {reason}"}

            # 2. File mutation path protection
            if tool_name in ("write_file", "patch_file", "delete_file"):
                fp = (args or {}).get("filepath") or (args or {}).get("path") or ""
                if fp:
                    valid, reason = validate_security_policy_path(fp, is_write=True)
                    if not valid:
                        return {"action": "block", "message": f"Access blocked: {reason}"}

            return {}

        ctx.register_hook("pre_tool_call", capability_pre_tool_call)

    return True


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
