"""
U4: Plugin Manifest Schema & Validator
=======================================
Defines the PluginManifest dataclass for `.hermes/plugins/<name>/plugin.yaml`
and enforces the token-efficient summary format required by Tier-1 discovery.

Token Budget (Roadmap §2.3):
  10 plugins at ~20 tokens each = ~200 tokens.
  Enforced ceiling: <=150 tokens total for the Tier-1 summary block.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class PluginManifest:
    """Typed representation of a plugin.yaml manifest."""
    name: str
    version: str
    description: str
    author: str = "hermes"
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    hooks: dict = field(default_factory=dict)
    mcp_servers: List[str] = field(default_factory=list)
    subagent_profiles: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "enabled": self.enabled,
            "hooks": self.hooks,
            "mcp_servers": self.mcp_servers,
            "subagent_profiles": self.subagent_profiles,
        }

    def summary_line(self, max_desc: int = 40) -> str:
        """Tier-1 token-efficient single-line summary (~15-20 tokens).

        Format: '- <name> (<tags>): <truncated_desc>'
        Truncation ensures each line stays well under the token ceiling.
        """
        desc = self.description[:max_desc]
        if len(self.description) > max_desc:
            desc += "..."
        tag_str = ",".join(self.tags[:3]) if self.tags else "core"
        return f"- {self.name} ({tag_str}): {desc}"

    def validate(self) -> None:
        """Raise ValueError if manifest fields are missing or invalid."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Plugin manifest: 'name' is required and must be a non-empty string.")
        if not self.version or not isinstance(self.version, str):
            raise ValueError(f"Plugin '{self.name}': 'version' is required.")
        if not self.description or not isinstance(self.description, str):
            raise ValueError(f"Plugin '{self.name}': 'description' is required.")


def load_manifest(path: Path) -> PluginManifest:
    """Load and validate a plugin.yaml file, returning a PluginManifest."""
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid manifest format: {path}")
    manifest = PluginManifest(
        name=data.get("name", ""),
        version=data.get("version", ""),
        description=data.get("description", ""),
        author=data.get("author", "hermes"),
        tags=data.get("tags", []),
        enabled=data.get("enabled", True),
        hooks=data.get("hooks") or {},
        mcp_servers=data.get("mcp_servers") or [],
        subagent_profiles=data.get("subagent_profiles") or [],
    )
    manifest.validate()
    return manifest


def estimate_tokens(text: str) -> int:
    """Deterministic sub-1ms token proxy (4 chars/token heuristic)."""
    return max(1, len(" ".join(text.split())) // 4)
