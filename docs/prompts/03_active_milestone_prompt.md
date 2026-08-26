# 03. Active Milestone Prompt: U60 (Master Grand Prix Production Certification)

> **Current Execution Target**: Milestone 4 Phase 2 — Specification `U60` (FINAL CAPSTONE)  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U60`)

Implement the **Master Grand Prix Production Certification Suite** (`tests/harness_contracts/test_roadmap4_u60_grand_prix_certification.py`):

1. **Holistic 10-Tier Unified Subsystem Audit**:
   * Evaluates end-to-end synergy across all Roadmap 4 subsystems (`U45` through `U59`):
     * Prompt Slotting & Context Compactor (`U45`)
     * OpenSkills Package Manager (`U46`)
     * OpenCode-Mem Vector Retrieval (`U47`)
     * Agent-OS Two-Tier Rules & Plan.json (`U48`)
     * COG Dual-Agent Verifier Consensus (`U49`)
     * Codebase Memory AST Graph (`U50`)
     * NVIDIA SkillEvaluator (+15% Lift Gate) (`U51`)
     * DeepMind Recirculation System-2 Hook (`U52`)
     * OpenViking 3-Tier VFS (`U53`)
     * Schema.org JSON-LD Grounding (`U54`)
     * Draft-Detective Fact-Checking & AST Gates (`U55`)
     * Google ADK 2.0 TaskDAG & `/learn` Reflection (`U56`)
     * Unified Synergy Event Bus (`U57`)
     * Closed-Loop Verification Matrix (`U58`)
     * Autonomous Skill Evolution Substrate (`U59`)

2. **Strict Hardware Envelope & Zero OOMs**:
   * Pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$) for all harness math and retrieval.
   * Full 64K Context Window stability under $\le 4,812\text{ MiB}$ VRAM.

---

## 2. Implementation Deliverables

* `tests/harness_contracts/test_roadmap4_u60_grand_prix_certification.py`: Master graduation certification suite.
* Master self-audit probe execution.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u60_grand_prix_certification.py` asserting:
1. `test_grand_prix_intake_and_grounding_tier()`: Validates slots, rules, OpenCode-Mem, and OpenViking VFS.
2. `test_grand_prix_planning_and_recirculation_tier()`: Validates plan.json, Schema.org JSON-LD, and DeepMind Recirculation.
3. `test_grand_prix_execution_and_synergy_tier()`: Validates ADK TaskDAG, OpenSkills loader, and Synergy Event Bus.
4. `test_grand_prix_verification_matrix_tier()`: Validates AST checks, Draft-Detective fact-checking, and 2-strike tabu pruner.
5. `test_grand_prix_reflective_evolution_tier()`: Validates `/learn` correction capture and NVIDIA SkillEvaluator promotion.
6. `test_grand_prix_hardware_invariants_and_vram_bounds()`: Enforces pure CPU RAMDisk bounds ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u60_grand_prix_certification.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes Master Grand Prix Production Certification turn" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 561 existing tests + new U60 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add tests/harness_contracts/test_roadmap4_u60_grand_prix_certification.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): complete U60 Master Grand Prix Production Certification and finalize Roadmap 4'"
   ```
