# Phase 30: Omniscient Runtime Master Gate & Reaper — Implementation Checklist

> **Phase Directory**: `phase_30_omniscient_runtime_master_gate_reaper`  
> **Status**: Ready for Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase30_master_runtime_eval/scenario/live_omniscient.py`
- Target Symbol: `OmniscientKernelVerifier.HARD_CEILING_MIB`
- Module Stems: `live_omniscient`
- Required Skills: `karpathy-surgical-diff`, `viking-retrieval`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - **Hypothesis**: In `OmniscientKernelVerifier`, `HARD_CEILING_MIB` is set to `481.2` due to a missing digit typographical defect. Updating it to `float(os.environ.get("HERMES_VRAM_CEILING_MIB", "5400.0"))` aligns hardware health telemetry with the 5,400.0 MiB discrete GPU ceiling.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Target is in Domain C git repository).
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
