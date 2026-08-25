---
name: debug-verification-patterns
description: Verify user-reported bugs exist before implementing fixes.
---

## When to Use

User reports: "X is broken" or "I expected Y but got Z"

## Steps

1. **Inspect Current Implementation**
   - Read the actual code, not the user's description
   - Check if the bug may already be fixed

2. **Run Existing Tests**
   - Execute all relevant unit tests
   - If tests pass, the bug may be resolved

3. **Test Reported Scenario Manually**
   - Run the exact scenario the user reported
   - Verify the behavior matches expected outcome
   - Example: User says "alerts fire twice" → Call the function and observe

4. **Report Finding**
   - If bug exists: document root cause, fix, and verification steps
   - If bug does NOT exist: explain current behavior is correct

## Pitfalls

- **Bug may already be fixed**: User reports outdated issues. Always run existing tests first. If all pass, test the reported scenario manually to confirm. Do not re-implement if tests indicate correct behavior.
- **Different codebase**: User may be describing behavior from a different branch. Verify the exact file and commit.
- **Multiple calls cause duplicates**: The bug may be in call sites, not the function itself.

## Related Skills

- `test-driven-development`: Use TDD workflow when implementing fixes
- `systematic-debugging`: 4-phase root cause debugging

## Support Files

- `references/alert-verification.md`: Session-specific alert debugging patterns