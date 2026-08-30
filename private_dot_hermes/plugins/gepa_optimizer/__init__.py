"""GEPA-Lite Optimizer Plugin Entrypoint."""
import sys
from pathlib import Path

try:
    from hermes_core.gepa_optimizer import GEPALiteOptimizer, GEPACandidate, GEPAResult, create_gepa_optimizer
except ImportError:
    for p in [Path.home() / ".hermes/src", Path.home() / ".local/share/chezmoi/private_dot_hermes/src"]:
        if str(p) not in sys.path and p.exists():
            sys.path.insert(0, str(p))
    from hermes_core.gepa_optimizer import GEPALiteOptimizer, GEPACandidate, GEPAResult, create_gepa_optimizer

def register(ctx=None):
    """Registers GEPA optimizer into Hermes plugin runtime."""
    pass
