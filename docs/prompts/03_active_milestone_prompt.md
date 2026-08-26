# 03. Active Milestone Prompt: U47 (OpenCode-Mem Local Vector Memory Engine & Episodic Recall)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U47`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/03_opencode_mem_persistent_memory.md` & `09_openviking_context_database.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U47`)

Implement the **OpenCode-Mem Local Vector Memory Engine & Episodic Recall Subsystem** (`src/hermes_core/opencode_mem.py`) to provide persistent cross-session episodic memory and negative constraint retrieval using FastEmbed CPU ONNX embeddings with **$0\text{ MB GPU VRAM}$** overhead:

1. **Local Embeddings & Vector Storage (`src/hermes_core/opencode_mem.py`)**:
   * Use **FastEmbed (BGE-Small-EN-v1.5 / MiniLM CPU ONNX)** for deterministic text embedding generation on CPU.
   * Persist episodic memories, architectural conventions, past failure traces, and negative constraints into SQLite WAL (`.hermes/memories.db`).
   * Implement cosine similarity vector search in pure NumPy / CPU memory with sub-millisecond latency.

2. **Cross-Session Retrieval & Negative Constraint Sieve**:
   * On new task intake, automatically query `.hermes/memories.db` with the user prompt.
   * Retrieve top-$K$ ($K=3$) relevant past episodes and negative constraints (e.g. *"In this repo, always use relative imports"* or *"Do not use library X"*).
   * Format retrieved memories as a compact injection into Slot 3 (Behavioral Invariants) consuming $<200\text{ tokens}$.

3. **Strict Hardware Envelope Bounds**:
   * **$0\text{ MB GPU VRAM}$**: Embeddings must execute strictly on host CPU threads.
   * **Fast Startup**: In-memory vector index with SQLite disk persistence.

---

## 2. Implementation Deliverables

* `src/hermes_core/opencode_mem.py`: OpenCode-Mem episodic vector memory engine with SQLite WAL persistence and FastEmbed CPU support.
* Integration into Prompt Slotting (`src/hermes_core/prompt_slotting.py`) to inject retrieved episodic constraints into Slot 3.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u47_vector_memory.py` asserting:
1. `test_opencode_mem_embedding_generation()`: Validates deterministic CPU vector embedding generation.
2. `test_episodic_memory_storage_and_sqlite_persistence()`: Validates storing, updating, and reloading memories from SQLite.
3. `test_semantic_vector_recall_top_k()`: Validates semantic similarity search returns top-3 relevant constraints.
4. `test_negative_constraint_injection_into_slot3()`: Validates retrieved constraints correctly inject into Slot 3 without overwriting master laws.
5. `test_vector_memory_zero_gpu_vram()`: Validates $0\text{ MB GPU VRAM}$ consumed during indexing and querying.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u47_vector_memory.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 366 existing tests + new U47 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/opencode_mem.py tests/harness_contracts/test_roadmap4_u47_vector_memory.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U47 OpenCode-Mem local vector memory engine and episodic recall'"
   ```
