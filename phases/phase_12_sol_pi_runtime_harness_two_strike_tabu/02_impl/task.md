# Phase 12: SoL-Pi Runtime Harness & Two-Strike Tabu — Implementation Checklist

> **Phase Directory**: `phase_12_sol_pi_runtime_harness_two_strike_tabu`  
> **Status**: Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- **Target File**: `tests/phase12_sol_pi_eval/scenario/data_pipeline.py`
- **Target Symbol**: `DataPipeline.process_record`
- **Causal Hypothesis**: Line 31 `event_id = first_event["event_id"]` raises `KeyError` when processing legacy records formatted with key `"id"` instead of `"event_id"`. Using safe lookup `first_event.get("event_id") or first_event.get("id", "UNKNOWN")` eliminates the `KeyError` and allows the data pipeline to succeed.
- **Karpathy U12 Limit**: Single causal mutation <= 15 lines diff.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis for `DataPipeline.process_record`.
- [ ] Step 2: Ensure shadow backup (`<target>.hermes.bak`) exists.
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 diff limit (<= 15 lines).
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
