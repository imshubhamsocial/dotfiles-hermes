# SQL Injection Defense Rule: Parameterized Queries

## Overview
This rule enforces the use of parameterized queries to prevent SQL Injection (CWE-89) vulnerabilities in Python database interactions. SQL queries must use placeholders (e.g., `?` for SQLite) and pass user-supplied variables as a separate tuple/list to the execution method (e.g., `cursor.execute(query, (params,))`).

## Detection (AST-grep)
This rule targets raw f-string interpolation within SQL query strings.

### Pattern (AST-grep)
The following pattern detects an f-string used to build a SQL query:

```yaml
id: sql-injection-fstring-use
language: python
severity: error
rules:
  - pattern: |
      cursor.execute(f"SELECT * FROM users WHERE username = '{username}'", )
```

## Fix
The fix requires replacing the string interpolation with a parameterized query structure.

### Correct Usage
```python
# Use placeholders (?) and pass variables in the second argument
query = "SELECT id, username, role FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

## Enforcement
All database interactions identified by this rule must be audited and rewritten to utilize parameterized statements. Do not use string concatenation or f-strings for dynamic query parts.
