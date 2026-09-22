# Cognitive Invariant Rule: Zero Bespoke Files & Upstream-First Extension Model
# File: .hermes/rules/rule_zero_bespoke_files_invariant.md

This rule codifies the non-negotiable architectural invariant that Hermes Agent OS operates exclusively through upstream-sanctioned mechanisms, eliminating bespoke synthetic files, shadow frameworks, and phantom scripts.

## ⚙️ Enforced Standards

### 1. Zero Custom Scripts Outside Sanctioned Extension Points
No standalone Python scripts, CLI wrappers, or custom tool dispatchers may be created in `.hermes/` (e.g. `.hermes/bin/`, `.hermes/scripts/`, `.hermes/tools/`).
- **Sanctioned Tool Extensions**: New tools must be added strictly via the **Model Context Protocol (MCP)** using `hermes mcp add` and registered under `mcp_servers` in `.hermes/config.yaml`.
- **Sanctioned Capability Extensions**: Specialized multi-step workflows must be implemented exclusively as native skills in `.hermes/skills/` adhering to the standard `SKILL.md` schema.
- **Sanctioned Memory Extensions**: Long-term memory providers must use upstream bundled plugins (`plugins/memory/` e.g. OpenViking, Hindsight, Mem0) activated via `hermes config set memory.provider <name>`.

### 2. Upstream Command Purity in Automation & Cron
All scheduled cron jobs (`.hermes/cron/*.yaml`) and diagnostic scripts must call ONLY official, upstream-supported Hermes CLI commands (`hermes doctor`, `hermes memory`, `hermes mcp`, `hermes skills`).
- **Forbidden**: Invoking non-existent subcommands (e.g., `hermes evolve analyze`, `hermes evolve propose`).
- **Verification**: Any script triggered by cron must pass standalone execution with exit code 0 before registration.

### 3. Absolute Prevention of Synthetic Specifications & Stubs
Never commit placeholder specs (`.hermes/specs/`), fake 200-byte LoRA adapters (`.hermes/adapters/*.gguf`), or mock test plans (`.hermes/plan.json`). All persistent system state resides exclusively in canonical locations:
- System Prompt Guardrails & Invariants: `.hermes/rules/rule_*.md`
- Long-Term Semantic Memories: `.hermes/memories/`
- Operational SQLite Database: `.hermes/state.db`
- Master Configuration: `.hermes/config.yaml`
