# Hermes Agent OS — Layer 0 Workspace Map (AGENTS.md)

> **Architectural Standard**: Jake Van Clief's Interpretable Context Methodology (ICM / MWP, arXiv:2603.16021)  
> **Layering Rule**: 60% Infrastructure | 30% Orchestration (Pure Markdown + Upstream Built-ins) | 10% Local Cognition  
> **Working Context Discipline**: Maintain active working context strictly between 2,000 and 8,000 tokens.

---

## 1. Quick Task Routing

| User Intent / Task | Entry File to Read Next | Target Stage / Tool |
| :--- | :--- | :--- |
| Understand pipeline & stage handoffs | CONTEXT.md | Layer 1 Router |
| Scope a new requirement or bug fix | stages/01-spec/CONTEXT.md | Stage 01 (Spec) |
| Design an architectural or file plan | stages/02-plan/CONTEXT.md | Stage 02 (Plan) |
| Modify code, configs, or skills | stages/03-execute/CONTEXT.md | Stage 03 (Execute) |
| Run fresh-session verification gate | stages/04-verify/CONTEXT.md | Stage 04 (Verify via delegate_task) |
| Audit or restructure ICM folders | ~/.hermes/skills/icm-architect/SKILL.md | icm-architect Skill |

---

## 2. 3-Tier Permissions & Core Invariants

- **Always (Autonomous Execution)**:
  - Read files, query AST, run pre-commit linters (`ruff check`), and execute stage contracts.
  - Query local read-only tools and memory (Port 1933) before mutating state.
- **Ask First (User Escalation Required)**:
  - Mutating upstream git remotes outside prescribed stage contracts.
  - Deleting non-temporary files or modifying environment configurations.
- **Never (Hard Forbidden Invariants)**:
  - Never author bespoke Python wrappers or custom plugins in `scripts/` or `plugins/`.
  - Never bypass permission checks, credentials, or sandbox boundaries.
  - Never execute with GPU VRAM exceeding 5,400.0 MiB (`nvidia-smi` live NVML check).
  - Upstream substrate purity: `.hermes/hermes-agent` must remain 100% clean.
