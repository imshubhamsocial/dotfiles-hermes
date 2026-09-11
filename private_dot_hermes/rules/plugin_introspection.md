---
version: 1.0.0
category: execution
extends: global
---

# Hermes Plugin Introspection & Namespace Disambiguation

This rule codifies the procedure for querying and introspecting Hermes plugins vs skills.

## Rule Directive

When queried about a Hermes plugin's exposed functions, schemas, hooks, or CLI commands:

1. **Direct File Path Resolution**: Always target the plugin directory at `~/.hermes/plugins/<plugin_name>/` rather than searching the procedural skills registry (`~/.hermes/skills/`).
2. **Read Implementation Directly**: Use `read_file` or AST symbol extraction directly on `~/.hermes/plugins/<plugin_name>/__init__.py` and `plugin.yaml`.
3. **Hook and CLI Extraction**: Verify functions defined in `__all__` and inspect the `register(ctx)` entry point for `ctx.hooks`, `ctx.commands`, or `ctx.slash_commands` registrations.
4. **Zero Fallback Confusion**: Never confuse plugins (Python extension modules loaded via `plugin.yaml`) with skills (procedural Markdown workflows loaded via `SKILL.md`).
