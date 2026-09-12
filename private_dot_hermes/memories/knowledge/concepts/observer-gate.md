---
id: "observer-gate"
title: "Observer Gate: Pre-Commit AST Structural Verification & Ruff Auditing"
category: ["verification", "ast", "ruff", "finish-first"]
tags: ["observer-gate", "ruff", "ast-grep", "pre-verify", "audit"]
source: "NousResearch / AST Verification Architecture"
era: "Era 1, Era 4 & Era 5"
status: "active"
verified: true
---

# Observer Gate: Pre-Commit AST Structural Verification

## Invariant: Finish-First & Maker/Verifier Separation
Under the Finish-First invariant (Mythos-Harness / Kornas 2026), no agent task may conclude until all touched code artifacts have passed deterministic syntax and lint verification. The model cannot self-certify its own code without independent gate approval.

## Technology Stack
- **`ruff`**: Lightning-fast Rust linter checking syntax errors (`E999`), undefined variables (`F821`), and missing file encodings (`PLW1514`).
- **`ast-grep-py`**: Tree-sitter CST parsing to detect unhandled delimiters, unclosed tags, and syntax error nodes.
- **Pass-through Rules**: Text, documentation (`.md`), and configuration (`.yaml`) files pass through without compiler rejection.

## Hermes Native Commands
- `hermes audit <file> [--json]` — performs audit on code artifact.
- `/audit <file>` — in-session slash command.
- `pre_verify` hook — autonomously audits all modified files before turn completion.
