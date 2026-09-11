---
name: agi-loop-director
description: Direct and execute autonomous long-horizon goal loops (/loop) with multi-milestone decomposition, empirical test verification, stall detection, and self-evolution.
tags: [agi, loop, autonomous, long-horizon, verification, meta-harness]
---

# AGI Loop Director

Use this skill when executing complex, long-horizon autonomous tasks that require multi-turn reasoning loops (`/loop`), autonomous tool selection, state persistence, and self-correcting execution.

## Core Directives

1. **Strategic State Anchoring (Magentic-One Pattern)**:
   - Always initialize and maintain a **Task Ledger** (goals, verified facts, completed milestones) and a **Progress Ledger** (active step, observation, stall counter).
   - If 2 consecutive turns achieve no measurable progress, immediately trigger the **2-Turn Stall Circuit Breaker**: pause tool calls, reflect on error traces, and mutate the strategic plan.

2. **The 4-Stage Autonomous Cycle**:
   - **Locate**: Use AST search or grep to identify the exact files and symbols without unconstrained exploratory loops.
   - **Retrieve**: Pull minimal context slices into memory (keep injected rules <400 tokens).
   - **Edit**: Apply surgical SEARCH/REPLACE diffs or smolagents Code-as-Action scripts.
   - **Verify**: Execute the test suite inside an isolated sandbox. If tests fail, automatically revert (`git reset --hard`) and prune the failed hypothesis.

3. **Continuous Trajectory Logging**:
   - Every intermediate step, observation, and reward score must be recorded in SQLite WAL (`trajectories.db`) with SWE-agent observation windowing (50 lines max).
