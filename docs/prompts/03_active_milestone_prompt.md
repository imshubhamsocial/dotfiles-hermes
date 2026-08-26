# 03. Active Milestone Prompt: U56 (Google ADK 2.0 TaskDAG & Reflective Learning Loop)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U56`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/12_google_agent_architecture_and_workflows.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U56`)

Implement the **Google ADK 2.0 TaskDAG & Reflective Learning Loop Subsystem** (`src/hermes_core/reflective_learner.py`):

1. **Google ADK 2.0 TaskDAG Workflow Runtime**:
   * Asynchronous DAG task decomposition with dependency resolution, topological ordering, cycle detection, and conditional fan-out.
   * State persistence in SQLite WAL mode (`~/.hermes/knowledge/state.db`).

2. **Reflective Learning Loop (`/learn` Capture Engine)**:
   * Captures user corrections and runtime execution failures into a structured reflection ledger.
   * Automatically distills corrections into machine-readable behavioral constraints in `~/.hermes/rules/` and candidate skills in `.hermes/skills/`.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution ($0\text{ MB GPU VRAM}$) with zero GPU contention.

---

## 2. Implementation Deliverables

* `src/hermes_core/reflective_learner.py`: ADK 2.0 TaskDAG engine and Reflective Learning `/learn` subsystem.
* Integration into the Hermes Execution and Learning Pipeline.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u56_reflective_learning_and_adk.py` asserting:
1. `test_adk_taskdag_workflow_execution()`: Validates asynchronous DAG execution and topological order.
2. `test_reflective_learner_correction_capture()`: Validates `/learn` extraction of user constraints.
3. `test_rule_synthesis_and_persistence()`: Validates automatic writing to `~/.hermes/rules/`.
4. `test_reflective_learner_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u56_reflective_learning_and_adk.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes ADK TaskDAG & Reflective Learning probe" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 545 existing tests + new U56 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/reflective_learner.py tests/harness_contracts/test_roadmap4_u56_reflective_learning_and_adk.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U56 Google ADK 2.0 TaskDAG and reflective learning loop'"
   ```
