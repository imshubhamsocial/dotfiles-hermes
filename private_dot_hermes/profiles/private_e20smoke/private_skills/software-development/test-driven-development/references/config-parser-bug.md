# Config Parser Bug Pattern: Inline Comments After Values

## The Bug

Parser doesn't strip trailing comment text after `=` split.

**Input:** `key=value # comment`  
**Buggy output:** `{'key': 'value # comment'}`  
**Correct output:** `{'key': 'value'}`

## Root Cause

```python
k, v = line.split('=', 1)
out[k.strip()] = v.strip()  # v includes trailing comment text
```

No stripping of content after `#` from the value.

## The Fix

Strip trailing `#` comment text from value after split:

```python
if '=' in line:
    k, v = line.split('=', 1)
    # Strip trailing comment (# comment) from value
    if '#' in v:
        v = v.split('#')[0].strip()
    out[k.strip()] = v.strip()
```

## Acceptance Criteria

- `parse("key=value # comment")` → `{'key': 'value'}`
- `parse("# comment only")` → `{}`
- `parse("key=value")` → `{'key': 'value'}` (no regression)
- `parse("key=value#more#hashes")` → `{'key': 'value'}`

## Test Cases

```python
def test_parse_inline_comment():
    """Inline comment after value is stripped."""
    result = config.parse("key=value # comment")
    assert result == {'key': 'value'}

def test_parse_comments_only():
    """Comment-only lines return empty dict."""
    result = config.parse("# comment only")
    assert result == {}

def test_parse_no_regression():
    """Values without comments still work."""
    result = config.parse("key=value")
    assert result == {'key': 'value'}

def test_parse_multiple_with_inline_comments():
    """Multiple key-value pairs with inline comments."""
    result = config.parse("key=value # comment\nother=other_val # another")
    assert result == {'key': 'value', 'other': 'other_val'}

def test_parse_value_multiple_hashes():
    """Only first # is comment start."""
    result = config.parse("key=value#more#hashes")
    assert result == {'key': 'value'}
```

## Pattern to Remember

When fixing config parsers:
1. Split on `=` to get key/value
2. Strip trailing `#` content from value (if any)
3. Strip whitespace from key and value

This pattern appears in INI-style parsers and config file processors.
