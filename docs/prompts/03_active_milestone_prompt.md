# 03. Active Milestone Prompt: U54 (Schema.org JSON-LD Semantic Structured Anchors Engine)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U54`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/10_schema_org_structured_data.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U54`)

Implement the **Schema.org JSON-LD Semantic Structured Anchors Engine** (`src/hermes_core/schema_anchors.py`):

1. **Deterministic Entity Grounding (JSON-LD)**:
   * Generates valid Schema.org JSON-LD payloads (`SoftwareSourceCode`, `SoftwareApplication`, `HowTo`, `TechArticle`, `TaskSpecification`).
   * Eliminates entity ambiguity across multi-file agent architectures.

2. **Plan & Plan.json Structured Anchor Injection**:
   * Automatically formats `.hermes/plan.json` and artifact headers with machine-readable `@context: "https://schema.org"` graphs.
   * Links entities via `isPartOf`, `isBasedOn`, `programmingLanguage`, `targetPlatform`, and `codeRepository`.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$) with sub-millisecond serialization latency.

---

## 2. Implementation Deliverables

* `src/hermes_core/schema_anchors.py`: Schema.org JSON-LD structured anchor builder and validator.
* Integration into the Spec-First Planner and Artifact Generator.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u54_schema_anchors.py` asserting:
1. `test_schema_jsonld_software_source_code_generation()`: Validates `SoftwareSourceCode` schema conformance.
2. `test_schema_jsonld_task_specification_graph()`: Validates multi-entity connected graph (`@graph` layout).
3. `test_schema_anchor_plan_injection()`: Validates `.hermes/plan.json` structured grounding anchor injection.
4. `test_schema_anchors_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u54_schema_anchors.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes Schema.org JSON-LD verification turn" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 536 existing tests + new U54 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/schema_anchors.py tests/harness_contracts/test_roadmap4_u54_schema_anchors.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U54 Schema.org JSON-LD structured anchors engine'"
   ```
