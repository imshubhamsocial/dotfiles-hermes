---
id: "ast-grep-py"
title: "Tree-Sitter Structural AST Search & Syntax Auditing (ast-grep-py)"
category: ["ast", "syntax", "auditing"]
tags: ["ast-grep", "tree-sitter", "parser", "linting", "ruff"]
source: "ast-grep OSS / Tree-Sitter"
era: "Era 1 & Era 5"
status: "active"
verified: true
---

# Tree-Sitter Structural AST Search & Syntax Auditing

## Architecture
Traditional regex-based code search (`grep`, `rg`) operates on raw text, causing false positives on comments, strings, and partial token matches. `ast-grep-py` uses Tree-sitter parsers to build concrete syntax trees (CST/AST):
- **Structural Pattern Matching**: Matches code patterns like `eval($$$)` or `def $FUNC($$$):` across arbitrary formatting and indentation.
- **Syntax Error Detection**: Identifies exact Tree-sitter `ERROR` nodes in Python, JavaScript, TypeScript, and HTML.
- **Multilingual Support**: Provides unified AST traversal across Python, JS, TS, HTML, and CSS.

## Hermes Integration
- **`observer_gate` plugin**: Combines `ast-grep-py` with `ruff` to audit Python/JS/TS files before git commit.
- **`demo_validator` plugin**: Verifies generative UI interactive web artifacts before turn completion.
- **`mcp_tools`**: Exposes `ast_grep_search` as an LLM-callable tool for deep codebase inspection.
