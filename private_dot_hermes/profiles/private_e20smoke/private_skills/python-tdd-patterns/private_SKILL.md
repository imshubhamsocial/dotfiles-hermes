---
name: python-tdd-patterns
description: Mock Python modules via import paths and verify type hints.
---

## When to use
- Writing unit tests for Python functions that depend on other modules
- Verifying type hints are correctly specified
- Testing database interaction layers
- Debugging cross-module dependencies

## Cross-module mocking

To mock functions that are imported by a module, patch at the import location:

```python
from unittest.mock import patch
import app.api as api

with patch('app.api.get_user') as mock_get_user:
    mock_get_user.return_value = {'name': 'alice', 'role': 'admin'}
    result = api.handle_request(conn, 1)
```

❌ WRONG: Patching source modules directly (`app.db.get_user`) won't work.

## Type hints verification

```python
import typing
hints = typing.get_type_hints(handle_request)
# Only explicitly typed params: {'uid': int, 'return': dict}
```

## Database row handling

SQLite `fetchone()` returns a tuple, not a dict. Convert manually:

```python
result = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
return {"name": result[1], "role": result[2]} if result else None
```

## Running tests

```bash
python3 -m pytest tests/test_module.py -v
```

## Pitfalls & Notes

- **Type hint inspection**: `__annotations__` returns a `dict`, not a string. Don't use `str(func.__annotations__)` — check the dict directly with `func.__annotations__['return']`.
- **Qualified imports for cross-module contracts**: When AC requires "qualified names" (e.g., `api.handle_request` not `from app.api import handle_request`), tests must verify module-level qualified access patterns.
- **Database testing**: Use `:memory:` for in-memory SQLite to avoid file I/O issues.
- **String matching patterns**: Using `if token in text:` does substring matching (e.g., `"ERROR" in "ERROR_HANDLER"` returns True). Always use `if text.startswith(token + ' ')` or `text.split()[0] == token` for token boundary matching. A line's log level is the FIRST token before any space, not any substring.