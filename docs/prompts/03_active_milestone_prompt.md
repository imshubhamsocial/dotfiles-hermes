# 03. Active Milestone Prompt: Roadmap 4 Phase 1 (U45 – U56)

> **Current Execution Target**: Milestone 4 Phase 1 Component Implementations  
> **Authoritative Specification**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/`

---

## Instructions for Codex / Execution Agent

You are tasked with executing the milestones of **Roadmap 4 (Frontier Cognitive OS)** sequentially. Follow these strict operational directives:

### Execution Protocol

1. **One Milestone at a Time**:
   * Implement the component specified in the active milestone (e.g., `U45: Modular Prompt Slotting`).
   * Author its dedicated contract test in `tests/harness_contracts/test_roadmap4_<spec>.py`.

2. **Verify Against Contract Suite**:
   * Run the test suite inside `ws-hermes`:
     ```bash
     distrobox enter ws-hermes -- pytest tests/harness_contracts/ -q
     ```
   * Ensure that **100% of tests pass** (all existing 309 tests + new milestone tests).

3. **Check Hardware Safety & Constraints**:
   * Verify that no GPU VRAM is consumed for tools or embeddings ($0\text{ MB GPU}$ overhead).
   * Verify all paths are 100% relative and portable.

4. **Stage Changes in Chezmoi**:
   * After verification passes, stage and commit the milestone cleanly:
     ```bash
     distrobox enter ws-hermes -- bash -c "chezmoi add <modified_files> && chezmoi git -- add -A && chezmoi git -- commit -m '<commit_message>'"
     ```

---

## Next Milestone in Queue: `U45` (Anthropic-Style Modular System Prompt Engine)

* **Goal**: Implement `hermes_core/prompt_slotting.py` replacing monolithic prompt strings with cache-aligned slots (`Identity`, `Environment`, `BehavioralLaws`, `ToolDefinitions`).
* **Contract Test**: `tests/harness_contracts/test_roadmap4_u45_prompt_slotting.py` asserting slot order, immutable boundary headers, and prefix-cache byte alignment.
