"""Hermes Plugin: quorum_audit"""

from .hooks.pre_tool_call import pre_tool_call


def register(ctx=None):
    """Registers plugin quorum_audit into Hermes runtime."""
    if ctx and hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_tool_call", pre_tool_call)


