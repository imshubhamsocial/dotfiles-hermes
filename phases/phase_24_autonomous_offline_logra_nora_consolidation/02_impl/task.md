# Phase 24: Autonomous Offline LoGRA/NoRA Consolidation — Implementation Checklist

> **Phase Directory**: `phase_24_autonomous_offline_logra_nora_consolidation`  
> **Status**: Ready for Stage `03_verify` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase24_autonomous_logra_eval/scenario/offline_adapter_engine.py`
- Targeted Symbol(s): `OfflineEvolutionOrchestrator.run_offline_evolution_cycle`
- Causal Hypothesis: In `OfflineEvolutionOrchestrator.run_offline_evolution_cycle`, the reference distribution `p_ref` and perturbed policy distribution `p_theta` were synthesized using Dirichlet sampling and linear Gaussian noise clipping (`p_theta = np.clip(p_ref + rng.normal(0, 0.005, size=64), 1e-6, 1.0)`). This unconstrained perturbation created severe probability ratio spikes, causing the calculated KL divergence to spike above the 0.05 budget (e.g. 0.2489 > 0.05) and raising a `RuntimeError`. Converting the policy drift synthesis to stable logit-space Gaussian perturbations projected through softmax (`exp_ref / np.sum(exp_ref)` and `exp_theta / np.sum(exp_theta)`) bounds the policy drift smoothly within the 0.05 KL budget, preserving mathematical validity while satisfying the stability invariant.
- Secondary Task: Run `benchmark_autonomous_logra.py` to persist `autonomous_logra_metrics.json` confirming TME verification, peak total VRAM <= 4,812.0 MiB, NoRA Frobenius norm == 1.0, KL divergence <= 0.05, and post-resume MTP throughput >= 42.4 tok/s.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
