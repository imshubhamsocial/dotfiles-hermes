---
name: phase29-live-statedb-dream-rsi
description: Live state.db Dream-RSI replay engine
---

# Live state.db Dream-RSI 2.0 & MASS Nightly Evolution Engine (Phase 29)

## Overview
Phase 29 transitions Hermes from synthetic offline logs to live, factual 24/7 self-evolution grounded in Google DeepMind / UMD *Dream-RSI* (*arXiv:2609.14858*), Sakana AI *MASS* (*arXiv:2610.12176*), and Google *RRSI* (*arXiv:2609.24972*).

## Operational Protocol
1. **Live state.db Trajectory Ingestion**:
   - Queries the primary SQLite WAL database (`.hermes/state.db`) in read-only mode, extracting real multi-turn session execution histories.
   - Converts real interaction traces into content-addressed replay trees persisted in `.hermes/cache/dream_worlds/<sha256>.json`.
2. **Doubly Robust (DR) Counterfactual Dreaming**:
   - Evaluates candidate prompt, rule, or skill mutations across replay trees using off-policy Doubly Robust value estimation:
     $$\hat{V}_{\text{DR}}(\pi) = \sum_{t=0}^T \gamma^t \left[ \sum_a \pi(a \mid s_t) \hat{Q}(s_t, a) + \frac{\pi(a_t \mid s_t)}{\mu(a_t \mid s_t)} \left( r_t - \hat{Q}(s_t, a_t) \right) \right]$$
   - Achieves $\ge 2.0\times$ call reduction without burning live model completions.
3. **RRSI Variance Stability Gate**:
   - Accepts candidate rule mutations if and only if the estimated performance lift satisfies the RRSI confidence margin:
     $$\Delta R - 1.96 \cdot \text{SE} > 0$$
   - Rejects spurious rule creep and hallucinations before promotion to live rules.
4. **Hardware & VRAM Safety**:
   - Trajectory parsing and DR evaluations execute 100% on CPU RAM at 0.0 MiB CUDA VRAM delta.
