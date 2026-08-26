# 03. Active Milestone Prompt: U49 (COG Second Brain Markdown Vault & Closed-Loop Verifier)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U49`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/05_cog_second_brain.md` & `12_google_agent_architecture_and_workflows.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U49`)

Implement the **COG Second Brain Markdown Vault & Closed-Loop Dual-Agent Verifier Subsystem** (`src/hermes_core/cog_vault.py` / `src/hermes_core/cog_verifier.py`):

1. **Human-Readable Markdown Vault (`src/hermes_core/cog_vault.py`)**:
   * Pure Markdown-backed knowledge store under `.hermes/knowledge/` and `docs/knowledge/`.
   * Auto-formats and organizes persistent architectural insights, decision records (ADRs), module contracts, and verification evidence into clean Markdown with YAML frontmatter.
   * Eliminates opaque binary lock-in while providing sub-millisecond retrieval.

2. **Dual-Agent Closed-Loop Audit (`src/hermes_core/cog_verifier.py`)**:
   * Implements an asymmetric **Worker $\leftrightarrow$ Verifier** execution protocol:
     * **Worker Stage**: Drafts code modifications according to active `plan.json`.
     * **Verifier Stage**: Independent verification agent inspects AST syntax, executes contract test suites, asserts $0\text{ MB GPU VRAM}$ overhead, and records a structured Markdown verification receipt into `.hermes/knowledge/evidence/`.
   * A task cannot complete without a cryptographic/hash-verified `VERIFIED` verdict receipt from the Verifier.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 2. Implementation Deliverables

* `src/hermes_core/cog_vault.py`: Markdown knowledge vault manager with frontmatter indexing.
* `src/hermes_core/cog_verifier.py`: Closed-loop dual-agent verifier with receipt generation.
* Integration into the verification lifecycle.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u49_cog_verifier.py` asserting:
1. `test_cog_markdown_vault_storage_and_indexing()`: Validates Markdown vault read/write/indexing with YAML frontmatter.
2. `test_dual_agent_worker_verifier_protocol()`: Validates that code edits require Verifier receipt before closing task.
3. `test_verifier_evidence_receipt_generation()`: Validates deterministic formatting of Markdown verification receipts.
4. `test_verification_failure_rejects_and_reverts()`: Validates that test failures trigger rejection and prevent commit.
5. `test_cog_vault_zero_gpu_vram()`: Validates $0\text{ MB GPU VRAM}$ overhead.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u49_cog_verifier.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 445 existing tests + new U49 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/cog_vault.py src/hermes_core/cog_verifier.py tests/harness_contracts/test_roadmap4_u49_cog_verifier.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U49 COG second brain markdown vault and closed-loop verifier'"
   ```
