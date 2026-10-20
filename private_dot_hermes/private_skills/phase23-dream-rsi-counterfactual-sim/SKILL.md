---
name: dream-rsi-counterfactual-sim
description: "Dream-RSI 2.0 counterfactual replay"
---

# Dream-RSI 2.0 Counterfactual Replay Simulator

## Purpose
Simulates counterfactual execution branches and evaluates candidate harness mutations offline during idle windows using persistent disk replay trees (`.hermes/cache/dream_worlds/`), Doubly Robust off-policy value estimation, and RRSI stability acceptance gates ($\hat{\Delta} \ge k \cdot \sigma_0$), achieving $\ge 2.0\times$ call reduction at 0 MiB CUDA VRAM delta.

## When to Hydrate
Hydrate this skill when:
- Evaluating competing prompt contracts, tabu rules, or toolchain playbooks without wasting live inference tokens.
- Conducting idle-window continuous self-improvement cycles across historical task trajectories.
- Validating whether a candidate skill or invariant mutation offers statistically significant lift over baseline variance.

## Execution Protocol

1. **Replay Tree Indexing**:
   - Ingest session traces into content-addressed JSON replay trees: `.hermes/cache/dream_worlds/<sha256>.json`.
   - Index state transitions $(s_t, a_t, r_t, s_{t+1})$ with deterministic environmental observations.

2. **Doubly Robust Off-Policy "Dreaming"**:
   - Evaluate candidate mutation policy $\pi$ against logged baseline behavior $\mu$.
   - Compute Doubly Robust estimate with normalized importance weights.
   - Execute counterfactual batch rollout in $\le 50.0\text{ ms}$ on CPU RAM.

3. **RRSI Variance Stability Gate**:
   - Compute baseline standard error $\sigma_0$ across historical trajectory rewards.
   - Enforce acceptance condition: $\hat{\Delta} = \hat{V}(\pi) - \hat{V}(\mu) \ge 1.645 \cdot \sigma_0$.
   - Reject candidates failing the variance gate as spurious statistical noise.

4. **Verification & Epistemic Receipt**:
   - Assert $\text{CallReductionRatio} \ge 2.0\times$ and 0 MiB CUDA VRAM delta.
   - Execute verification suite to exit code 0 and seal cryptographic receipt.
