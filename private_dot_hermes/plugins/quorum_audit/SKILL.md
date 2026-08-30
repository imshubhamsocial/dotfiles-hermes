---
name: quorum-audit
description: Enforce cross-model consensus and independent audit gates on code changes.
tags: [audit, ast, consensus, verification]
---

# Quorum Consensus Audit Gate

Enforces the invariant: **No single model can both write and approve code.**

## Protocol Lifecycle
`edit -> audit -> agree -> retro -> commit`

1. **Author Phase**: Agent proposes a code diff or file modification.
2. **Audit Phase**: Independent auditor verifies AST syntax health, blast radius, and test regressions.
3. **Agreement**: If fitness score >= 0.85 and no critical violations, consensus is reached.
4. **Rejection**: If rejected, author must refine with structured failure feedback.
