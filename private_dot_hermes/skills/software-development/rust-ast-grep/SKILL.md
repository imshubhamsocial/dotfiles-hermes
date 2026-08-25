---
name: rust-ast-grep
description: Structural AST code search, linting, and refactoring using Rust ast-grep (sg) for precision code edits without regex bugs.
---

# Rust AST-Grep Structural Code Tool

Use `ast-grep` (`sg`) when you need to find functions, variable declarations, or syntax blocks based on **AST structure** rather than fragile line-by-line regex.

## Quick CLI Invocations

1. **Find Pattern Across Project**:
```bash
ast-grep -p "function $NAME($$$ARGS) { $$$BODY }" --lang js
```

2. **Find Specific Class or Interface**:
```bash
ast-grep -p "class $NAME extends $BASE { $$$MEMBERS }" --lang js
```

3. **Structural Search & Replace**:
```bash
ast-grep -p "const $VAR = require('$MOD')" -r "import $VAR from '$MOD'" --lang js --update-all
```

## Best Practices
- `ast-grep` runs in pure Rust (50x faster than ESLint) and guarantees exact syntax matching.
- Use `$$$VAR` for matching arbitrary sequences of statements or arguments.
