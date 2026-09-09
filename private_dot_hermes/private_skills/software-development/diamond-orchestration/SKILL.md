---
name: diamond-orchestration
description: Orchestrate fan-out, reduce, verify, converge refactors.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [orchestration, refactoring, multi-agent, verification]
    category: software-development
---

# Diamond Orchestration Pattern

The Diamond Orchestration pattern structures complex multi-file refactoring and architectural migrations across four deterministic stages:

```
         [ 1. Fan-Out (Independent Inquiries) ]
                   /          \
    [ Subagent A: Tree 1 ]   [ Subagent B: Tree 2 ]
                   \          /
        [ 2. Deterministic Reduce (Unified AST Diff) ]
                         |
        [ 3. Skeptic Verifier (Maker != Verifier) ]
                         |
        [ 4. Converge & Commit (Atomic Milestone) ]
```

---

## 1. When to Use
Use Diamond Orchestration when:
- A refactor touches 3+ independent subsystems or modules.
- Independent inquiries or code migrations can execute in parallel.
- Work requires strict maker-vs-verifier separation to avoid blind spots.

Do NOT use for single-file or sequential edits (where multi-agent overhead yields zero benefit and wastes tokens).

---

## 2. The Four Stages

### Stage 1: Fan-Out (Parallel Independent Inquiries)
- Dispatch independent subagents (or parallel task nodes) to analyze or mutate isolated branches/files.
- Each subagent operates within its own bounded context and capability mask:
  - `@architect`: Identifies interfaces and data dependencies.
  - `@coder`: Applies surgical code edits and AST transformations.

### Stage 2: Deterministic Reduce
- Aggregate diffs and findings from parallel subagents into a unified patch.
- Resolve any overlapping symbol collisions or interface mismatches deterministically before running verification.

### Stage 3: Skeptic Verifier (Maker != Verifier)
- The agent or reviewer evaluating the deliverable must NOT be the author.
- The verifier executes independent, ground-truth tool checks:
  - Full automated test suite (`pytest`, `npm test`, `cargo test`).
  - AST syntax and lint integrity (`ast-grep`, `ruff`, `biome`).
  - Strict evidence-audit verification (speculative claims forbidden).

### Stage 4: Converge & Atomic Commit
- Upon all verification checks passing green:
  - Synchronize changes to disk and configuration/chezmoi.
  - Commit milestone with evidence citations.
  - Reset working context for the next horizon.
