# 03. Active Milestone Prompt: U46 (OpenSkills Universal Package Manager & Lifecycle)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U46`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/13_perplexity_local_first_and_openskills.md` & `02_anthropic_universal_skills.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U46`)

Implement the **OpenSkills Universal Package Manager & Skill Lifecycle Subsystem** (`src/hermes_core/openskills_manager.py`) to standardize on-demand skill discovery, JIT loading, isolated execution, and eviction without bloating Gemma-4's active context window:

1. **Standardized OpenSkills Parser & Manifest Engine (`src/hermes_core/openskills_manager.py`)**:
   * Parse `SKILL.md` packages following the universal OpenSkills / Anthropic standard (`name`, `description`, YAML frontmatter, execution schema, dependencies).
   * Replace legacy ad-hoc `bin/skills_catalog.py` indexing with a standardized registry supporting both local `.hermes/skills/` and system-wide bundled packages.

2. **JIT Lifecycle: Progressive Disclosure (Load ➔ Execute ➔ Unload)**:
   * **Stage 1 (L0 Discovery - In Prompt)**: Expose only concise name + single-sentence description in the system prompt ($<50\text{ tokens}$ per skill).
   * **Stage 2 (L1 On-Demand Load)**: When the model invokes `load_skill(name)`, inject the full detailed instruction block and tool schema dynamically into Slot 4 / Active Context.
   * **Stage 3 (L2 Unload & Context Eviction)**: Once the skill-related subtask concludes, automatically unload detailed instructions to prevent attention dilution and context bloat.

3. **Dependency & Environment Isolation**:
   * Validate that skill execution hooks adhere to zero-GPU-VRAM limits (running CPU / RAMDisk).

---

## 2. Implementation Deliverables

* `src/hermes_core/openskills_manager.py`: OpenSkills package parser, registry, JIT loader, and lifecycle manager.
* Integration into CLI agent loop and prompt slotting engine (`src/hermes_core/prompt_slotting.py`).

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u46_openskills_lifecycle.py` asserting:
1. `test_openskills_yaml_frontmatter_parsing()`: Validates YAML frontmatter parsing against OpenSkills schema.
2. `test_progressive_disclosure_discovery_tokens()`: Validates that L0 discovery format consumes $<50$ tokens per skill.
3. `test_jit_skill_load_and_unload_lifecycle()`: Validates dynamic injection into active context on `load_skill` and eviction on `unload_skill`.
4. `test_skill_dependency_and_missing_field_validation()`: Validates graceful refusal and error trapping on malformed `SKILL.md`.
5. `test_openskills_zero_vram_overhead()`: Validates $0\text{ MB GPU VRAM}$ consumed during skill lifecycle operations.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u46_openskills_lifecycle.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 325 existing tests + new U46 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/openskills_manager.py tests/harness_contracts/test_roadmap4_u46_openskills_lifecycle.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U46 OpenSkills universal package manager and lifecycle'"
   ```
