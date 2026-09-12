---
name: multi-perspective-audit
description: Adversarial 4-axis code review across safety, VRAM, and YAGNI.
triggers: ["code review", "pre-merge audit", "security scan", "YAGNI check", "diff audit", "PR review"]
---

# Multi-Perspective Adversarial Audit

Trigger: Use before completing a PR, declaring a task done, or committing significant changes.

## Workflows
- **Rubric**: See [docs/four-axis-rubric.md](docs/four-axis-rubric.md)

## Quick Audit
```bash
./scripts/audit-diff.sh
```
