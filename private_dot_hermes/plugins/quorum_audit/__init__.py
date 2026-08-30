"""Quorum Audit Gate Plugin Entrypoint."""
import sys
from pathlib import Path

try:
    from hermes_core.quorum_gate import QuorumAuditGate, QuorumAuditReceipt, BlastRadius
except ImportError:
    for p in [Path.home() / ".hermes/src", Path.home() / ".local/share/chezmoi/private_dot_hermes/src"]:
        if str(p) not in sys.path and p.exists():
            sys.path.insert(0, str(p))
    from hermes_core.quorum_gate import QuorumAuditGate, QuorumAuditReceipt, BlastRadius

def register(ctx=None):
    """Registers Quorum audit gate into Hermes plugin runtime."""
    pass
