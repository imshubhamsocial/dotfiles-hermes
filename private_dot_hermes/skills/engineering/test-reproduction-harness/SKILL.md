---
name: test-reproduction-harness
description: Autonomous repro harness synthesis with red-green verification.
triggers: ["bug fix", "reproduce issue", "regression test", "failing test", "SWE-bench", "red-green"]
---

# Test Reproduction Harness

Trigger: Use when fixing a bug or implementing an issue fix before touching production source code.

## Workflows
- **Protocol**: See [docs/swe-repro-protocol.md](docs/swe-repro-protocol.md)

## Quick Run
```bash
./scripts/run-repro.sh reproduce_issue.py
```
