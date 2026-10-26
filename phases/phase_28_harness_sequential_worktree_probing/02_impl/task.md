# Phase 28: Harness² Sequential Worktree Probing — Implementation Checklist

> **Phase Directory**: `phase_28_harness_sequential_worktree_probing`  
> **Status**: Ready for Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase28_harness2_worktree_eval/scenario/cluster_annealer.py`
- Target Symbol: `ClusterAnnealer.schedule_tasks`
- Module Stems: `cluster_annealer`
- Required Skills: `karpathy-surgical-diff`, `viking-retrieval`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - **Hypothesis**: In `ClusterAnnealer.schedule_tasks`, iterating over `edges` directly indexes `adj[u]` and increments `in_degree[v]` without checking if `u` or `v` are in the registered `tasks` set. If an edge references an external or unregistered task, a `KeyError` is raised. Guarding edge insertion with `if u in tasks and v in tasks:` prevents unregistered dependency nodes from crashing topological scheduling.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Target is in Domain C git repository).
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
