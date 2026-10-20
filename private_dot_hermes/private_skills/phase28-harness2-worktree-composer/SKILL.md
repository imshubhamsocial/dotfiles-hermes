---
name: phase28-harness2-worktree-composer
description: Harness2 worktree Propose-Probe-Compose
---

# Harness² Worktree Propose-Probe-Compose (Phase 28)

## Overview
Phase 28 implements Google Harness² (*arXiv:2610.14224*) and Google ADK 2.9+ TaskDAG federation natively. To prevent out-of-memory crashes on the 4,812 MiB VRAM ceiling, parallel multi-agent containers are strictly avoided in favor of **Sequential Native Worktree Probing**:

## Operational Protocol
1. **ADK Kahn Topological Scheduling**:
   - Multi-agent handoff executes sequentially across 4 sandboxed personas: `@architect` $\to$ `@coder` $\to$ `@tester` $\to$ `@critic`.
   - Directed acyclic graph scheduling eliminates circular execution deadlocks via Kahn in-degree tracking (`mcp_openjev(jev_taskdag_plan)`).
2. **Sequential Worktree Probes**:
   - Competing hypotheses are probed in temporary git worktrees (`/tmp/hermes_probe_inv_<id>` vs `/tmp/hermes_probe_dom_<id>`) on single-slot Port 8138.
   - The winning patch is selected via the Harness² objective functional:
     $$f_{\text{select}}(\tau) = \mathbf{1}_{V_{\text{act}} \equiv V_{\text{con}}} \cdot \mathbf{1}_{\text{exit}=0} \cdot \frac{1}{1 + \max(0, L_{\text{diff}} - 10)} \cdot \frac{1}{\log T_{\text{total}}}$$
3. **Spec-Kit 2.0 Failure Cluster Annealing**:
   - Failure clusters are annealed into `specs/annealed_<cluster_id>.md` using symbolic SymPy proofs ($V_{\text{total}} \le 4,812.0\text{ MiB}$), eliminating incremental patch debt ($D_{t+1} \equiv 0.0$).
