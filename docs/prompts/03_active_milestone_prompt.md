# 03. Active Milestone Prompt: U52 (Google DeepMind Recirculation Inference-Time Dynamical System-2 Engine)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U52`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/08_deepmind_recirculation.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U52`)

Implement the **Google DeepMind Recirculation Inference-Time Dynamical System-2 Engine** (`src/hermes_core/recirculation.py`):

1. **Training-Free Recurrent State Tracking**:
   * Operates directly on frozen models (Gemma-4-4B) during prefill and planning steps.
   * Multi-pass hidden state feedback loop propagating latent representations across recurrent planning iterations ($K \ge 2$).

2. **System-2 Dynamic Planning Loop**:
   * Intercepts pre-execution prompts to refine speculative hypotheses and eliminate hallucinated AST branches before token generation.
   * Recirculates intermediate latent embeddings to achieve $\ge 20\%$ reasoning quality lift on complex multi-file tasks.

3. **Strict Hardware Envelope Bounds**:
   * CPU ONNX / PyTorch vector recurrence math executing on RAMDisk with **$0\text{ MB GPU VRAM}$** contention.

---

## 2. Implementation Deliverables

* `src/hermes_core/recirculation.py`: DeepMind Recirculation state tracker and recurrent prefill hook.
* Integration into the Hermes planning and hypothesis loop.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u52_recirculation.py` asserting:
1. `test_recirculation_state_initialization()`: Validates recurrent state container and hidden activation buffers.
2. `test_recurrent_prefill_iteration_pass()`: Validates $K$-pass dynamic recurrence step transformation.
3. `test_recirculation_reasoning_lift()`: Asserts $\ge 20\%$ variance reduction / belief convergence across recurrent iterations.
4. `test_recirculation_zero_gpu_vram()`: Enforces pure CPU RAMDisk execution ($0\text{ MB GPU VRAM}$).

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u52_recirculation.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 520 existing tests + new U52 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/recirculation.py tests/harness_contracts/test_roadmap4_u52_recirculation.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U52 Google DeepMind Recirculation inference-time dynamical system-2 engine'"
   ```
