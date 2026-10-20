# Invariant Rule: Phase 30 Production Hibernate-and-Train LoGRA/NoRA Consolidator & Omniscient ARSI Master Gate

> **Scope**: Layer 4 Invariant Rule (Phase 30)  
> **Authority**: NVIDIA *LoGRA* (arXiv:2610.06647), Frobenius-Normalized *NoRA* (arXiv:2608.31036), ADR-2  
> **Hardware Boundary**: Live NVML Hardware Telemetry, Quiescent VRAM $< 650\text{ MiB}$, Active VRAM $\le 4,812.0\text{ MiB}$

## Operational Invariants

1. **Live NVML Hardware Telemetry**:
   - Hardware resource monitoring must query live NVML interfaces (`pynvml` / `nvidia-smi`) rather than synthetic dictionaries.
   - Total active GPU VRAM must never breach the **4,812 MiB physical ceiling** during live inference or offline consolidation.

2. **Loopback Service Health Invariant**:
   - Primary LLM inference server (Port 8138 `/health`), vision sidecar (Port 8139), and OpenViking daemon (Port 1933) must remain verifiable and healthy.
   - Database WAL continuity on `.hermes/state.db` and constitutional coverage on `.hermes/SOUL.md` must be maintained at all times.

3. **Temporal Mutual Exclusion (TME) Weight Consolidation**:
   - Neural adapter consolidation (PyTorch gradient sketching) is strictly forbidden while online inference daemons are serving traffic.
   - The inference daemon must be quiesced before launching adapter consolidation, ensuring total training VRAM $\le 4,552.2\text{ MiB} \le 4,812\text{ MiB}$.
   - NoRA weight matrices must strictly satisfy the Frobenius normalization invariant $\|A\|_F \equiv 1.0$ and retain $D_{\text{KL}} \le 0.05$.

4. **Deterministic Epistemic Closure**:
   - Multi-tier system verification must validate all operational subsystems, exiting code 0 and sealing `/tmp/hermes_verified_receipt.json`.
