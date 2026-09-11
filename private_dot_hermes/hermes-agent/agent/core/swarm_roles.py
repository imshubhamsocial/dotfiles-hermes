"""
Specialized Role Swarm Loader & Registry (Phase III.2)
======================================================
Loads and configures specialized Hermes swarm personas:
  - Director (temp 0.1, top-p 0.9, Planning, decomposition)
  - Researcher (temp 0.7, top-p 0.95, Hypothesis generation)
  - Implementer (temp 0.2, top-p 0.85, Code synthesis)
  - Auditor (temp 0.1, top-p 0.9, Security, correctness)
  - Synthesizer (temp 0.4, top-p 0.9, Integration, final answer)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import yaml

DEFAULT_SWARM_ROLES_PATH = os.path.expanduser("~/.hermes/profiles/swarm_roles.yaml")

# Hardcoded robust fallbacks ensuring zero runtime degradation if file missing
FALLBACK_SWARM_ROLES: Dict[str, Dict[str, Any]] = {
    "director": {
        "role_name": "director",
        "title": "Chief Architectural Director",
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 2048,
        "focus": "Planning, decomposition",
        "system_prompt": (
            "You are @director. Your responsibility is high-level orchestration, goal decomposition, "
            "and topological milestone sequencing. Break complex challenges into strictly ordered, "
            "verifiable phases. Never produce speculative implementations."
        ),
        "capabilities": ["planning", "decomposition", "coordination", "invariant_monitoring"],
    },
    "researcher": {
        "role_name": "researcher",
        "title": "Autonomous Knowledge Researcher",
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 3072,
        "focus": "Hypothesis generation",
        "system_prompt": (
            "You are @researcher. Your responsibility is deep exploration, hypothesis generation, "
            "technical documentation discovery, and literature synthesis. Formulate lateral hypotheses "
            "and discover hidden connections across domains."
        ),
        "capabilities": ["literature_discovery", "hypothesis_generation", "api_reconnaissance", "synthesis"],
    },
    "implementer": {
        "role_name": "implementer",
        "title": "Surgical Implementation Engineer",
        "temperature": 0.2,
        "top_p": 0.85,
        "max_tokens": 4096,
        "focus": "Code synthesis",
        "system_prompt": (
            "You are @implementer. Your responsibility is clean, robust, and minimal implementation. "
            "Write production-grade code with complete typing, defensive validations, and atomic patches. "
            "Avoid unnecessary rewrites."
        ),
        "capabilities": ["code_generation", "atomic_patching", "refactoring", "interface_binding"],
    },
    "auditor": {
        "role_name": "auditor",
        "title": "Adversarial Verification Auditor",
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 2048,
        "focus": "Security, correctness",
        "system_prompt": (
            "You are @auditor. Your responsibility is adversarial verification, edge-case vulnerability "
            "probing, and invariant enforcement. Strictly enforce the Maker != Verifier invariant. "
            "Scrutinize every assumption and detect silent failures."
        ),
        "capabilities": ["invariant_verification", "red_team_critique", "security_audit", "regression_guard"],
    },
    "synthesizer": {
        "role_name": "synthesizer",
        "title": "Consensus Aggregator & Synthesizer",
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 4096,
        "focus": "Integration, final answer",
        "system_prompt": (
            "You are @synthesizer. Your responsibility is harmonizing divergent perspectives, "
            "resolving conflicts, weighting evidence by confidence scores, and distilling the authoritative, "
            "unified consensus for the final decision."
        ),
        "capabilities": ["perspective_fusion", "conflict_resolution", "confidence_weighting", "executive_synthesis"],
    },
}


@dataclass
class SwarmRole:
    role_name: str
    title: str
    temperature: float
    top_p: float
    max_tokens: int
    focus: str
    system_prompt: str
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_name": self.role_name,
            "title": self.title,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "focus": self.focus,
            "system_prompt": self.system_prompt,
            "capabilities": self.capabilities,
        }


class SwarmRoleRegistry:
    """Registry for loading and accessing swarm persona definitions."""

    def __init__(self, config_path: str = DEFAULT_SWARM_ROLES_PATH):
        self.config_path = config_path
        self._roles: Dict[str, SwarmRole] = {}
        self._load()

    def _load(self) -> None:
        raw_roles: Dict[str, Any] = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    raw_roles = data.get("roles", {})
            except Exception:
                raw_roles = {}

        # Merge with fallback defaults to ensure all 5 core roles exist
        merged = dict(FALLBACK_SWARM_ROLES)
        if isinstance(raw_roles, dict):
            for k, v in raw_roles.items():
                if isinstance(v, dict):
                    merged[k.lower()] = {**merged.get(k.lower(), {}), **v}

        self._roles = {
            name: SwarmRole(
                role_name=name,
                title=d.get("title", name.capitalize()),
                temperature=float(d.get("temperature", 0.2)),
                top_p=float(d.get("top_p", 0.9)),
                max_tokens=int(d.get("max_tokens", 2048)),
                focus=str(d.get("focus", "")),
                system_prompt=str(d.get("system_prompt", "")),
                capabilities=list(d.get("capabilities", [])),
            )
            for name, d in merged.items()
        }

    def get_role(self, name: str) -> SwarmRole:
        role_key = name.lower().strip().lstrip("@")
        if role_key in self._roles:
            return self._roles[role_key]
        raise KeyError(f"Swarm role '{name}' not found. Available: {sorted(self._roles.keys())}")

    def list_roles(self) -> List[SwarmRole]:
        return list(self._roles.values())


# Global singleton registry
_REGISTRY: Optional[SwarmRoleRegistry] = None


def get_swarm_registry() -> SwarmRoleRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = SwarmRoleRegistry()
    return _REGISTRY


def get_swarm_role(role_name: str) -> SwarmRole:
    return get_swarm_registry().get_role(role_name)


def list_swarm_roles() -> List[SwarmRole]:
    return get_swarm_registry().list_roles()
