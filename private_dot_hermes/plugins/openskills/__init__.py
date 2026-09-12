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
    if not ctx:
        return True

    manager = get_openskills_manager()

    # 1. Native CLI command: hermes openskills [list | load | unload | status]
    if hasattr(ctx, "register_cli_command"):
        def setup_openskills(parser):
            parser.description = "OpenSkills Universal Package Manager & Progressive Disclosure"
            subparsers = parser.add_subparsers(dest="subcommand", help="OpenSkills actions")
            subparsers.add_parser("list", help="List available skills (L0 discovery)")
            subparsers.add_parser("status", help="Show active loaded skills (L1 context) and VRAM guarantee")
            load_p = subparsers.add_parser("load", help="Load skill into active context")
            load_p.add_argument("name", help="Skill name to load")
            unload_p = subparsers.add_parser("unload", help="Unload skill from active context")
            unload_p.add_argument("name", help="Skill name to unload")

        def handle_openskills(args):
            subcmd = getattr(args, "subcommand", None) or "list"
            if subcmd == "list":
                skills = manager.list_available_skills()
                print(f"OpenSkills Available ({len(skills)} skills):")
                for s in skills:
                    loaded_marker = "[LOADED]" if s.get("loaded") else "        "
                    print(f"  {loaded_marker} {s['name']}: {s['description']}")
            elif subcmd == "status":
                loaded = manager.get_loaded_skills()
                print(f"OpenSkills Status — {len(loaded)} Active Loaded Skill(s):")
                for name, skill in loaded.items():
                    print(f"  • {name} (v{skill.package.manifest.version}): {len(skill.tools)} tools, {skill.tokens} tokens")
                guarantee = manager.get_zero_vram_guarantee()
                print(f"  VRAM Usage: {guarantee.get('vram_used_bytes', 0)} bytes (Strict 0 VRAM Guarantee: {guarantee.get('zero_vram_respected')})")
            elif subcmd == "load":
                res = manager.load_skill(args.name)
                if res.get("status") == "loaded":
                    print(f"Loaded skill '{args.name}' ({res.get('tokens', 0)} tokens, {len(res.get('tools', []))} tools).")
                else:
                    print(f"Failed to load skill '{args.name}': {res.get('error')}")
            elif subcmd == "unload":
                if manager.unload_skill(args.name):
                    print(f"Unloaded skill '{args.name}'.")
                else:
                    print(f"Skill '{args.name}' was not loaded.")

        ctx.register_cli_command("openskills", setup_openskills, handle_openskills)

    # 2. Slash command: /openskills
    if hasattr(ctx, "register_command"):
        def slash_openskills(arg_str: str = ""):
            parts = arg_str.strip().split()
            if not parts or parts[0] == "list":
                skills = manager.list_available_skills()
                lines = [f"OpenSkills Catalog ({len(skills)} available):"]
                for s in skills[:15]:
                    lines.append(f"- {s['name']}: {s['description'][:60]}")
                return "\n".join(lines)
            elif parts[0] == "load" and len(parts) > 1:
                res = manager.load_skill(parts[1])
                return f"Skill '{parts[1]}' load status: {res.get('status')}"
            elif parts[0] == "unload" and len(parts) > 1:
                success = manager.unload_skill(parts[1])
                return f"Skill '{parts[1]}' unloaded: {success}"
            return "Usage: `/openskills [list | load <name> | unload <name>]`"

        ctx.register_command("openskills", slash_openskills, "Manage OpenSkills dynamic package lifecycle", "[list|load|unload]")

    # 3. Lifecycle Hooks: inject loaded skills context via user message suffix
    if hasattr(ctx, "register_hook"):
        def openskills_pre_llm_call(**kwargs):
            loaded_context = manager.get_all_loaded_context()
            if loaded_context.strip():
                return {"context": f"[OpenSkills Active Context]\n{loaded_context.strip()}"}
            return None

        ctx.register_hook("pre_llm_call", openskills_pre_llm_call)

    return True

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
