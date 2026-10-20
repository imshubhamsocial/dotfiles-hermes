---
name: smart-clean-rebuild
description: SMART clean-slate module regeneration from specification DAG.
triggers: ["specification change", "rebuild module", "generation debt", "SMART rebuild", "clean slate"]
---

# SMART Clean-Slate Rebuild

Trigger: Use when a specification document shifts or patching has accumulated technical debt.

## Workflows
- **Mathematical Basis**: See [docs/clean-slate-math.md](docs/clean-slate-math.md)

## Quick Command
```bash
./scripts/verify-spec-dag.sh .hermes/specs
```
