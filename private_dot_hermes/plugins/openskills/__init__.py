"""Hermes Plugin: openskills"""

from .manager import (
    SkillManifest,
    SkillPackage,
    LoadedSkill,
    SkillParser,
    ToolSchemaExtractor,
    OpenSkillsManager,
    get_openskills_manager,
    reset_openskills_manager,
    build_skills_discovery_block,
    inject_loaded_skills_context,
)
from .manifest import PluginManifest, load_manifest, estimate_tokens
from .loader import (
    discover_plugins,
    tier1_summaries,
    summary_block_tokens,
    tier1_in_budget,
    activate_plugin,
    load_plugin_hooks,
)

def register(ctx=None):
    """Registers plugin openskills into Hermes runtime."""
    pass

__all__ = [
    "SkillManifest",
    "SkillPackage",
    "LoadedSkill",
    "SkillParser",
    "ToolSchemaExtractor",
    "OpenSkillsManager",
    "get_openskills_manager",
    "reset_openskills_manager",
    "build_skills_discovery_block",
    "inject_loaded_skills_context",
    "PluginManifest",
    "load_manifest",
    "estimate_tokens",
    "discover_plugins",
    "tier1_summaries",
    "summary_block_tokens",
    "tier1_in_budget",
    "activate_plugin",
    "load_plugin_hooks",
    "register",
]
