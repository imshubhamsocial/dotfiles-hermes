---
name: phase19-looped-latent-deliberator
phase: "Phase 19"
authority: "In-Engine Looped Prefill & Latent Attractors"
description: "Looped prefill latent attractor gate"
---
# Looped Latent Deliberator

This skill guides deep System-2 recurrent hidden-state deliberation using looped transformer prefill and fixed-point attractor convergence on Port 8138.

## Mathematical Principle of Latent Thought Attractors

Under **Phase 19 Latent Thought Attractors** (Google DeepMind *Reasoning with Latent Thoughts*, Apple AI *LoopCD* arXiv:2610.02185), prefill and latent deliberation iterate through shared recurrent transformer layers across $k \in [1, K_{\max}]$ recurrent passes:

$$h_t^{(k)} = \text{LayerNorm}\left(h_t^{(k-1)} + \mathcal{F}_{\text{shared}}\left(h_t^{(k-1)}\right)\right)$$

The recurrent scheduler evaluates the **Fixed-Point Attractor Convergence Criterion**:

$$\Delta^{(k)} = \|h^{(k)} - h^{(k-1)}\|_2 < \epsilon \quad \text{where } \epsilon \in [10^{-4}, 10^{-2}]$$

## Operational Protocol & Invariants

1. **Entropy Assessment**: When an incoming problem exhibits high constraint density (e.g., deadlock cycle analysis, multi-variable constraint satisfaction, or dependency graphs), escalate from single-pass prefill to looped deliberation ($K \in [2, 6]$).
2. **Convergence Gate Mandatory**: Track hidden-state residual displacement $\Delta^{(k)} = \|h^{(k)} - h^{(k-1)}\|_2$. Deliberation must iterate until $\Delta^{(k)} < \epsilon$ ($\epsilon = 0.01$) is stabilized or maximum budget $K_{\max} = 6$ is exhausted. The solver must never prematurely halt at loop $k=1$ or arbitrary step counts without verifying convergence.
3. **Hardware Zero-Delta Guarantee**: Enforce `last_loop` KV cache overwriting to guarantee 0 MiB CUDA memory footprint expansion during recurrent iterations.
4. **Slot Cache Re-use**: Maintain warm system prompt prefix in `.hermes/cache/slots` to achieve $\ge 85.0\%$ prefill cache hits.
5. **Contractive State Normalization**: In recurrent updates, apply contractive mapping (Lipschitz constant $< 1$) and vector normalization (`_layer_norm` or contractive convex combination) so residual displacement monotonically decreases below $\epsilon$ within the 6-loop budget.
