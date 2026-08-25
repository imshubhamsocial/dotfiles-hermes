---
name: demo_validator
description: "AST syntax validation gate for Python/JS/HTML artifacts"
tier: 2
---
# Demo Validator Skill

Provides pre-commit AST validation for Python, JavaScript, and HTML files.

## Usage
When activated, validates file syntax before disk write:
- Python: `ast.parse()` check
- JS/HTML: brace balance + dangerous pattern scan
- Returns exact line-number error slices on failure

## Commands
- `validate <filepath>` — run syntax probe on target file
- `validate-all` — scan all changed files in current session
