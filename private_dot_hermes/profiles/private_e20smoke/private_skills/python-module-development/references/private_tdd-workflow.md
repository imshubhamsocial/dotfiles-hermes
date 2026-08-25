# TDD Workflow for Python Module Development

## Files Created in This Session

### `tests/test_api.py`
Test file demonstrating the TDD pattern:
- 6 unit tests covering all acceptance criteria
- Uses `unittest` framework with `patch` for mocking
- Tests: AC1 (admin user), AC2 (regular user), AC3 (non-existent user), AC4 (monkeypatch), AC5 (type hints/docstring), AC6 (returns dict)

### `app/api.py`
Example implementation showing:
- Type hints (`Optional[Dict[str, Any]]`)
- Docstring with Args, Returns, and Example
- Cross-module imports from `.` (package-relative)
- Proper return value when user doesn't exist

### `app/__init__.py`
Updated exports to include `api` module for proper imports.

## Key Points

1. **PLAN.md first**: Always document what, why, and acceptance criteria before coding
2. **Red tests before green code**: Tests fail before implementation to ensure they test the right behavior
3. **Targeted edits**: Use `patch` for find-and-replace, never rewrite whole files
4. **Import management**: Update `__init__.py` exports when new modules need to import from other modules in same package
