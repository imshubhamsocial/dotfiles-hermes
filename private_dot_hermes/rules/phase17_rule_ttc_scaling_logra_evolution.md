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

1. **Online Hardware-Bounded Test-Time Compute (TTC) Scaling**:
   - Deliberation depth inside `<|channel>thought` and MTP draft sampling (`--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0.75`) dynamically scale according to the initial LoopCD token entropy $H(Y \vert X)$.
   - Active GPU VRAM allocation during inference must remain strictly $\le 4,812$ MiB (single-slot `-np 1`, symmetric `q4_0` KV cache).

2. **Offline Hibernate-and-Train LoGRA/NoRA Evolution**:
   - **Temporal Mutual Exclusion**: Before launching PyTorch optimization, Hermes hibernates `hermes-llama-server` and verifies GPU memory drops below 650 MiB.
   - **Allocator Ceiling**: Sets `torch.cuda.set_per_process_memory_fraction(0.64)`, restricting PyTorch to $\le 3,932$ MiB and guaranteeing total system VRAM remains $\le 4,812$ MiB.
   - **Rank-64 LoGRA Random Gradient Projection**: Projects microbatch gradients on-the-fly via rank-$r$ ($r=64$) step-redrawn Gaussian matrices $P \in \mathbb{R}^{d \times r}$:
     $$\Delta W = P (P^T \nabla_W \mathcal{L})$$
     without materializing dense gradient tensors.
   - **NoRA Frobenius Normalization**: Down-projection matrix $A \in \mathbb{R}^{r \times d}$ is normalized at step 0:
     $$A \leftarrow \frac{A}{\|A\|_F}, \quad \text{guaranteeing } \|A\|_F \equiv 1.0$$
     at 0 inference latency penalty, preventing catastrophic forgetting of base model weights.
   - **KL Drift Guard**: Policy updates are throttled so that $D_{KL}(\pi_\theta \| \pi_{\text{ref}}) \le \epsilon_{KL}$.
   - **Speculative Throughput Invariant**: Post-resume MTP generation throughput must sustain $\ge 39.7$ tok/s.
