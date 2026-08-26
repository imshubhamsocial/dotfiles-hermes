# 03. Active Milestone Prompt: U59 (Autonomous Reflective Skill Evolution Substrate)

> **Current Execution Target**: Milestone 4 Phase 2 — Specification `U59`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U59`)

Implement the **Autonomous Reflective Skill Evolution Substrate** (`src/hermes_core/skill_evolution.py`):

1. **Autonomous Evolution Loop**:
   * Bridges Reflective Learner (`reflective_learner.py`), OpenSkills Universal Manager (`openskills_manager.py`), and NVIDIA SkillEvaluator (`skill_evaluator.py`) into an end-to-end self-improvement loop:
     $$\text{Correction / Failure} \longrightarrow \text{Draft Candidate SKILL.md} \longrightarrow \text{A/B Benchmark} \longrightarrow \text{Promotion ($\ge +15\%$ Lift Gate)}$$

2. **Drift & Bloat Prevention**:
   * Automatically discards candidate skills that produce regressions or prompt bloat ($>150\text{ tokens}$).

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$) with zero background GPU overhead.

---

## 2. Implementation Deliverables

* `src/hermes_core/skill_evolution.py`: Autonomous skill evolution orchestrator and promotion engine.
* Integration into the OpenSkills lifecycle manager.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u59_skill_evolution.py` asserting:
1. `test_skill_evolution_candidate_synthesis()`: Validates automatic generation of candidate `SKILL.md` from `/learn` reflections.
2. `test_skill_evolution_successful_promotion_cycle()`: Validates end-to-end promotion when candidate achieves $\ge +15\%$ empirical lift.
3. `test_skill_evolution_rejection_on_insufficient_lift()`: Rejects candidate skills with $<+15\%$ lift or token bloat.
4. `test_skill_evolution_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u59_skill_evolution.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes Autonomous Skill Evolution Substrate probe" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 557 existing tests + new U59 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/skill_evolution.py tests/harness_contracts/test_roadmap4_u59_skill_evolution.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U59 Autonomous Reflective Skill Evolution Substrate'"
   ```
