---
name: observer-gate
description: "Pre-commit syntax validation and sub-5ms formatting gate."
---

# Observer Gate Pre-Commit Tool

Run the Observer Gate before committing or claiming verification to ensure zero syntax errors, balanced braces, and clean AST structure.

## Quick CLI Invocations

1. **Run Full Observer Gate on File**:
```bash
python3 ~/.hermes/bin/observer_gate.py <filepath>
```

2. **Run Ultra-Fast Rust Biome Formatting (<5ms)**:
```bash
biome format --write <filepath>
```

3. **Check Node.js Syntax & AST Validity**:
```bash
node -c <filepath>
```
