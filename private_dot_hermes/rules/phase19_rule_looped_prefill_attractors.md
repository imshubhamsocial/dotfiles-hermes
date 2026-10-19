---
phase: "Phase 19"
authority: "In-Engine Looped Prefill & Latent Thought Attractors"
testbed: "tests/phase19_looped_attractor_eval/"
status: "Operational & Certified"
---

# Behavioral Invariant: In-Engine Looped Prefill & Latent Thought Attractors (Phase 19)

> **Authority**: Google Research & DeepMind (*Reasoning with Latent Thoughts: On the Power of Looped Transformers*), Apple AI *LoopCD* (arXiv:2610.02185), NVIDIA Dory Recurrent Core.  
> **Hardware Boundary**: Port 8138 `llama-server-dory`, RTX 3050 (6GB VRAM, $\le 4,812$ MiB Active Ceiling), `0 MiB CUDA Delta`.

---

## 1. Mathematical Principle of Latent Thought Attractors

Standard autoregressive language models execute single-pass static feedforward inference where computational depth scales strictly linearly with token length $T$. In complex systems programming, concurrency verification, and constraint satisfaction, single-pass prefill fails to resolve high-entropy dependency graphs.

Under **Phase 19 Latent Thought Attractors**, prefill and latent deliberation iterate through shared recurrent transformer layers $\mathcal{F}_{\text{shared}}$ across $k \in [1, K_{\max}]$ recurrent passes:

$$h_t^{(k)} = \text{LayerNorm}\left(h_t^{(k-1)} + \mathcal{F}_{\text{shared}}\left(h_t^{(k-1)}\right)\right)$$

The recurrent scheduler must evaluate the **Fixed-Point Attractor Convergence Criterion**:

$$\Delta^{(k)} = \|h^{(k)} - h^{(k-1)}\|_2 < \epsilon \quad \text{where } \epsilon \in [10^{-4}, 10^{-2}]$$

### Invariant Rules for Recurrent Deliberation:
1. **Convergence Gate Mandatory**: The solver must never prematurely halt at loop $k=1$ or fixed loop counts without validating that the latent displacement $\Delta^{(k)} < \epsilon$ has stabilized or maximum deliberation budget $K_{\max}$ is exhausted.
2. **KV Cache Overwrite Parity**: Memory for recurrent iterations must utilize `last_loop` KV cache overwriting to guarantee **0 MiB CUDA VRAM delta** regardless of the number of recurrent iterations.
3. **Prefix Pinned Reuse**: Common system prompt prefixes and invariant harness contracts must reside in pinned slots (`--slot-save-path ~/.hermes/cache/slots`), achieving $\ge 85.0\%$ prefill cache reuse across iterative cycles.
4. **Accuracy Gain Bound**: Deep looped recurrent execution must achieve a relative accuracy gain of $\ge +15.0\%$ over single-pass shallow execution on multi-constraint logic and deadlock graphs.
