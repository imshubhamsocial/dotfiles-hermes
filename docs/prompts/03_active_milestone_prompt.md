# 03. Active Milestone Prompt: U58 (Closed-Loop Dual-Agent Verification Matrix)

> **Current Execution Target**: Milestone 4 Phase 2 — Specification `U58`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U58`)

Implement the **Closed-Loop Dual-Agent Verification Matrix Subsystem** (`src/hermes_core/verification_matrix.py`):

1. **Multi-Tier Pre-Flight Audit Matrix**:
   * Combines AST Syntax & Brace Verification (`DraftDetective.validate_code_ast`), Adversarial Claim Grounding (`DraftDetective.verify_claims`), and COG Worker/Verifier closed-loop consensus.
   * Eliminates single-agent self-grading bias through strict adversarial cross-examination.

2. **2-Strike Tabu Rollback Trigger**:
   * Automatically tracks consecutive verification rejections on file diffs and triggers clean git revert to parent commit upon 2 consecutive failures.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$) with sub-$100\text{ms}$ audit latency.

---

## 2. Implementation Deliverables

* `src/hermes_core/verification_matrix.py`: Dual-agent pre-commit audit matrix and 2-strike tabu pruner.
* Integration into the Pre-Commit Observer Gate.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u58_verification_matrix.py` asserting:
1. `test_verification_matrix_full_approval_pass()`: Validates clean approval when AST, claims, and verifier agree.
2. `test_verification_matrix_rejection_on_ast_or_claim_failure()`: Rejects diffs with broken syntax or phantom file claims.
3. `test_two_strike_tabu_pruner_trigger()`: Triggers tabu rollback after 2 consecutive failures.
4. `test_verification_matrix_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u58_verification_matrix.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes Dual-Agent Closed-Loop Verification Matrix probe" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 553 existing tests + new U58 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/verification_matrix.py tests/harness_contracts/test_roadmap4_u58_verification_matrix.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U58 Closed-Loop Dual-Agent Verification Matrix'"
   ```
