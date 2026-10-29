# Hardware & NVML VRAM Invariants

> Layer 3 Reference Contract: Physical Hardware Boundaries & Verification Gates.
> Rule: File must remain strictly under 200 lines.

---

## Envelope Limits

* **Physical GPU**: Discrete NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB physical GDDR6).
* **Hard VRAM Ceiling**: Total GPU VRAM usage must strictly respect:
  $$\text{VRAM}_{\text{live}} \le 5,400.0\text{ MiB}$$
* **API Cost Invariant**: $0.00 ongoing API cost. All primary reasoning and representation models execute offline.
* **CPU Core Partitioning**: AMD Ryzen 5 7430U (6 physical cores / 12 logical threads):
  - Cores 0–5 (`taskset -c 0-5`): Reserved for `llama-server` GPU engine.
  - Cores 6–11 (`CPUAffinity=6-11`): Reserved for `hermes-embedding-cpu.service` (`CUDA_VISIBLE_DEVICES=""`).

---

## Live NVML Verification

Any execution stage mutating or testing models must verify live VRAM using:
```bash
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
```
The reported value must remain strictly $\le 5400$. If VRAM exceeds 5,400.0 MiB, halt execution immediately.
