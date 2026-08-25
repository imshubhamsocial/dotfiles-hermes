# Reproduction Recipe: Pytest Installation for TDD Workflow

## Problem
Pytest is not pre-installed in the sandbox environment. The TDD workflow requires pytest to run test files (python -m pytest test_db.py), but running it directly fails with ModuleNotFoundError: No module named pytest.

## Root Cause
The sandbox interpreter does not include pytest in the base Python environment. This is a common setup state for test-driven development workflows.

## Fix
Create a virtual environment and install pytest before running TDD verification:

```bash
# Create virtual environment
python -m venv .venv

# Activate and install pytest
.venv/bin/python -m pip install pytest

# Run tests
.venv/bin/python -m pytest tests/test_db.py -v
```

## Why This Works
- Virtual environments isolate dependencies from the base interpreter
- Pip can install pytest without conflicts with other packages
- The .venv/bin/python path should be used consistently in execute_code tool calls

## When to Use
Whenever you need to run pytest-based tests and the sandbox lacks pytest pre-installed. Check for the absence of pytest by attempting to import it first; if ModuleNotFoundError occurs, install it using the recipe above.

## Verification
.venv/bin/python -c import pytest; print(pytest.__version__)

Should return pytest version information without errors