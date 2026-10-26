# Phase 21: Google ADK 2.9+ TaskDAG & A2A Federation — Implementation Checklist

> **Phase Directory**: `phase_21_google_adk_2_9_taskdag_a2a_federation`  
> **Status**: Completed Stage `02_impl`, ready for Stage `03_verify`  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase21_adk_taskdag_eval/scenario/taskdag_router.py`
- Target Symbol: `TaskDAGRouter.transfer_to_agent`
- Module Stems: `taskdag_router`
- Required Skills: `karpathy-surgical-diff`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - Causal hypothesis: `TaskDAGRouter.transfer_to_agent` bypasses raw telemetry sanitization, allowing raw terminal and stdout dumps to pollute `structured_payload` and accumulating context pollution tokens. Restoring the filtering condition so that raw log keys are summarized when `sanitize_logs=True` enforces the zero-context-pollution invariant (`context_pollution_tokens == 0`), passing `test_zero_context_pollution_a2a_transfer`, `test_end_to_end_dag_execution`, and `test_adk_taskdag_metrics`.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Domain C repo: shadow backup created at `tests/phase21_adk_taskdag_eval/scenario/taskdag_router.py.hermes.bak`).
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
