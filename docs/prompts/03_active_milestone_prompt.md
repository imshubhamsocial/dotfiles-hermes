# 03. Active Milestone Prompt: U53 (Volcengine OpenViking Hierarchical VFS Context Database)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U53`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/09_openviking_context_database.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U53`)

Implement the **Volcengine OpenViking Hierarchical Virtual Filesystem Context Database** (`src/hermes_core/openviking_vfs.py`):

1. **Hierarchical Virtual Filesystem (`viking://`)**:
   * Replaces flat memory stores with a virtual directory tree (`viking://core/`, `viking://skills/`, `viking://plans/`).
   * Supports standard POSIX-like operations (`ls`, `find`, `cat`, `tree`) across memory nodes.

2. **3-Tier Context Representation (L0 / L1 / L2)**:
   * **L0 (Abstract)**: $\le 100\text{ tokens}$ ultra-compact discovery summary for fast routing.
   * **L1 (Overview)**: $\le 2,000\text{ tokens}$ structural outline for architectural planning.
   * **L2 (Full Detail)**: Unabridged node content loaded JIT on demand.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution with **$0\text{ MB GPU VRAM}$** overhead.

---

## 2. Implementation Deliverables

* `src/hermes_core/openviking_vfs.py`: OpenViking VFS database engine and 3-tier retrieval subsystem.
* Integration into the Hermes context retrieval pipeline.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u53_openviking_vfs.py` asserting:
1. `test_openviking_vfs_mount_and_navigation()`: Validates `viking://` URI routing, `ls`, `tree`, and `find`.
2. `test_openviking_three_tier_resolution()`: Validates L0 ($\le 100\text{ tok}$), L1 ($\le 2,000\text{ tok}$), and L2 on-demand resolution.
3. `test_openviking_directory_recursive_search()`: Validates subtree pruning and token-efficient search.
4. `test_openviking_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u53_openviking_vfs.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 528 existing tests + new U53 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/openviking_vfs.py tests/harness_contracts/test_roadmap4_u53_openviking_vfs.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U53 OpenViking hierarchical VFS context database'"
   ```
