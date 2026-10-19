---
name: looped-latent-deliberator
description: "Looped prefill latent attractor gate"
---

# Looped Latent Deliberator

This skill guides deep System-2 recurrent hidden-state deliberation using looped transformer prefill and fixed-point attractor convergence on Port 8138.

## Operational Protocol

1. **Entropy Assessment**: When an incoming problem exhibits high constraint density (e.g., deadlock cycle analysis, 5-variable constraint satisfaction, or multi-step logic), escalate from single-pass prefill to looped deliberation ($K \in [2, 6]$).
2. **Attractor Convergence Check**: Track hidden-state residual displacement $\Delta^{(k)} = \|h^{(k)} - h^{(k-1)}\|_2$. Deliberation terminates when $\Delta^{(k)} < \epsilon$ ($\epsilon = 0.01$) or at $K_{\max}$.
3. **Hardware Zero-Delta Guarantee**: Enforce `last_loop` KV cache overwriting to guarantee 0 MiB CUDA memory footprint expansion during recurrent iterations.
4. **Slot Cache Re-use**: Maintain warm system prompt prefix in `.hermes/cache/slots` to achieve $\ge 85.0\%$ prefill cache hits.
