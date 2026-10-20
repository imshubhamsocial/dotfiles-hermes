# EXPERIENCE.md — Cross-Task Evolutionary Lessons & Counterfactual Dream Memory

## 1. System Invariants & Distilled Heuristics
- **AST Navigation Priority**: Always extract compact line-range signature outlines via `npx ast-grep outline` or Python `ast` before slicing source files. Zero full-file KV cache bloat.
- **Two-Strike Tabu Rollback**: When a tool action fails twice consecutively, halt immediately, pivot search branch, and revert unverified edits.
- **Declarative Attention Scoping**: Enforce `<focus id="...">` mode during method surgery and compact raw outputs to `<local>` upon verification (`exit 0`).
- **Cryptographic Epistemic Closure**: Every goal resolution must verify exit status 0 and generate `/tmp/hermes_verified_receipt.json` before halting.

## 2. Replay Simulation & Branch Pruning Log
- **Trace World Tree Construction**: Cached in `.hermes/cache/dream_worlds/`.
- **Counterfactual Call Reduction**: Simulated branch rollbacks yield $\ge 1.40\times$ call reduction relative to unpruned search.
- **MASS 3-Pass Validation**: Skills evolved via Pass B must pass Pass C leakage auditing (zero test suite literal leaks).
