"""
U4: Bundled Plugin Loader — Two-Tier JIT Discovery
===================================================
Standardizes `.hermes/plugins/<name>/` packaging into versioned units.

Two-Tier Architecture (Roadmap §2.3 Trap-1 Countermeasure):
  Tier 1 (Index):  Only 1-line plugin descriptions loaded into root prompt
                   (~15-20 tokens each; 10 plugins <= 150 tokens total).
  Tier 2 (JIT):    Full SKILL.md body + hook scripts loaded ONLY when the
                   plugin is explicitly activated for the current turn.

Token budget enforced at discovery time: summary_block_tokens() <= 150.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .manifest import PluginManifest, estimate_tokens, load_manifest

TIER1_TOKEN_BUDGET = 150


def discover_plugins(plugins_root: Path) -> List[PluginManifest]:
    """Tier-1: scan all enabled plugin directories, load manifests only."""
    manifests = []
    if not plugins_root.is_dir():
        return manifests
    for plugin_dir in sorted(plugins_root.iterdir()):
        if not plugin_dir.is_dir():
            continue
        manifest_path = plugin_dir / "plugin.yaml"
        if not manifest_path.exists():
            continue
        try:
            manifest = load_manifest(manifest_path)
            if manifest.enabled:
                manifests.append(manifest)
        except (ValueError, FileNotFoundError):
            continue
    return manifests


def tier1_summaries(manifests: List[PluginManifest]) -> List[str]:
    """Return list of token-efficient 1-line summaries for enabled plugins."""
    return [m.summary_line() for m in manifests]


def summary_block_tokens(summaries: List[str]) -> int:
    """Estimate token count of the full Tier-1 summary block injected into system prompt."""
    block = "\n".join(summaries)
    return estimate_tokens(block)


def tier1_in_budget(manifests: List[PluginManifest],
                     budget: int = TIER1_TOKEN_BUDGET) -> bool:
    """Check if Tier-1 summaries stay within the token budget."""
    sums = tier1_summaries(manifests)
    return summary_block_tokens(sums) <= budget


def activate_plugin(plugins_root: Path, name: str) -> Optional[Dict]:
    """Tier-2 JIT activation: load full SKILL.md + hook metadata for one plugin.

    Returns a dict with manifest, skill_content, and hook paths, or None if
    the plugin does not exist or is disabled.
    """
    plugin_dir = plugins_root / name
    manifest_path = plugin_dir / "plugin.yaml"
    if not manifest_path.exists():
        return None

    try:
        manifest = load_manifest(manifest_path)
    except (ValueError, FileNotFoundError):
        return None

    if not manifest.enabled:
        return None

    skill_path = plugin_dir / "SKILL.md"
    skill_content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

    hook_paths = {}
    for hook_name, hook_rel in manifest.hooks.items():
        hp = plugin_dir / hook_rel
        if hp.exists():
            hook_paths[hook_name] = hp

    return {
        "manifest": manifest,
        "skill_content": skill_content,
        "hook_paths": hook_paths,
        "plugin_dir": plugin_dir,
    }


def load_plugin_hooks(plugin_dir: Path, hook_name: str) -> Optional[callable]:
    """Dynamically load a hook script from a plugin directory."""
    import importlib.util
    hook_path = plugin_dir / hook_name
    if not hook_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        f"plugin_hook_{hook_name}", str(hook_path)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "run", None)
