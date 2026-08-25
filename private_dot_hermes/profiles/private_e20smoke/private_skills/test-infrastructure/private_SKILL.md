---
name: test-infrastructure
description: Handle test environment setup for pytest-based tests
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [test-infrastructure, pytest, venv, setup]
    related_skills: [test-driven-development, hermes-agent-skill-authoring]
---

# Test Infrastructure Skill

This skill handles test environment setup for running pytest-based tests. It addresses the common problem where pytest is not pre-installed in sandbox environments.

## When to Use

- Pytest is not found when attempting to run python -m pytest in a project directory
- TDD workflow verification fails because tests cannot be executed
- Project dependencies require test frameworks not in the base Python environment

## Prerequisites

- Python 3.8+ available in the environment
- Access to create virtual environments (venv module built-in)

## How to Run

1. Identify the project root where tests need to be run
2. Create virtual environment: python -m venv .venv
3. Install pytest: .venv/bin/python -m pip install pytest
4. Verify installation: .venv/bin/python -c import pytest; print(pytest.__version__)
5. Run tests: .venv/bin/python -m pytest tests/test_db.py -v

## Pitfalls

- Do not capture session-specific failures (e.g., missing binaries, credential errors). These are transient and not durable rules
- Virtual environments must match the projects Python version
- Pip may have version conflicts. Use the venvs pip directly (venv/bin/pip) rather than pip3 in the base environment
- Some project directories may already have a .venv. Check if pytest is installed before reinstalling

## Support Files

- scripts/install_pytest.py - Automated venv creation and pytest installation

## Verification

.venv/bin/python -c import pytest; print(pytest.__version__)

Should return pytest version information without errors