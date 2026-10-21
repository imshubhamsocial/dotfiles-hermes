---
name: codebase-architect
description: TaskDAG & Harness2 repo modernizer
---

# Codebase Architect & Polyglot Modernizer

## When to Use
Use for multi-file refactorings, architectural migrations, and resolving recurring failure clusters across polyglot repositories.

## Quick Reference
* AST Recon: `mcp_openjev(extract_workspace_ast)` & `npx ast-grep outline`
* DAG Planner: `mcp_openjev(jev_taskdag_plan)`
* Worktree Probe: `mcp_openjev(jev_harness2_probe_compose)`
* Cluster Annealer: `mcp_openjev(jev_anneal_cluster)`

## Procedure
1. Run `jev_compile_intent` and `extract_workspace_ast` on Turn 1 to index symbols and caller blast radius on CPU.
2. Build a cycle-free topological plan via `jev_taskdag_plan`.
3. Execute surgical diffs (Karpathy U12 <= 15 lines) or probe competing implementations sequentially via `jev_harness2_probe_compose`.
4. If Strike 2 occurs, execute `git checkout HEAD -- <file>` and invoke `jev_anneal_cluster` to regenerate clean-slate from `specs/annealed_<module>.md`.
5. Verify `pytest -q` exit code 0 and validate `/tmp/hermes_verified_receipt.json`.
