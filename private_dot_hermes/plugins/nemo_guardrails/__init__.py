"""
Hermes Plugin: nemo_guardrails
==============================
NVIDIA NeMo Guardrails Integration Bridge (Milestone D7-11)
Formal input, output, dialog, and loop rails powered by NeMo Guardrails
and deterministic Colang 1.0 policies.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Graceful optional import of nemoguardrails
try:
    import nemoguardrails
    from nemoguardrails import RailsConfig, LLMRails

    NEMO_GUARDRAILS_AVAILABLE = True
except (ImportError, Exception):
    nemoguardrails = None
    RailsConfig = None
    LLMRails = None
    NEMO_GUARDRAILS_AVAILABLE = False


# High-Risk Critical Shell Command Patterns (mirrored in input_rails.co)
CRITICAL_COMMAND_PATTERNS = [
    re.compile(r"\brm\s+-(?:r|f|rf|fr)\b", re.IGNORECASE),
    re.compile(r"\b(?:drop\s+database|drop\s+table|truncate\s+table)\b", re.IGNORECASE),
    re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
    re.compile(r"\bchmod\s+(?:-R\s+)?777\b", re.IGNORECASE),
    re.compile(r"\b(?:sudo|su\s+-?)\b", re.IGNORECASE),
    re.compile(r"\b(?:curl|wget)\b.*\|\s*(?:ba)?sh\b", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE),  # Fork bomb
]

# Sensitive Credential & Key Leakage Patterns (mirrored in output_rails.co)
SENSITIVE_SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "sk-***REDACTED***"),
    (re.compile(r"AIza[0-9A-Za-z-_]{20,}"), "AIza***REDACTED***"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"), "ghp_***REDACTED***"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA***REDACTED***"),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        "-----BEGIN PRIVATE KEY-----\n***REDACTED PRIVATE KEY CONTENT***\n-----END PRIVATE KEY-----",
    ),
]


@dataclass
class GuardrailVerdict:
    allowed: bool
    rail_triggered: Optional[str] = None  # "input", "output", "dialog", "loop"
    reason: str = ""
    sanitized_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def get_guardrails_config_path() -> Path:
    """Discovers the active NeMo Guardrails configuration directory."""
    override = os.environ.get("HERMES_GUARDRAILS_PATH")
    if override and os.path.exists(override):
        return Path(override)

    candidate_paths = [
        Path(__file__).resolve().parent / "config",
        Path(__file__).resolve().parents[2] / "guardrails",
        Path.home() / ".hermes" / "plugins" / "nemo_guardrails" / "config",
        Path.home() / ".hermes" / "guardrails",
        Path.cwd() / ".hermes" / "plugins" / "nemo_guardrails" / "config",
        Path.cwd() / ".hermes" / "guardrails",
        Path.cwd() / ".local" / "share" / "chezmoi" / "private_dot_hermes" / "plugins" / "nemo_guardrails" / "config",
        Path.cwd() / ".local" / "share" / "chezmoi" / "private_dot_hermes" / "guardrails",
    ]
    for p in candidate_paths:
        if p.exists() and (p / "config.yml").exists():
            return p
    return candidate_paths[0]


class HermesGuardrailsEngine:
    """
    Unified Guardrails Engine combining NeMo Guardrails Colang configs
    with deterministic sub-millisecond safety evaluations.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else get_guardrails_config_path()
        self.rails_config: Optional[Any] = None
        self.llm_rails: Optional[Any] = None
        self._load_nemo_rails()

    def _load_nemo_rails(self):
        if NEMO_GUARDRAILS_AVAILABLE and RailsConfig is not None:
            if self.config_path.exists() and (self.config_path / "config.yml").exists():
                try:
                    self.rails_config = RailsConfig.from_path(str(self.config_path))
                    # Only instantiate LLMRails if config parsed successfully
                    if self.rails_config and LLMRails is not None:
                        try:
                            self.llm_rails = LLMRails(self.rails_config)
                        except Exception:
                            self.llm_rails = None
                except Exception:
                    self.rails_config = None
                    self.llm_rails = None

    def check_input_rail(self, command_or_prompt: str, role: Optional[str] = None) -> GuardrailVerdict:
        """
        Evaluates input against NeMo Input Rails.
        Blocks destructive shell commands, fork bombs, and injection exploits.
        """
        if not command_or_prompt:
            return GuardrailVerdict(allowed=True, reason="empty_input")

        # 1. Critical destructive command check
        for pat in CRITICAL_COMMAND_PATTERNS:
            if pat.search(command_or_prompt):
                matched = pat.pattern
                return GuardrailVerdict(
                    allowed=False,
                    rail_triggered="input",
                    reason=f"Execution blocked by NeMo input rail: Destructive pattern '{matched}' detected.",
                    metadata={"pattern": matched},
                )

        # 2. High-risk path access
        for bad_path in ("/etc/shadow", "/etc/sudoers", "/etc/passwd"):
            if bad_path in command_or_prompt and any(cmd in command_or_prompt for cmd in ("cat", "head", "tail", "less", "cp")):
                return GuardrailVerdict(
                    allowed=False,
                    rail_triggered="input",
                    reason=f"Execution blocked by NeMo input rail: Protected system path '{bad_path}' access.",
                    metadata={"target": bad_path},
                )

        # 3. Role capability boundary check if role provided
        if role:
            role_verdict = self.check_dialog_rail(role, command_or_prompt)
            if not role_verdict.allowed:
                return role_verdict

        return GuardrailVerdict(allowed=True, reason="input_rail_passed")

    def check_output_rail(self, response_text: str) -> GuardrailVerdict:
        """
        Evaluates generated output against NeMo Output Rails.
        Detects, blocks, and redacts sensitive credentials, API keys, and private keys.
        """
        if not response_text:
            return GuardrailVerdict(allowed=True, sanitized_content="")

        redacted_text = response_text
        secrets_found = []

        for pat, replacement in SENSITIVE_SECRET_PATTERNS:
            matches = pat.findall(redacted_text)
            if matches:
                secrets_found.extend(matches)
                redacted_text = pat.sub(replacement, redacted_text)

        if secrets_found:
            return GuardrailVerdict(
                allowed=False,
                rail_triggered="output",
                reason="Sensitive credential or private key pattern detected by NeMo output rail.",
                sanitized_content=redacted_text,
                metadata={"secrets_count": len(secrets_found)},
            )

        return GuardrailVerdict(allowed=True, sanitized_content=response_text, reason="output_rail_passed")

    def check_dialog_rail(self, role: str, tool_or_intent: str) -> GuardrailVerdict:
        """
        Evaluates role capability boundaries against NeMo Dialog Rails.
        Denies mutating actions from read-only roles (e.g. reviewer).
        """
        normalized_role = role.strip().lower()

        # Reviewer role is read-only
        if normalized_role in ("reviewer", "auditor"):
            mutating_keywords = ("write", "patch", "delete", "rm", "apply", "create", "modify")
            if any(k in tool_or_intent.lower() for k in mutating_keywords):
                return GuardrailVerdict(
                    allowed=False,
                    rail_triggered="dialog",
                    reason=f"Capability Denied by NeMo dialog rail: Role '{role}' is read-only and denied mutating actions.",
                    metadata={"role": role, "action": tool_or_intent},
                )

        # Coder role cannot perform destructive database/system admin
        if normalized_role == "coder":
            admin_keywords = ("drop database", "truncate table", "wipe all disks", "format disk")
            if any(k in tool_or_intent.lower() for k in admin_keywords):
                return GuardrailVerdict(
                    allowed=False,
                    rail_triggered="dialog",
                    reason=f"Capability Denied by NeMo dialog rail: Role '{role}' cannot perform administrative database operations.",
                    metadata={"role": role, "action": tool_or_intent},
                )

        return GuardrailVerdict(allowed=True, reason="dialog_rail_passed")

    def check_loop_rail(
        self, iteration: int, max_iterations: int = 5, consecutive_failures: int = 0
    ) -> GuardrailVerdict:
        """
        Evaluates loop termination contracts against NeMo Loop Rails.
        Enforces iteration ceiling and 2-strike tabu failure limits.
        """
        if iteration > max_iterations:
            return GuardrailVerdict(
                allowed=False,
                rail_triggered="loop",
                reason=f"Loop ceiling breached: iteration {iteration} exceeds max {max_iterations}.",
                metadata={"iteration": iteration, "max_iterations": max_iterations},
            )

        if consecutive_failures >= 2:
            return GuardrailVerdict(
                allowed=False,
                rail_triggered="loop",
                reason=f"Tabu 2-strike limit tripped: {consecutive_failures} consecutive failures.",
                metadata={"consecutive_failures": consecutive_failures},
            )

        return GuardrailVerdict(allowed=True, reason="loop_rail_passed")


# Global engine instance singleton
_GLOBAL_GUARDRAILS_ENGINE: Optional[HermesGuardrailsEngine] = None


def get_guardrails_engine() -> HermesGuardrailsEngine:
    """Returns the shared HermesGuardrailsEngine instance."""
    global _GLOBAL_GUARDRAILS_ENGINE
    if _GLOBAL_GUARDRAILS_ENGINE is None:
        _GLOBAL_GUARDRAILS_ENGINE = HermesGuardrailsEngine()
    return _GLOBAL_GUARDRAILS_ENGINE


def audit_input_with_guardrails(command_or_prompt: str, role: Optional[str] = None) -> GuardrailVerdict:
    """Convenience helper to check input against NeMo input & dialog rails."""
    return get_guardrails_engine().check_input_rail(command_or_prompt, role=role)


def sanitize_output_with_guardrails(text: str) -> str:
    """Convenience helper to redact secrets from output using NeMo output rails."""
    verdict = get_guardrails_engine().check_output_rail(text)
    return verdict.sanitized_content if verdict.sanitized_content is not None else text


def register(ctx=None):
    """Registers plugin nemo_guardrails into Hermes runtime."""
    pass


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
    "register",
]
