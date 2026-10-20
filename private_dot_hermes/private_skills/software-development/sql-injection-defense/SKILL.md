---
name: sql-injection-defense
description: Defend against SQL injection with parameters.
version: 1.0.0
author: Hermes Agent (Nous Research)
license: MIT
tags: [security, sql-injection, parameterized-queries, sql-injection-defense]
---

# SQL Injection Defense Skill

## Overview
This skill provides workflows and patterns for securely interacting with databases in Python, specifically preventing SQL injection (CWE-89) by strictly enforcing the use of parameterized queries.

## 🛠️ Procedure: Secure Database Interaction

1.  **Identify Risk**: Locate all database calls using string formatting (e.g., f-strings or `%` formatting) to include user-supplied input within the SQL query string.
2.  **Parameterize**: Modify the query to use a placeholder (e.g., `?` for SQLite, `%s` for MySQL, or `:name` for Psycopg2).
3.  **Execute**: Pass the user-controlled variables as a separate tuple or dictionary in the second argument of `cursor.execute()`.
4.  **Validate**: Run `ast-grep scan -r rules/sqli_fstring.yml` to verify all high-risk patterns are absent.
5.  **Test**: Ensure unit and integration tests explicitly include inputs that would trigger SQL injection if the defense were missing.

## 📚 References

### `references/sqli_patterns.md`
*   **Vulnerable Pattern**: Using f-strings or string concatenation to build queries: `query = f"SELECT * FROM users WHERE username = '{username}'"`
*   **Correct Pattern**: Using placeholders and argument separation: `query = "SELECT * FROM users WHERE username = ?" ; cursor.execute(query, (username,))`

### `references/sqli_mitigation_steps.md`
1. Replace all string interpolation with query placeholders.
2. Audit all database access points in the codebase.
3. Maintain an active CI check using AST-based security rules (`rules/sqli_fstring.yml`).
