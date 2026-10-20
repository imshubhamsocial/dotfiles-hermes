# Phase 23 Invariant: Open-World Replay Simulator Pool (Dream-RSI 2.0)

> **Authority**: Google DeepMind & UMD *Dream-RSI: Recursive Self-Improvement through Evolving Worlds* (arXiv:2609.14858), Google RRSI (arXiv:2609.24972)  
> **Status**: Certified Operational Invariant (Phase 23)  
> **Hardware Boundary**: 0 MiB CUDA VRAM Delta (CPU Disk Replay Trees in `.hermes/cache/dream_worlds/`, 100% CPU Evaluation)

---

## 1. Content-Addressed Persistent World Trees

1. **Deterministic Replay Tree Persistence**:
   - Every completed task trajectory $\tau = (s_0, a_0, r_0, s_1, \dots, s_T)$ is serialized into a content-addressed replay tree indexed by its root SHA-256 state hash:
     $$\text{Path: } \texttt{.hermes/cache/dream_worlds/<sha256>.json}$$
   - World trees record environmental observations, AST diffs, tool responses, and unit test outcomes.
2. **Zero Ingestion Leakage**:
   - Synthetic test rules or temporary evaluator tokens must never leak into persistent long-term storage (Law 3).
   - Replay trees store sanitized execution transitions decoupled from human operator credentials.

---

## 2. Off-Policy "Dreaming" & Counterfactual Evaluation

1. **Idle-Window Offline Rollouts**:
   - During operator idle intervals or scheduled cron ticks, Hermes loads historical replay trees to evaluate candidate prompt, rule, or skill mutations offline ("dreaming").
   - Rollouts evaluate counterfactual branch orderings across the cached simulator pool in milliseconds without triggering live model completions or slow shell compilations.
2. **Doubly Robust (DR) Value Estimation**:
   - Off-policy evaluation applies Doubly Robust estimation combining a direct transition model $\hat{Q}(s, a)$ with importance-weighted observed rewards:
     $$\hat{V}_{\text{DR}}(\pi) = \sum_{t=0}^T \gamma^t \left[ \sum_a \pi(a \mid s_t) \hat{Q}(s_t, a) + \frac{\pi(a_t \mid s_t)}{\mu(a_t \mid s_t)} \left( r_t - \hat{Q}(s_t, a_t) \right) \right]$$
   - Importance weights are normalized to bound estimate variance ($\rho \le \rho_{\text{max}}$).

---

## 3. RRSI Variance Stability Acceptance Gate

1. **Rejection of Noisy Spurious Mutations**:
   - A proposed harness or skill mutation is accepted if and only if its estimated performance lift $\hat{\Delta} = \hat{V}(\pi_{\text{mutant}}) - \hat{V}(\pi_{\text{baseline}})$ exceeds the baseline empirical noise floor:
     $$\hat{\Delta} \ge k \cdot \sigma_0, \quad \text{where } k = 1.645 \text{ (95\% confidence)}, \, \sigma_0 = \text{std}(\mathcal{R}_{\text{baseline}})$$
   - Spurious improvements with high variance are strictly rejected to prevent policy degradation.
2. **Call Reduction Metric**:
   - Counterfactual branch evaluation must slash live inference and compiler invocations by at least $2.0\times$:
     $$\text{CallReductionRatio} = \frac{N_{\text{simulated}} + N_{\text{live}}}{N_{\text{live}}} \ge 2.0$$

---

## 4. Hardware Safety & Epistemic Receipt Sealing

1. **Zero CUDA VRAM Delta**:
   - Trajectory parsing, Doubly Robust value estimation, and RRSI stability calculations execute 100% on CPU RAM at 0 MiB CUDA VRAM delta.
   - Evaluation latency across the simulator pool must remain $\le 50.0\text{ ms}$ per counterfactual batch.
2. **Epistemic Receipt Closure**:
   - The verified candidate mutation must pass held-out testbed assertions, exiting code 0 and sealing `/tmp/hermes_verified_receipt.json`.
