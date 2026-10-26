# AGENTS.md — Phase 28 Native Google Harness² Worktree Engine & ADK TaskDAG Evaluation

> **Project**: Hermes Agent OS — Phase 28 Evaluation Harness  
> **Literature**: Google Cloud AI & Northwestern University *Harness²* (arXiv:2610.14224), Google ADK 2.9+  
> **Target Scenario**: `scenario/cluster_annealer.py` (Kahn topological scheduling, unregistered dependency edge handling)  
> **Verification Gate**: `pytest scenario/ -q`

---

## 1. Scope & Verification Contract
- **Target Module**: `scenario/cluster_annealer.py`
- **Test Module**: `scenario/test_cluster_annealer.py`
- **Verification Command**: `pytest scenario/ -q`
