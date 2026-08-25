---
name: python-module-development
description: "Python modules: TDD via PLAN.md, red tests, impl, verify."
---

# Python Module Development

## When to Use
Creating new Python modules when: module has interface requirements, acceptance criteria exist, and cross-module dependencies exist.

## Workflow

### Step 1: Create Implementation Plan (PLAN.md)
Write a brief plan: what to change, why, acceptance criteria, verification strategy.

### Step 2: Write Red Tests First
Create unit tests BEFORE implementing. Test all acceptance criteria. Use `patch` for targeted edits. Update `__init__.py` exports if needed.

**Key Points:**
1. **PLAN.md first**: Always document what, why, and acceptance criteria before coding
2. **Red tests before green code**: Tests fail before implementation to ensure they test the right behavior
3. **Targeted edits**: Use `patch` for find-and-replace, never rewrite whole files
4. **Import management**: Update `__init__.py` exports when new modules need to import from other modules in same package. **Critical**: Use qualified names (`api.handle_request`, `response.render_response`, `log.format_log`) for cross-module calls within a package. Bare `import api` can fail with "No module named 'api'" even when the module exists—the qualified pattern bypasses namespace resolution issues and is the reliable cross-module contract.
5. **Verification**: Run tests to confirm all acceptance criteria pass before considering implementation complete

### Step 3: Implement with Targeted Edits
Use `patch` or `write_file` for targeted changes. Never rewrite whole files.

### Step 4: Verify Tests Pass
Run tests to confirm all acceptance criteria pass.

## Pitfalls

- Import failures: Check `__init__.py` exports the module.
- Return type mismatches: Use `Optional[Dict[str, Any]]` when function can return `None`.
- **SQLite fetchall() returns list of dicts, NOT single dict**: `db.get_user(conn, uid)` with `fetchall()` returns `[dict]` - a list containing one dict. Code expecting direct dict access will fail. **Fix**: Extract first element: `user_list = db.get_user(conn, uid); if user_list: user = user_list[0]`.
- **Interface key mismatch**: Mocked test data may use keys different from implementation. Ensure mock data structure matches actual return type.
- **Missing __init__.py**: When importing from a package (`from . import db`), the `__init__.py` must exist and export the submodule.
- **Stable sort / input-order preservation for ties**: Python's default sort is stable - items with equal sort keys maintain their original input order. **Pitfall**: When sorting by a numeric field (e.g., stock level), items with the same value appear in the order they appeared in the input, not alphabetically. **Example**: `check([('zebra',3), ('apple',3), ('banana',3)], 4)` returns `['zebra', 'apple', 'banana']` (input order for same stock), not `['apple', 'banana', 'zebra']` (alphabetical). Test expectations must reflect this behavior.
- **Inverted logic bugs**: Common bug is using `!=` instead of `==` for boolean comparisons (e.g., `is_admin` returning True for non-admin users). Always verify logic by reading the implementation and comparing with test output, not just trusting the test file.
- **Missing import causing NameError**: Common bug: a function uses another module's function (e.g., `money(v)`) but fails to import it, causing `NameError: name 'X' is not defined` even when the module exists. **Fix**: Add the missing import statement at the top of the file. Always verify cross-module imports exist before running tests - use `python3 -c "import module"` to diagnose.
- **Stable sort / input-order preservation for ties**: Python's default sort is stable - items with equal sort keys maintain their original input order. **Pitfall**: When sorting by a numeric field (e.g., stock level), items with the same value appear in the order they appeared in the input, not alphabetically. **Example**: `check([('zebra',3), ('apple',3), ('banana',3)], 4)` returns `['zebra', 'apple', 'banana']` (input order for same stock), not `['apple', 'banana', 'zebra']` (alphabetical). Test expectations must reflect this behavior.
- **Rounding before aggregation**: When computing aggregates (sums, averages) involving decimals, round individual values BEFORE aggregation, not after. Python's banker's rounding can cause drift when rounding final totals vs. pre-rounded values. **Example**: `round(12.345 + 5.9, 2) = 18.34` vs `round(12.345, 2) + round(5.9, 2) = 18.34` (same, but with multiple values the difference grows). Tests expecting per-value rounding will fail if you round only the final result.
- **Duplicate value aggregation**: Common bug in `collapse()` or grouping functions: treating duplicates as "keep first" instead of "sum them up". When deduplicating by key and values are numeric (cents, amounts), you must **sum the values** for each key, not keep the first occurrence. **Example**: `collapse([('a',1),('a',1),('b',2)])` should return `[('a',2),('b',2)]` - aggregating 1+1=2 for key 'a'. Using `dict` with `if key not in seen` keeps only first; use `defaultdict(float)` and `seen[key] += value` to aggregate.
- **Import verification before running tests**: If pytest reports `ModuleNotFoundError`, fix the import structure first before running tests. Use `python3 -c "import module"` to quickly diagnose import issues.

## Reference Files

- `tests/test_api.py` - TDD test file
- `app/api.py` - Example implementation
