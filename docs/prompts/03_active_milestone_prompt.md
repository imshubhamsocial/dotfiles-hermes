# 03. Active Milestone Prompt: U45 (Modular System Prompt Engine & Context Compactor Gate)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U45`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/01_anthropic_system_prompts.md` & `13_perplexity_local_first_and_openskills.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U45`)

Refactor the prompt construction engine in `hermes` to replace monolithic string concatenation with **Anthropic-style modular prompt slotting** and implement a **Perplexity-style active context compaction gate**:

1. **Modular Prompt Slotting Engine (`src/hermes_core/prompt_slotting.py` or `hermes_cli/prompt_slotting.py`)**:
   * Break system instructions into 4 immutable, orthogonal slots:
     * **Slot 1: Identity & Persona Isolation** (Strict operational boundaries, non-intrusive refusal).
     * **Slot 2: Environmental & Hardware Bounds** (Local RTX 3050, 64k context, Btrfs NOCOW, `/dev/shm`).
     * **Slot 3: Master Behavioral Invariants & Coding Laws** (AST containment, zero-sorry testing, relative paths).
     * **Slot 4: Tool Definitions & Native Jinja Schema** (Gemma-4 tool-calling format).
   * **Prefix-Cache Byte Alignment**: Ensure static slots sit strictly at byte-offset 0 so `llama-server` achieves $>90\%$ KV-cache prefix hits across multi-turn sessions.

2. **Active Context Compactor Gate (`src/hermes_core/context_compactor.py`)**:
   * Monitor active trajectory token volume during multi-turn sessions.
   * When conversational history / stale tool outputs approach $\ge 4,000\text{ tokens}$, automatically compact stale turns into concise semantic summaries so Gemma-4 stays within its peak cognitive reasoning window.

---

## 2. Implementation Deliverables

* `src/hermes_core/prompt_slotting.py`: Modular prompt slot engine with ordering, validation, and rendering.
* `src/hermes_core/context_compactor.py`: Active context compactor gate with token thresholding and summary generation.
* Integration into CLI agent loop (`src/hermes_core/agent.py` or `hermes_cli/agent.py`).

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u45_prompt_slotting_and_compactor.py` asserting:
1. `test_prompt_slots_render_in_strict_canonical_order()`: Validates Slots 1 through 4 ordering.
2. `test_prefix_cache_byte_stability()`: Validates identical hash output on static slots across turns.
3. `test_slot_injection_and_override_protection()`: Validates user messages cannot overwrite Slot 1/3 invariants.
4. `test_context_compactor_triggers_at_threshold()`: Validates compaction triggers when token count $\ge 4,000$.
5. `test_context_compactor_preserves_most_recent_turn_and_plan()`: Validates active diffs and plan state are preserved verbatim during compaction.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- pytest tests/harness_contracts/test_roadmap4_u45_prompt_slotting_and_compactor.py -v
   distrobox enter ws-hermes -- pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 309 existing tests + new U45 tests.
3. Verify **$0\text{ MB GPU VRAM}$** overhead.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add <modified_files> && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U45 modular prompt slotting engine and active context compactor gate'"
   ```
