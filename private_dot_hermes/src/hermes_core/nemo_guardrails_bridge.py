"""
Hermes Core Shim: nemo_guardrails_bridge
========================================
Thin pass-through adapter delegating to plugins.nemo_guardrails.
Preserves backward-compatible imports for hermes_core.
"""

import sys
from pathlib import Path

for p in [Path.home() / ".hermes", Path.cwd() / ".hermes", Path.home() / ".local/share/chezmoi/private_dot_hermes"]:
    if str(p) not in sys.path and p.exists():
        sys.path.insert(0, str(p))

from plugins.nemo_guardrails import (
    CRITICAL_COMMAND_PATTERNS,
    NEMO_GUARDRAILS_AVAILABLE,
    SENSITIVE_SECRET_PATTERNS,
    GuardrailVerdict,
    HermesGuardrailsEngine,
    audit_input_with_guardrails,
    get_guardrails_config_path,
    get_guardrails_engine,
    sanitize_output_with_guardrails,
)

__all__ = [
    "GuardrailVerdict",
    "HermesGuardrailsEngine",
    "get_guardrails_engine",
    "get_guardrails_config_path",
    "audit_input_with_guardrails",
    "sanitize_output_with_guardrails",
    "NEMO_GUARDRAILS_AVAILABLE",
    "CRITICAL_COMMAND_PATTERNS",
    "SENSITIVE_SECRET_PATTERNS",
]
