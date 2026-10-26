---
name: speckit-annealing
description: Spec-Kit clean-slate on Strike 2
---
# Spec-Kit 2.0 Failure Cluster Annealing
1. When Strike 2 triggers, halt incremental patching and execute git checkout HEAD -- <file>.
2. Call jev_anneal_cluster to generate a formal specification in 01_spec/specs/.
3. Regenerate module topologically from scratch to eliminate patch debt.
