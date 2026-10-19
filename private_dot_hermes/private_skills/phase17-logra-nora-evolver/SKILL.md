---
name: phase17-logra-nora-evolver
phase: "Phase 17"
authority: "TTC Scaling & Hibernate LoGRA/NoRA"
description: "LoGRA NoRA hibernate weight evolver"
---
# LoGRA & NoRA Weight Evolver Playbook (Phase 17)

When executing offline adapter or draft-head parameter evolution under `<focus id="weight_evolution">`:

1. **Temporal Mutual Exclusion & Hardware Boundary Check**:
   - Verify that all pending verification receipts are sealed before stopping inference.
   - Confirm active GPU VRAM drops below 650 MiB prior to initializing PyTorch CUDA allocators.
   - Restrict CUDA memory ceiling via `torch.cuda.set_per_process_memory_fraction(0.64)`.

2. **NoRA Frobenius Normalization**:
   - Initialize adapter down-projection matrix $A \in \mathbb{R}^{r \times d}$.
   - Enforce Frobenius normalization: $A \leftarrow A / \|A\|_F$, asserting $\|A\|_F = 1.0$.
   - Preserves DeepMind base model distillation weights with zero inference latency overhead.

3. **Rank-64 LoGRA Gradient Projection**:
   - Redraw rank-64 random Gaussian projection matrix $P \in \mathbb{R}^{d \times r}$ per step.
   - Project parameter updates on-the-fly: $\Delta W = P (P^T \nabla_W \mathcal{L})$.
   - Verify that estimated policy drift satisfies $D_{KL}(\pi_\theta \| \pi_{\text{ref}}) \le \epsilon_{KL}$.

4. **Inference Daemon Resumption & Speculative Throughput Verification**:
   - Free PyTorch CUDA tensors and restart inference server on Port 8138.
   - Assert that Multi-Token Prediction generation achieves $\ge 39.7$ tokens/second.
