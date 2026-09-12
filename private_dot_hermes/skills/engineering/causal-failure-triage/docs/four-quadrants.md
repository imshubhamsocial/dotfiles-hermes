# 4-Quadrant Causal Attribution Matrix

| Quadrant | Failure Signature | Resolution Strategy |
|:---|:---|:---|
| **I — Spec Ambiguity** | Ambiguous prompt, contradictory interfaces | Inspect `.hermes/specs/` and probe AST |
| **II — Grounding Error** | Hallucinated symbol, missing function name | Query symbol index `rg -n "<symbol>"` |
| **III — Environment Defect** | Missing tool/library, container permission | Run substrate-recon, install devel package |
| **IV — Logic Error** | Assertion failure, broken test, regression | Tabu branch swap, dialectic thesis-antithesis |
