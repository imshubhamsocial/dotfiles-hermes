---
name: phase20-harness2-dream-meta-loop
description: Continuous RSI nightly dream loop
---

# Google Harness² Continuous RSI Dream Meta-Loop

## 1. When to Use
Use this skill when executing the scheduled nightly dream cycle, auditing historical session failures in `state.db`, or distilling new operational invariants from recurring terminal/compiler errors.

## 2. Dream Cycle Workflow

### Step 1: Session Failure Reconnaissance
Query `.hermes/state.db` using read-only SQL queries to extract recent failed sessions, error traces, and Two-Strike Tabu interventions:
```sql
SELECT session_id, role, content 
FROM messages 
WHERE content LIKE '%FAILED%' OR content LIKE '%Error%' OR content LIKE '%Tabu%'
ORDER BY id DESC LIMIT 50;
```

### Step 2: Hypothesis & Invariant Synthesis
Identify recurring failure patterns (e.g., misconfigured compiler flags, deprecated library imports, tool call formatting errors). Formulate a candidate behavioral invariant:
- Format: `rule_<domain>_<behavior>.md`
- Core sections: Context, Invariants, Examples.

### Step 3: Regression Guard in Isolated Sandbox
Evaluate the candidate rule against existing testbeds under `tests/` in an isolated temporary directory:
1. Copy testbed scenario to a temporary directory.
2. Verify that existing assertions pass with the candidate rule injected.
3. Assert exit code 0.

### Step 4: Promotion & Distillation
If all regression checks pass with zero defects:
1. Promote the rule into `.hermes/rules/` via `/loop learn`.
2. Commit session reflection into OpenViking semantic memory via `memory` tool.
3. Sync changes to Chezmoi dotfiles.
