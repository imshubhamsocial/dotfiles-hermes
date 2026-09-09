"""Hermes Plugin: gepa_optimizer"""
import sys
from pathlib import Path

for p in [Path.home() / ".hermes/src", Path.home() / ".local/share/chezmoi/private_dot_hermes/src"]:
    if str(p) not in sys.path and p.exists():
        sys.path.insert(0, str(p))

from .hooks.on_session_end import on_session_end


def register(ctx=None):
    """Registers plugin gepa_optimizer into Hermes runtime."""
    if ctx and hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_end", on_session_end)

