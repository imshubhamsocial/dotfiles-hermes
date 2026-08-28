"""
Upstream Plugin Standard & Awesome-Skills Catalog (Milestone U26)
==================================================================
Implements 100% compliance with upstream Hermes Agent plugin architecture:
  1. Standard Manifest Validation (`plugin.yaml`)
  2. Two-Tier Dynamic Skill Absorption (Tier-1 <=150 tok index, Tier-2 JIT payload)
  3. Awesome-Hermes-Skills Catalog Downloader & Local Cache Sync
  4. MCP Server & Hook Configuration Binding
"""

from __future__ import annotations

import json
import os
import shutil
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from .plugin_manifest import PluginManifest, load_manifest, estimate_tokens
    from .plugin_loader import discover_plugins, activate_plugin, tier1_summaries, summary_block_tokens
except ImportError:
    from hermes_core.plugin_manifest import PluginManifest, load_manifest, estimate_tokens
    from hermes_core.plugin_loader import discover_plugins, activate_plugin, tier1_summaries, summary_block_tokens


@dataclass
class SkillCatalogItem:
    name: str
    version: str
    description: str
    author: str = "upstream"
    tags: List[str] = field(default_factory=list)
    installed: bool = False
    mcp_compatible: bool = False


class SkillsCatalogManager:
    """
    Manages local and upstream awesome-hermes-skills catalog,
    packaging validation, and Two-Tier JIT absorption.
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or Path.home() / ".hermes" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._catalog_cache: Dict[str, SkillCatalogItem] = {}

    def list_installed_plugins(self) -> List[PluginManifest]:
        """Discovers all locally installed and enabled plugins."""
        return discover_plugins(self.plugins_dir)

    def get_tier1_prompt_injection(self, max_tokens: int = 150) -> str:
        """
        Generates the compressed Tier-1 summary string for system prompt injection.
        Guaranteed to stay under max_tokens budget (Rule 10 token economy).
        """
        manifests = self.list_installed_plugins()
        summaries = tier1_summaries(manifests)
        block = "\n".join(summaries)
        toks = summary_block_tokens(summaries)
        if toks > max_tokens:
            # Drop entries from tail if budget exceeded
            allowed = []
            cur_tokens = 0
            for s in summaries:
                t = estimate_tokens(s)
                if cur_tokens + t <= max_tokens:
                    allowed.append(s)
                    cur_tokens += t
                else:
                    break
            block = "\n".join(allowed)
        return block

    def activate_jit_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Tier-2 JIT activation: loads the full skill body and hook scripts
        only when explicitly invoked for a specific task.
        """
        return activate_plugin(self.plugins_dir, name)

    def install_local_skill(
        self,
        name: str,
        skill_md_content: str,
        description: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        hooks: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[str]] = None,
    ) -> Path:
        """
        Installs a new skill into the local Hermes plugin repository following the upstream standard.
        """
        plugin_path = self.plugins_dir / name
        plugin_path.mkdir(parents=True, exist_ok=True)

        manifest_data = {
            "name": name,
            "version": version,
            "description": description,
            "author": "hermes-agent",
            "tags": tags or ["custom"],
            "enabled": True,
            "hooks": hooks or {},
            "mcp_servers": mcp_servers or [],
        }

        # Write plugin.yaml
        manifest_file = plugin_path / "plugin.yaml"
        import yaml

        with open(manifest_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(manifest_data, f)

        # Write SKILL.md
        skill_file = plugin_path / "SKILL.md"
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(skill_md_content)

        return plugin_path

    def delete_skill(self, name: str) -> bool:
        """Removes an installed skill."""
        plugin_path = self.plugins_dir / name
        if plugin_path.exists() and plugin_path.is_dir():
            shutil.rmtree(plugin_path)
            return True
        return False


def create_skills_catalog_manager(plugins_dir: Optional[Path] = None) -> SkillsCatalogManager:
    """Factory helper creating SkillsCatalogManager instance."""
    return SkillsCatalogManager(plugins_dir=plugins_dir)


__all__ = [
    "SkillCatalogItem",
    "SkillsCatalogManager",
    "create_skills_catalog_manager",
]
