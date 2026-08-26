# 03. Active Milestone Prompt: U48 (Agent-OS Two-Tier Standards & Spec-First Planner)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U48`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/04_agent_os_architecture.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U48`)

Implement the **Agent-OS Two-Tier Standards & Spec-First Planning Subsystem** (`src/hermes_core/agent_os_standards.py` / `src/hermes_core/spec_first_planner.py`):

1. **Two-Tier Hierarchical Standards Engine (`src/hermes_core/agent_os_standards.py`)**:
   * **Global Standards (`~/.hermes/rules/` or `/var/home/imshubhamsocial/.hermes/rules/`)**: Immutable core rules (Btrfs NOCOW, RTX 3050 hardware ceiling, zero-sorry tests, relative paths).
   * **Project Standards (`.hermes/rules/` or repo-local rules)**: Project-specific architectural conventions, stack requirements, and test commands.
   * **Deterministic Precedence**: Project rules override defaults, but can NEVER violate Global hardware or safety constraints.

2. **Pre-Implementation `plan.json` Spec Gate (`src/hermes_core/spec_first_planner.py`)**:
   * Enforce that before modifying any file, the agent generates or updates a structured `.hermes/plan.json` file.
   * Schema requires: `task_id`, `goal`, `steps` (with `id`, `description`, `status`), `constraints`, `affected_files`.
   * The active plan state is verified and formatted into a machine-readable anchor for Slot 3 / User turns.

3. **Strict Invariant Verification**:
   * Fast load times ($<5\text{ ms}$ parsing).
   * Pure CPU / RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 2. Implementation Deliverables

* `src/hermes_core/agent_os_standards.py`: Two-tier hierarchical rule loader with inheritance and precedence rules.
* `src/hermes_core/spec_first_planner.py`: Spec-first planner enforcing `plan.json` generation before execution.
* Integration into Prompt Slotting (`src/hermes_core/prompt_slotting.py`) to inject combined two-tier rules into Slot 3.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u48_agent_os_specs.py` asserting:
1. `test_two_tier_rules_inheritance_and_precedence()`: Validates project rules take precedence over defaults while respecting immutable global safety constraints.
2. `test_spec_first_planner_plan_json_schema()`: Validates deterministic generation and JSON schema compliance of `.hermes/plan.json`.
3. `test_pre_implementation_plan_gate()`: Validates that code edits are gated behind an active valid `plan.json`.
4. `test_rules_token_budget_in_slot3()`: Validates that compiled two-tier rules stay within $<300\text{ tokens}$ in Slot 3.
5. `test_agent_os_zero_gpu_vram()`: Validates $0\text{ MB GPU VRAM}$ overhead.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u48_agent_os_specs.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 403 existing tests + new U48 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/agent_os_standards.py src/hermes_core/spec_first_planner.py tests/harness_contracts/test_roadmap4_u48_agent_os_specs.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U48 Agent-OS two-tier standards and spec-first planner'"
   ```
