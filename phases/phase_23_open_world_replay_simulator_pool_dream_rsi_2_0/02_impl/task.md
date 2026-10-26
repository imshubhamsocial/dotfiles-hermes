# Phase 23: Open-World Replay Simulator Pool (Dream-RSI 2.0) — Implementation Checklist

> **Phase Directory**: `phase_23_open_world_replay_simulator_pool_dream_rsi_2_0`  
> **Status**: Ready for Stage `03_verify` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase23_dream_rsi2_eval/scenario/replay_simulator.py`
- Targeted Symbol(s): `DoublyRobustEvaluator.evaluate`
- Causal Hypothesis: In `DoublyRobustEvaluator.evaluate`, the doubly robust step value `dr_step` was computed as `dr_step = q_hat + rho * (trans.reward - q_hat)` without weighting the direct model baseline `q_hat` by the target policy probability (`expected_q = pi_prob * q_hat`). This inflated baseline evaluation values and deflated the estimated performance lift ($\Delta V$) below the RRSI noise variance margin ($k \cdot \sigma_0$), causing `check_stability` to reject candidate policies. Weighting the baseline by target policy probability (`expected_q = pi_prob * q_hat`) restores formal Doubly Robust estimation ($\hat{V}_{\text{DR}} = \mathbb{E}_{\pi}[\hat{Q}] + \rho (r - \hat{Q})$), yielding sufficient lift to pass the RRSI stability gate.
- Secondary Task: Run `benchmark_dream_rsi2.py` to persist `dream_rsi2_metrics.json` confirming 0.0 MiB CUDA delta, >= 2.0x call reduction, and <= 50.0 ms dream evaluation latency.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
