# Invariant Rule: Phase 28 Native Google Harness² Worktree Engine & ADK Bridge

> **Scope**: Layer 4 Invariant Rule (Phase 28)  
> **Authority**: Google Harness² (arXiv:2610.14224) & Google ADK 2.9.0 A2A Protocol  
> **Hardware Boundary**: Port 8138 `-np 1`, SymPy CPU RAM, $\Delta \text{VRAM} \equiv 0.0\text{ MiB}$

## Operational Invariants

1. **Sequential Worktree Probe Isolation**:
   - Competing hypotheses must be probed sequentially using isolated git worktrees rather than concurrent subagent containers.
   - All worktree explorations reuse Port 8138 slot 0 with 0.0 MiB VRAM overhead.
   - The Harness² selection functional strictly weights verification non-substitution ($\mathbf{1}_{V_{\text{act}} \equiv V_{\text{con}}}$), zero exit codes ($\mathbf{1}_{\text{exit}=0}$), Karpathy U12 surgical bound, and minimal latency.

2. **Kahn Topological TaskDAG Scheduling**:
   - Multi-agent task handoff across `@architect`, `@coder`, `@tester`, and `@critic` MUST execute along a verified topological DAG order.
   - Cyclic dependencies must be intercepted before execution ($C_{\text{cycles}} \equiv 0$).

3. **Clean-Slate Failure Cluster Annealing**:
   - Failure clusters must be annealed into formal SMART specifications with CPU SymPy mathematical VRAM proofs ($V_{\text{total}} \le 4,812.0\text{ MiB}$).
   - Annealing must eliminate recurring failure patterns, driving residual debt to zero ($D_{t+1} \equiv 0.0$).
