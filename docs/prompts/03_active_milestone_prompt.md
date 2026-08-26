# 03. Active Milestone Prompt: U51 (NVIDIA SkillEvaluator Automated Skill Lift Evaluation Harness)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U51`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/07_nvidia_skill_evaluator.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U51`)

Implement the **NVIDIA SkillEvaluator Automated Skill Lift Evaluation Harness Subsystem** (`src/hermes_core/skill_evaluator.py`):

1. **A/B Baseline vs. Candidate Empirical Benchmark**:
   * Evaluates candidate OpenSkills before promotion into the active skill library.
   * Runs dual-arm evaluation runs:
     * **Baseline Arm**: Standard Hermes prompt execution without candidate skill.
     * **Candidate Arm**: Hermes execution with candidate `SKILL.md` injected.
   * Measures Pass@1 rate, step economy ($\Delta\text{steps}$), token reduction, and pre-commit observer gate clearance.

2. **Statistical Quality Gate ($\ge +15\%$ Skill Lift Rule)**:
   * Rejects candidate skills that produce regressions, prompt bloat ($>150\text{ tokens}$ increase), or fail to deliver at least $+15\%$ empirical lift on task benchmark suites.
   * Auto-records evaluation metrics into `.hermes/knowledge/evaluations/`.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution ($0\text{ MB GPU VRAM}$) for evaluation orchestrator and metric computation.

---

## 2. Implementation Deliverables

* `src/hermes_core/skill_evaluator.py`: Empirical A/B skill benchmark harness and promotion gate.
* Integration into the OpenSkills lifecycle manager (`openskills_manager.py`).

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u51_skill_evaluator.py` asserting:
1. `test_skill_evaluator_ab_benchmark_run()`: Validates baseline vs candidate comparative execution.
2. `test_skill_lift_metric_calculation()`: Validates formula: $\text{Lift} = \frac{\text{Candidate Pass Rate} - \text{Baseline Pass Rate}}{\text{Baseline Pass Rate}}$.
3. `test_promotion_gate_requires_15_percent_lift()`: Rejects skills with $<+15\%$ lift or token bloat.
4. `test_evaluation_report_markdown_generation()`: Validates persistent Markdown receipt in `.hermes/knowledge/evaluations/`.
5. `test_skill_evaluator_zero_gpu_vram()`: Validates $0\text{ MB GPU VRAM}$ overhead.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u51_skill_evaluator.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 511 existing tests + new U51 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/skill_evaluator.py tests/harness_contracts/test_roadmap4_u51_skill_evaluator.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U51 NVIDIA SkillEvaluator automated skill lift evaluation harness'"
   ```
