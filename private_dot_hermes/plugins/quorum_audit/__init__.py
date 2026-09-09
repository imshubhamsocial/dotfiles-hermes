"""Hermes Plugin: quorum_audit"""
import sys
from pathlib import Path

for p in [Path.home() / ".hermes/src", Path.home() / ".local/share/chezmoi/private_dot_hermes/src"]:
    if str(p) not in sys.path and p.exists():
        sys.path.insert(0, str(p))

from .hooks.pre_tool_call import pre_tool_call


def register(ctx=None):
    """Registers plugin quorum_audit into Hermes runtime."""
    if ctx and hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_tool_call", pre_tool_call)

