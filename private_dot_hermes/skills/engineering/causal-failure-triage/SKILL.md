---
name: causal-failure-triage
description: 4-quadrant causal failure attribution and recovery routing.
triggers: ["tool failure", "error triage", "recovery routing", "repeated failure", "tabu swap", "root cause"]
---

# Causal Failure Triage & Recovery

Trigger: Use after any tool call or test execution fails twice in succession.

## Workflows
- **Taxonomy**: See [docs/four-quadrants.md](docs/four-quadrants.md)

## Quick Triage
```bash
./scripts/triage-error.sh "<error-message>"
```
