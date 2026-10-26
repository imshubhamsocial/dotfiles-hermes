# Phase 17: Hibernate-and-Train LoGRA/NoRA \+ GrowMTP — Implementation Checklist

> **Phase Directory**: `phase_17_hibernate_and_train_logra_nora_growmtp`  
> **Status**: Completed Stage `02_impl`, ready for Stage `03_verify`  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase17_logra_nora_eval/scenario/logra_aligner.py`
- Target Symbol: `LoGRAAligner.initialize_nora_down_proj`
- Module Stems: `logra_aligner`
- Required Skills: `karpathy-surgical-diff`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - Causal hypothesis: `LoGRAAligner.initialize_nora_down_proj` returns unnormalized `a_matrix` with Frobenius norm ~362.0 instead of dividing by `compute_frobenius_norm(a_matrix)` to achieve `||A||_F == 1.0`. Normalizing `normalized_a = a_matrix / f_norm` and returning `normalized_a, final_norm` satisfies NoRA Frobenius normalization and satisfies unit tests and training telemetry assertions.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Domain C repo: shadow backup created at `tests/phase17_logra_nora_eval/scenario/logra_aligner.py.hermes.bak`).
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
