# 11. Draft-Detective & Graft: Adversarial Verification & AST Refactoring

> **Research Source Reference**: `https://github.com/agencyenterprise/draft-detective` & `GRAFT AST Migration`  
> **Topic Category**: Adversarial Verification Gates & AST Code Refactoring  
> **Sequential Index**: `11 / 11`

---

## 1. What the Reference Means

* **Draft-Detective** (by Agency Enterprise / AE Studio): An automated verification framework built to adversarially cross-examine generated claims, technical specifications, and reference links against actual ground-truth files to flag hallucinations and unsupported assertions.
* **Graft (AST Refactoring & Migration)**: Automated structural code transformation and API dependency graph generation using Tree-sitter and compiler error feedback loops.

---

## 2. Core Architectural Mechanisms

1. **Adversarial Claim Verification**: Every statement or architectural assertion made by an agent is checked against real workspace files; unverified claims are flagged as violations.
2. **Compiler-Feedback Synthesis**: Validates code refactorings against real compiler / test runner outputs and feeds exact error diagnostics back to the repair loop.
3. **MCP & Plugin Accessibility**: Exposes audit results as structured Model Context Protocol tools for continuous quality gating.

---

## 3. Key Takeaways for Agent OS Design

* **Pre-Commit Adversarial Gate**: Run a dedicated verification pass that scans generated PR descriptions and documentation for factual alignment with actual code diffs.
* **AST-Aware Transformation**: Perform surgical code migrations using formal AST graphs rather than relying on unstructured text replacement.
