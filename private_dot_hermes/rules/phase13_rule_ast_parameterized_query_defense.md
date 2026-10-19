---
phase: "Phase 13"
authority: "AST Parameterized Query Defense & Injection Prevention"
testbed: "tests/phase13_stair_memory_eval/"
status: "Operational & Certified"
---

# AST Security Rule: Parameterized Query Defense

## Overview
This rule targets the use of f-strings or string concatenation to construct SQL queries, which is a primary cause of SQL injection (CWE-89).

## Detection Pattern
The rule uses AST analysis to detect when a string literal, potentially containing variable names, is formatted (e.g., via f-strings) and then passed directly as the query argument to `cursor.execute()`.

## Vulnerable Pattern (CWE-89)
```python
# Vulnerable: Uses string formatting to inject user-controlled input into SQL
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query) # Input 'username' is not sanitized
```

## Defense Mechanism
All database interactions must utilize parameterized queries. This means using placeholders (like `?` or `%s`) in the query string and passing the user-controlled variables as a separate tuple or list in the second argument of `execute()`.

## Correct Pattern
```python
# Safe: Parameterized query using placeholders
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,)) # Input is treated as data, not executable code
```

## Structural Requirements
1. **Detect**: Look for string formatting operations applied to SQL strings before execution.
2. **Remediate**: Rewrite the pattern to use database driver-specific placeholders and separate argument passing.
3. **Verify**: Run `ast-grep scan -r rules/sqli_fstring.yml` and verify the fix.
4. **Test**: Ensure existing unit tests cover the parameterized approach and that new tests fail when f-string injection is attempted.