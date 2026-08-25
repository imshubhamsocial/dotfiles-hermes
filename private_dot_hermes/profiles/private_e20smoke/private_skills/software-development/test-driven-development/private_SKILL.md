---
name: test-driven-development
description: >-
  Use TDD workflow: Read AC, write tests first, implement minimal code to pass them, verify.
---

## Steps

1. **Read Requirements**
   - Acceptance criteria from user or task specification
   - Module dependencies and function signatures

2. **Write Tests (Red)**
   - Derive unit test expectations from acceptance criteria
   - Create test file with test cases
   - Run tests — should fail initially

3. **Implement (Green)**
   - Write minimal code to make tests pass
   - Use `patch` or `write_file` for targeted edits
   - Avoid rewriting entire files

4. **Verify**
   - Run tests to confirm they pass
   - Check acceptance criteria are met
   - Verify cross-module contracts (qualified function calls)

## Examples

- AC: "Function returns {'data': 'result'}" → Test: `assert result == {'data': 'result'}`
- AC: "Must call `api.process()` then `log.record()`" → Test checks qualified names
- AC: "Type hints required" → Test validates hints with `inspect.signature`