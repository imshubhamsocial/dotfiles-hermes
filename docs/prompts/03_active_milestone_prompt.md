# 03. Active Milestone Prompt: U57 (Unified Reactive Execution & Memory Bus)

> **Current Execution Target**: Milestone 4 Phase 2 — Specification `U57`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U57`)

Implement the **Unified Reactive Execution & Memory Bus Subsystem** (`src/hermes_core/synergy_bus.py`):

1. **Unified Reactive Event Bus**:
   * Bridges ADK 2.0 TaskDAG (`reflective_learner.py`), OpenViking VFS (`openviking_vfs.py`), OpenCode-Mem Vector Store (`vector_memory.py`), and Tree-sitter Codebase MCP into a single asynchronous event stream.
   * Dispatches lifecycle events (`TASK_SPAWN`, `TOOL_CALL`, `VFS_MUTATION`, `MEMORY_RECALL`, `VERIFICATION_GATE`).

2. **Zero-Token Telemetry & State Consistency**:
   * Propagates memory state without blowing prompt token budgets.
   * Fast event emission with $\le 5\text{ms}$ dispatch latency.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution with **$0\text{ MB GPU VRAM}$** overhead.

---

## 2. Implementation Deliverables

* `src/hermes_core/synergy_bus.py`: Reactive event bus integrating TaskDAG, VFS, and Vector Memory.
* Integration into the core execution runtime.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u57_synergy_bus.py` asserting:
1. `test_synergy_bus_event_subscription_and_dispatch()`: Validates multi-subscriber async event broadcasting.
2. `test_synergy_bus_vfs_and_memory_event_wiring()`: Validates automatic VFS mutation and vector memory indexing on bus events.
3. `test_synergy_bus_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives (4-Step Lifecycle)

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u57_synergy_bus.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Execute live native upstream Hermes verification turn:
   ```bash
   distrobox enter ws-hermes -- hermes -z "Hermes Unified Synergy Event Bus probe" --yolo --usage-file /dev/shm/usage.json
   ```
3. Ensure **100% pass rate** across all 550 existing tests + new U57 tests.
4. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/synergy_bus.py tests/harness_contracts/test_roadmap4_u57_synergy_bus.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U57 Unified Reactive Execution and Memory Bus'"
   ```
