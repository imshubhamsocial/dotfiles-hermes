---
id: "branch-swapper"
title: "Two-Strike Tabu MCTS Hypothesis Tree & Branch Swapper"
category: ["search", "mcts", "tabu", "branching"]
tags: ["swe-search", "tabu-search", "hypothesis-tree", "backtracking"]
source: "Astra / SWE-Search / Inherent Labs (2026)"
era: "Era 2 & Era 4"
status: "active"
verified: true
---

# Two-Strike Tabu MCTS Hypothesis Tree & Branch Swapper

## Architecture
Small language models (4B-27B) frequently suffer from fixation traps—repeatedly modifying the same lines of code with cosmetic variations when a build or test fails. The Branch Swapper implements an autonomous Monte Carlo Tree Search (MCTS) with Tabu restrictions:
- **Two-Strike Failure Rule**: If 2 consecutive repair attempts fail on the same file or hypothesis node, the active branch is marked `FAILED`.
- **Automatic Backtracking**: Execution state rewinds to the parent hypothesis node.
- **Negative Boundary Constraint Extraction**: The failure signature (e.g. `SyntaxError`, `IndexError`, `MissingImport`) is converted into an explicit negative constraint injected into the prompt of the alternate branch.
- **SQLite WAL Persistence**: State history is persisted in RAMDisk SQLite WAL (`/dev/shm/branch_swapper.db` and `/dev/shm/hypothesis_tree.json`).

## Hermes Commands
- `hermes hypothesis status` — inspects active branch and accumulated negative constraints.
- `hermes hypothesis branch <title> <hypothesis>` — adds exploratory candidate path.
- `hermes hypothesis backtrack <reason>` — manually or autonomously prunes a failing approach.
