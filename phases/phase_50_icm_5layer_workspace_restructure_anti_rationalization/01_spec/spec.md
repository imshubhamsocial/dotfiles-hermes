# Phase 50 Specification: ICM 5-Layer Workspace Hierarchy with icm-architect & Anti-Rationalization Tables

* **ICM Layer**: Orchestration & Context Architecture (30% Tier)
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)
* **Input State**: 
  - Workspace currently exhibits unstructured rule loading, missing 3-Tier permission boundaries (`Always` / `Ask First` / `Never`), and lacks static context-wiring auditing.
  - LLM agents frequently rationalise skipping verification passes or bail out prematurely during multi-turn recovery.
* **Process**:
  1. Install `icm-architect` skill into `~/.hermes/skills/icm-architect/SKILL.md` (and workspace counterpart):
     - Implements schema validation for ICM 5-Layer Hierarchy (Layers 0–4).
     - Enforces line count invariants: `CONTEXT.md` <= 80 lines, reference files <= 200 lines.
     - Enforces "One Fact, One Home" and the **Walk Test** (zero-memory orientation).
  2. Implement root 6-section `AGENTS.md` (and symlink `CLAUDE.md -> AGENTS.md`):
     - 1. Operational Scope & 60/30/10 Layering Rule.
     - 2. 3-Tier Permissions Boundary (`Always` / `Ask First` / `Never`).
     - 3. ICM 5-Layer Hierarchy & 4-Column Selective Section Loading.
     - 4. Stage Gate Machine (01_spec -> 02_impl -> 03_verify).
     - 5. Anti-Rationalization & Anti-Sycophancy Inline Rebuttal Table.
     - 6. Hardware & Cryptographic Invariants (5400 MiB ceiling, receipt sealing).
  3. Deploy Addy Osmani's Anti-Rationalization Tables into `rules/anti_rationalization_tables.md` and awesome-cursorrules's 17 Anti-Sycophancy Directives into `rules/anti_sycophancy_directives.md`.
  4. Implement `scripts/hermes_icm_validator.py` executing automated static context-wiring checks in Phase 44's ruff pre-commit gate.
* **Output Artifacts**:
  - `AGENTS.md` & `CLAUDE.md`
  - `~/.hermes/skills/icm-architect/SKILL.md`
  - `rules/anti_rationalization_tables.md`
  - `rules/anti_sycophancy_directives.md`
  - `scripts/hermes_icm_validator.py`
