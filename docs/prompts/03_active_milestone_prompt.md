# 03. Active Milestone Prompt: U55 (Draft-Detective Adversarial Fact-Checker & AST Verification Gates)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U55`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/11_draft_detective_and_graft.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U55`)

Implement the **Draft-Detective Adversarial Fact-Checker & AST Verification Gates Engine** (`src/hermes_core/draft_detective.py`):

1. **Adversarial Claim Verification**:
   * Scans agent markdown summaries, plan descriptions, and PR notes to extract factual assertions (file references, symbol declarations, test claims).
   * Cross-references claims against real filesystem ground truth and AST trees to flag hallucinations or phantom links.

2. **AST-Aware Structural Code Transformation (Graft Kernel)**:
   * Analyzes syntax validity, brace balance, and symbol linkage before commit.
   * Feeds compiler diagnostic lines directly back into the repair loop.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution ($0\text{ MB GPU VRAM}$) with $\le 50\text{ms}$ audit latency.

---

## 2. Implementation Deliverables

* `src/hermes_core/draft_detective.py`: Draft-Detective adversarial fact-checker and AST pre-commit auditor.
* Integration into the Observer Gate and Verification Pipeline.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u55_draft_detective.py` asserting:
1. `test_claim_extraction_and_verification()`: Validates ground truth matching against existing workspace files.
2. `test_hallucinated_file_claim_detection()`: Flags phantom file or symbol claims as verification violations.
3. `test_ast_structural_transformation_gate()`: Validates syntax and symbol integrity checking.
4. `test_draft_detective_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u55_draft_detective.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes Draft-Detective adversarial verification turn" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 541 existing tests + new U55 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/draft_detective.py tests/harness_contracts/test_roadmap4_u55_draft_detective.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U55 Draft-Detective adversarial fact-checker and AST verification gates'"
   ```
