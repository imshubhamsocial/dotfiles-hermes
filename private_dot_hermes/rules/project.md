---
version: 1.0.0
category: project
extends: global
---

# Project-Specific Rules (Hermes Agent OS)

These rules supplement global constraints with project-specific conventions.

## Architecture Conventions
- Use modular prompt slotting (Slot 1-4) for system prompts
- Implement progressive disclosure for skills (L0/L1/L2)
- Vector memory must use SQLite WAL + FastEmbed CPU ONNX
- All new modules must have contract tests in tests/harness_contracts/

## Stack Requirements
- Python 3.13+ with strict type annotations
- FastEmbed for embeddings (CPU ONNX)
- SQLite WAL for persistence
- Pytest 9+ for testing
- Playwright for browser automation

## Testing Commands
```bash
# Unit tests
distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q

# Specific test
distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u48_agent_os_specs.py -v
```

## Code Style
- from __future__ import annotations
- Dataclasses with type hints
- No bare exceptions
- Exit codes: 0 on success, non-zero on failure

## File Organization
- Core library: src/hermes_core/
- Tests: tests/harness_contracts/
- Config: .hermes/
- Assets: assets/
