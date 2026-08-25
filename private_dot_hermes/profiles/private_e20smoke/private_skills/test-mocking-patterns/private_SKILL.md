---
name: test-mocking-patterns
description: Mock cross-module dependencies in Python tests
tags: [testing, mocking, unittest, pytest, cross-module]
---

# Test Mocking Patterns for Cross-Module Dependencies

This skill provides proven patterns for mocking database and authentication modules when testing functions that import and call other modules.

## Common Problem

When testing a function like `api.handle_request(conn, uid)` that calls `db.get_user(conn, uid)` and `auth.is_admin(user)`, the tests fail because:

1. `db.get_user` expects a cursor object with `fetchall()` method, not a direct list
2. `auth.is_admin` is imported in `app/api`, so you must patch `app.api.auth`, not `app.auth`

## Pattern 1: Mocking Database Cursors

**WRONG** - Returns list directly:
```python
mock_conn.execute.return_value = [user_dict]
```

**CORRECT** - Returns cursor object:
```python
mock_cursor = MagicMock()
mock_cursor.fetchall.return_value = [user_dict]
mock_conn.execute.return_value = mock_cursor
```

## Pattern 2: Patching Cross-Module Imports

**WRONG** - Patches module itself:
```python
with patch('app.auth') as mock_auth:
    ...
```

**CORRECT** - Patches at import site:
```python
with patch('app.api.auth') as mock_auth:
    mock_auth.is_admin.return_value = True
    result = api.handle_request(conn, uid)
```

## Pattern 3: Complete Test Example

```python
@patch('app.api.auth')
def test_handle_request_calls_auth_is_admin(self, mock_auth):
    """AC4: must call auth.is_admin (monkeypatch-checked)."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{'id': 1, 'username': 'alice', 'role': 'admin'}]
    mock_conn.execute.return_value = mock_cursor
    mock_auth.is_admin.return_value = True
    
    result = api.handle_request(self.mock_conn, 1)
    
    # Verify both cross-module calls were made
    mock_conn.execute.assert_called_once()
    mock_auth.is_admin.assert_called_once()
    
    # Verify correct arguments were passed
    call_args = mock_auth.is_admin.call_args
    self.assertEqual(call_args[0][0], self.mock_user_alice)
```

## Verification

Run the tests to confirm all cross-module dependencies are properly mocked:
```bash
python -m unittest app.test_api -v
```

All 5 test cases should pass, including tests that verify `db.get_user` and `auth.is_admin` calls.
