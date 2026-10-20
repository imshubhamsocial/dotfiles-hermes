# Invariant Rule: Phase 29 Live state.db Dream-RSI 2.0 & MASS Nightly Engine

> **Scope**: Layer 4 Invariant Rule (Phase 29)  
> **Authority**: Google DeepMind / UMD *Dream-RSI* (arXiv:2609.14858), Sakana AI *MASS* (arXiv:2610.12176), Google *RRSI* (arXiv:2609.24972)  
> **Hardware Boundary**: SQLite WAL read-only mode, 100% CPU RAM Evaluation, $\Delta \text{VRAM} \equiv 0.0\text{ MiB}$

## Operational Invariants

1. **Live state.db Ingestion & Content-Addressed Persistence**:
   - Trajectory mining must ingest directly from `.hermes/state.db` using read-only WAL queries, preserving operational database integrity.
   - Real multi-turn trajectories are serialized into content-addressed persistent replay trees indexed by root state hashes:
     $$\text{Path: } \texttt{.hermes/cache/dream_worlds/<sha256>.json}$$

2. **Off-Policy Doubly Robust Counterfactual Evaluation**:
   - Candidate skill, prompt, and rule mutations are evaluated counterfactually across stored replay trees without executing live LLM completions.
   - Off-policy evaluation applies Doubly Robust estimation:
     $$\hat{V}_{\text{DR}}(\pi) = \sum_{t=0}^T \gamma^t \left[ \sum_a \pi(a \mid s_t) \hat{Q}(s_t, a) + \frac{\pi(a_t \mid s_t)}{\mu(a_t \mid s_t)} \left( r_t - \hat{Q}(s_t, a_t) \right) \right]$$
   - Call reduction ratio must satisfy $\frac{N_{\text{simulated}} + N_{\text{live}}}{N_{\text{live}}} \ge 2.0$.

3. **RRSI Variance Stability Gate**:
   - Candidate mutations must exceed the empirical noise margin before live promotion:
     $$\Delta R - 1.96 \cdot \text{SE} > 0$$
   - Rejects spurious rule creep and hallucinations before promotion to `.hermes/rules/`.

4. **Zero CUDA Delta & Epistemic Receipt Closure**:
   - All trajectory ingestion, serialization, and counterfactual value estimations execute 100% on CPU RAM at 0.0 MiB CUDA VRAM delta.
   - Any promoted rule or skill mutation requires held-out testbed verification with exit code 0 and cryptographic receipt sealing.
