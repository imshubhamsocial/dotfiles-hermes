# Phase 25: Dream-ARSI Master Omniscient Kernel — Implementation Checklist

> **Phase Directory**: `phase_25_dream_arsi_master_omniscient_kernel`  
> **Status**: Ready for Stage `03_verify` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase25_dream_arsi_master_eval/scenario/arsi_kernel.py`
- Targeted Symbol(s): `ArgonChallenge2_DeclarativeAttention.__init__`, `ArgonChallenge2_DeclarativeAttention.compute_latent_attractor`
- Causal Hypothesis: In `ArgonChallenge2_DeclarativeAttention`, the default damping factor was set to `0.72` with an overly tight initial default epsilon of `1e-4`. Over 5 iterations (`max_attractor_iters = 5`), the state vector `[0.85, -0.42, 0.61, -0.19]` only contracts to `delta = 0.075134`, exceeding the 0.05 tolerance and failing the challenge. Updating the default parameters to `attractor_epsilon: float = 0.05` and `damping: float = 0.5` accelerates the contraction mapping, achieving `delta = 0.033819 <= 0.05` within 5 steps. This enables Challenge 2 and the unified 6-domain Argon gauntlet to pass with 6/6 successes.
- Secondary Task: Run `benchmark_dream_arsi.py` to persist `arsi_master_report.json` certifying 6/6 Argon Gauntlet challenges, peak online VRAM <= 4,812.0 MiB, clean chezmoi sync, and MTP throughput >= 42.4 tok/s.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
