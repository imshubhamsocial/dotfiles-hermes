# Phase 24: Autonomous Offline LoGRA/NoRA Weight Evolution & Temporal Mutual Exclusion

## 1. Context & Operational Invariant
When consolidating distilled reasoning trajectories into open-weight adapter parameters, executing dense PyTorch backpropagation while `llama-server` is actively running on Port 8138 will breach the physical **RTX 3050 Laptop GPU ceiling (4,812 MiB active limit)**.
To maintain continuous recursive self-improvement without human intervention or Out-Of-Memory (OOM) faults, weight evolution executes strictly during system idle/hibernation under **Temporal Mutual Exclusion (TME)**.

---

## 2. Core Architectural Pillars

### Pillar A: Temporal Mutual Exclusion (TME) & VRAM Quorum
* **Quorum Guard**: Weight evolution must never initialize PyTorch CUDA allocators while Port 8138 is loaded in VRAM.
* `acquire_vram_quorum()` must verify that current allocated GPU VRAM is below $\le 650.0\text{ MiB}$ (quiescent desktop level) before proceeding.
* If Port 8138 is active, the orchestrator triggers an offline suspend signal or coordinates with systemd/hibernation.
* PyTorch memory allocator is strictly bounded at initialization:
  ```python
  torch.cuda.set_per_process_memory_fraction(0.64)  # 3,932.16 MiB max reserve
  ```
* Total peak VRAM must satisfy:
  $$V_{\text{peak}} = V_{\text{quiescent}} + V_{\text{torch}} \approx 620.0 + 3,932.2 = 4,552.2\text{ MiB} \le 4,812.0\text{ MiB}$$

### Pillar B: NVIDIA LoGRA Gradient Sketches (arXiv:2610.06647)
* Low-Rank Gradient Random Approximation projects dense token gradients onto a rank-$r$ ($r=64$) subspace using a fixed random Gaussian projection matrix $P \in \mathbb{R}^{d \times r}$ normalized by $1/\sqrt{r}$:
  $$\Delta W = P (P^T \nabla_{W} \mathcal{L})$$
* This eliminates the need to allocate full-rank Adam first-moment ($m_t$) and second-moment ($v_t$) momentum buffers, reducing optimizer memory by over $78\%$.

### Pillar C: NoRA Frobenius Regularization (arXiv:2608.31036)
* Normalized Rank Adaptation initializes down-projection adapter matrix $A \in \mathbb{R}^{r \times d}$ such that:
  $$\|A\|_F = \sqrt{\sum_{i=1}^r \sum_{j=1}^d A_{i,j}^2} \equiv 1.0$$
* Enforces gradient stability across recursive evolution cycles, preventing runaway adapter magnitude and catastrophic forgetting.

### Pillar D: Bounded KL Drift & Speculative MTP Resumption
* **KL Budget Verification**: Policy distribution shift against pre-update base model $P_{\text{ref}}$ must strictly satisfy:
  $$D_{KL}(P_{\text{ref}} \parallel P_{\theta}) \le 0.05$$
* **Post-Consolidation Resumption**: Following adapter consolidation and PyTorch VRAM release (`torch.cuda.empty_cache()`), Port 8138 is resumed.
* Multi-Token Prediction (MTP) speculative decoding draft throughput must achieve:
  $$\text{Throughput}_{\text{MTP}} \ge 42.4\text{ tok/s}$$

---

## 3. Negative Constraints (Zero Exceptions)
1. **Never allocate dense optimizer states on CUDA**: All gradient updates must use rank-64 LoGRA projection.
2. **Never train concurrently with inference**: Temporal Mutual Exclusion is mandatory. Violating VRAM quorum halts execution immediately.
3. **Never allow $\|A\|_F \ne 1.0$ at initialization**: NoRA normalization is mandatory.
4. **Never create synthetic Python shims in `.hermes/`**: All runtime logic resides in isolated testbeds or standard package entry points.
