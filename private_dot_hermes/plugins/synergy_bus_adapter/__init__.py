"""Hermes Plugin: synergy_bus_adapter"""
import sys
from pathlib import Path

for p in [Path.home() / ".hermes/src", Path.home() / ".local/share/chezmoi/private_dot_hermes/src"]:
    if str(p) not in sys.path and p.exists():
        sys.path.insert(0, str(p))

def register(ctx=None):
    """Registers plugin synergy_bus_adapter into Hermes runtime."""
    pass
