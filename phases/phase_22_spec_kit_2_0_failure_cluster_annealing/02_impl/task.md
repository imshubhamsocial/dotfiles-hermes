# Phase 22: Spec-Kit 2.0 Failure Cluster Annealing — Implementation Checklist

> **Phase Directory**: `phase_22_spec_kit_2_0_failure_cluster_annealing`  
> **Status**: Ready for Stage `03_verify` execution  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase22_speckit_annealing_eval/scenario/annealing_engine.py`
- Targeted Symbol(s): `ASTFailureClusterer.extract_ast_tokens`
- Causal Hypothesis: `ASTFailureClusterer.extract_ast_tokens` extracts literal identifier names inside quotes (e.g. `'record'`, `'data'`, `'payload'`), causing Jaccard similarity between identical structural nodes with different identifier names to drop below the 0.75 threshold (producing 5 clusters instead of 2). Stripping quoted literals via `normalized = re.sub(r"['\"][^'\"]*['\"]", "", ast_pattern)` retains pure AST structural tokens (`subscript_expression`, `base`, `index`, `binary_expression`, `operator`, `right`), restoring 1.0 similarity and partitioning failure traces into exactly 2 clusters.
- Secondary Task: Run `benchmark_speckit2.py` to produce `speckit2_metrics.json` confirming 0.0 MiB CUDA VRAM delta, SymPy hardware proof validity, and Kahn topological regeneration with >= 60.0% patch debt reduction.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
