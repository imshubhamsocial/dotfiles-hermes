---
version: 1.1.0
category: project
extends: global
---

# Project-Specific Rules (Hermes Agent OS)

These rules supplement global constraints with project-specific conventions.

## Architecture Conventions
- Use modular prompt slotting (Slot 1-4) for system prompts
- Implement progressive disclosure for skills (L0/L1/L2)
- Vector memory must use SQLite WAL + FastEmbed CPU ONNX
- Plugins must follow official NousResearch Hermes Agent Plugin specification (`plugin.yaml`)
- All new modules must have contract and unit tests in `~/.hermes/tests/`

## Stack Requirements
- Python 3.13+ with strict type annotations
- FastEmbed for embeddings (CPU ONNX)
- SQLite WAL for persistence
- Pytest 9+ for testing
- Playwright for browser automation

## Testing Commands
```bash
# Unit & contract tests
make test
# or
distrobox enter ws-hermes -- python3.13 -m pytest ~/.hermes/tests/ -q

# System doctor & plugin verification
make doctor
```

## Code Style
- from __future__ import annotations
- Dataclasses with type hints
- No bare exceptions
- Exit codes: 0 on success, non-zero on failure

## File Organization
- Agent Home: `~/.hermes/`
- Plugins: `~/.hermes/plugins/`
- Tests: `~/.hermes/tests/`
- Documentation: `~/.hermes/docs/`
- Skills: `~/.hermes/skills/`
- Rules: `~/.hermes/rules/`
- Policy: `~/.hermes/policy/`

## Evidence-Grounded Progress Audit
Before reporting task progress or milestone completion, audit each claim against a concrete tool output from the current session. Speculative claims are strictly forbidden. Only report work you can point to evidence for. If something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, cite the exact error; if a step was skipped, state that clearly.
