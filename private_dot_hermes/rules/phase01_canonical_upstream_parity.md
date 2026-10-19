---
phase: "Phase 01"
authority: "Pristine Upstream NousResearch Parity"
testbed: "tests/"
status: "Operational & Certified"
version: 1.0.0
category: architecture
extends: global
---
# Canonical Upstream Parity & Agent OS Invariants

This rule codifies the architecture invariants governing Hermes Agent OS within both native bare-metal production environments and containerized development runtimes (e.g. Distrobox).

## Invariants

### 1. Single Canonical Agent Home (`$HOME/.hermes`)
- All agent configuration, capabilities, plugins, skills, hooks, rules, documentation, and tests reside strictly inside `~/.hermes/`.
- No parallel root-level directories (`tests/`, `docs/`, `src/`) may exist outside `~/.hermes/` to avoid dual-hierarchy drift.

### 2. Zero Hardcoded Workspace Paths
- Code, policies, tests, and skill prompts must **never** hardcode machine-specific host paths (e.g. `/var/home/.../Projects/...`).
- Always use portable home expansions (`~`, `$HOME`, or `Path.home()`) or relative paths.
- Sandboxing policies (`agent_capabilities.yaml`) must enforce relative/home confinement (`workspace_root: "~"`).

### 3. Upstream NousResearch Compatibility
- The agent core at `~/.hermes/hermes-agent` tracks official NousResearch `hermes-agent`.
- Built-in Hermes lifecycle operations (`/learn`, `/rollback`, `/loop`, `/clear`, `hermes doctor`, `hermes plugins`) execute identically in local dev and production.
- Plugins reside in `~/.hermes/plugins/<plugin_name>/` and implement standard `plugin.yaml` manifests discoverable by `hermes plugins`.

### 4. Continuous Verification & Clean Chezmoi Sync
- Verification is maintained via `make test` (`python3.13 -m pytest ~/.hermes/tests/ -q`) and `hermes doctor`.
- Every modification to `~/.hermes/` must be mirrored in `~/.local/share/chezmoi/private_dot_hermes/` to ensure full reproduction across machines.
