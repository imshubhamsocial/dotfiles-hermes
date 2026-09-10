"""Hermes Plugin: gepa_optimizer"""

from .hooks.on_session_end import on_session_end


def register(ctx=None):
    """Registers plugin gepa_optimizer into Hermes runtime."""
    if ctx and hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_end", on_session_end)


