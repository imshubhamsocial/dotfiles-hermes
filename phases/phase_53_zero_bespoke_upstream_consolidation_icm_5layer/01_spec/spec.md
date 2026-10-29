# Phase 53 Specification: Zero-Bespoke Upstream Consolidation & 5-Layer ICM Architecture

> **Architectural Standard**: Jake Van Clief's Interpretable Context Methodology (ICM / MWP, arXiv:2603.16021)  
> **Mandate**: Retire 100% of bespoke scripts from `scripts/` and `private_dot_hermes/`. Replace all orchestration with native upstream NousResearch/hermes-agent subsystems, official catalog plugins (`openviking`, `jev-curator`), and a 5-layer pure Markdown folder hierarchy.

---

## 1. Intent & Problem Statement
Prior to Phase 53, Hermes Agent OS accumulated 17 custom Python wrapper scripts across Phases 1 through 52, plus an ephemeral proxy on Port 1934. In GDR27, a proposal to consolidate these into `hermes-icm-os/__init__.py` was rejected because creating a bespoke plugin retains custom technical debt.

Phase 53 achieves a pure, 100% zero-custom-code architecture:
1. **Script Decommissioning**: Permanently retire all 17 bespoke scripts and the Port 1934 proxy.
2. **Official Plugin Adoption**: Install and enable catalog plugins `openviking` (Port 1933 memory) and `jev-curator` (8-way semantic skill governance).
3. **Declarative Upstream Bug Fixes**:
   - Resolve Issue #28825 via `gateway.platforms.api_server.extra.direct_model_requests: true`.
   - Resolve Issue #56360 by disabling `agent.tool_use_enforcement`, `agent.task_completion_guidance`, and `agent.parallel_tool_call_guidance`.
4. **5-Layer ICM Workspace**:
   - Layer 0: Root `AGENTS.md` (< 60 lines) and `SOUL.md`.
   - Layer 1: Root `CONTEXT.md` (< 80 lines).
   - Layer 2: Stage contracts `stages/01-spec/` through `stages/04-verify/` (< 80 lines each).
   - Layer 3: Immutable reference rules in `rules/` and `_config/` (< 200 lines each).
   - Layer 4: Working outputs connecting stages.
5. **Mechanical Pre-Commit Enforcement**: Standard `.pre-commit-config.yaml` running Ruff and POSIX line limits.

---

## 2. Hard Invariants
- **Zero Bespoke Code**: 0 custom `.py` scripts in `scripts/` or `plugins/`.
- **Substrate Purity**: Upstream `.hermes/hermes-agent` must remain 100% clean (`git status --porcelain == ""`).
- **Hardware Invariant**: Pure-GPU VRAM usage strictly $\le 5,400.0\text{ MiB}$ at $0 ongoing API cost.
- **Line Limit Invariant**: All `CONTEXT.md` files $< 80$ lines; all `rules/*.md` files $< 200$ lines.
