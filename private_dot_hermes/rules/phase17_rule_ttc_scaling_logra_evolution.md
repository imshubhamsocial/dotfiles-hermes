---
phase: "Phase 17"
authority: "Hardware-Bounded TTC Scaling & Hibernate LoGRA/NoRA"
testbed: "tests/phase17_logra_nora_eval/"
status: "Operational & Certified"
---

# rule_ttc_scaling_logra_evolution.md — Invariant Operating Rule for TTC Scaling & Hibernate LoGRA/NoRA Evolution

> **Target**: Hermes Agent OS & Test-Time Compute (TTC) Post-Training Runtime  
> **Authority**: Phase 17 Architectural Standard (`Evolution.md` Section 3.6 & 4.1)  
> **Theoretical Grounding**: NVIDIA LoGRA (*arXiv:2610.06647*), NoRA (*arXiv:2608.31036*), GrowMTP (*DeepSeek / Bartowski*)

---

## 1. Context & Architectural Mandate

In local-first execution on hardware-bounded consumer GPUs (NVIDIA RTX 3050, 6GB physical VRAM), running 128K context inference and post-training parameter optimization simultaneously is physically impossible without exceeding the 4,812 MiB VRAM ceiling. Hermes enforces two coupled mechanisms:

1. **Online Hardware-Bounded Test-Time Compute (TTC) Scaling & GrowMTP Tracking**:
   - Deliberation depth inside `<|channel>thought` and MTP draft sampling (`--spec-type draft-mtp,ngram-map-k --spec-draft-n-max 4 --spec-draft-p-min 0.55`) dynamically scale according to the initial LoopCD token entropy $H(Y \vert X)$.
   - Active GPU VRAM allocation during inference must remain strictly $\le 4,812$ MiB (single-slot `-np 1`, asymmetric `q8_0` Keys / `q4_0` Values KV cache, 16K host DDR5 paging `--cache-ram 16384`).
   - **GrowMTP Tracking (arXiv:2609.16648)**: Logs online speculative acceptance $(\text{draft\_n}, \text{draft\_n\_accepted})$. If empirical draft acceptance falls below $\alpha_{\text{draft}} < 0.75$, offline draft head distillation is queued during the 03:15 AM TME window.

2. **Offline Hibernate-and-Train LoGRA/NoRA Evolution**:
   - **Temporal Mutual Exclusion**: Before launching PyTorch optimization, Hermes hibernates `hermes-llama-server` and verifies GPU memory drops below 650 MiB.
   - **Allocator Ceiling**: Sets `torch.cuda.set_per_process_memory_fraction(0.64)`, restricting PyTorch to $\le 3,932$ MiB and guaranteeing total system VRAM remains $\le 4,812$ MiB.
   - **GRADDOT & LoRIF Data Attribution (arXiv:2609.38767, arXiv:2601.21929)**: Trajectories are filtered online via GRADDOT inner products before backpropagation; gradients are stored in LoRIF rank-1 factorized Woodbury formats ($15\times$ I/O reduction, $30\times$ speedup).
   - **Rank-64 LoGRA Random Gradient Projection**: Projects microbatch gradients on-the-fly via rank-$r$ ($r=64$) step-redrawn Gaussian matrices $P \in \mathbb{R}^{d \times r}$:
     $$\Delta W = P (P^T \nabla_W \mathcal{L})$$
     without materializing dense gradient tensors.
   - **NoRA Frobenius Normalization**: Down-projection matrix $A \in \mathbb{R}^{r \times d}$ is normalized at step 0:
     $$A \leftarrow \frac{A}{\|A\|_F}, \quad \text{guaranteeing } \|A\|_F \equiv 1.0$$
     at 0 inference latency penalty, preventing catastrophic forgetting of base model weights.
   - **Predicted-KL Drift Guard**: Policy updates are throttled so that $D_{KL}(\pi_\theta \| \pi_{\text{ref}}) \le 0.0002$.
   - **Speculative Throughput Invariant**: Post-resume MTP generation throughput must sustain $\ge 120.0$ tok/s.
