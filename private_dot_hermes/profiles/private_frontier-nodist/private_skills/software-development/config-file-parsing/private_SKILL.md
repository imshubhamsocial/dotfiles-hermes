---
name: config-file-parsing
description: "Parse config files with inline comment handling."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [config, parsing, text-processing, development]
    related_skills: [test-driven-development, plan]
---

# Config File Parsing with Inline Comments

## Overview

Parse configuration files handling inline comments, empty lines, and edge cases.

**Core principle:** Strip `#` comments from values (not just lines) when parsing config files.

## When to Use

**Always:**
- Parsing `.cfg`, `.conf`, `.ini`, or any config file format
- Handling inline comments like `key=value # comment`
- Processing YAML, INI, or custom config formats with comment support

## Pattern: Strip Inline Comments

```python
def parse(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)  # Split on first = only
            out[k.strip()] = v.strip().split('#')[0].strip()  # Remove inline # comment
    return out
```

## Test Pattern

```python
def test_parse_comment_after_value():
    """Handle comment appearing after value"""
    text = 'key=value # this is a comment'
    result = parse(text)
    self.assertEqual(result, {'key': 'value'})

def test_parse_comment_line():
    """Skip full comment lines"""
    text = '# This is a comment\nkey=value'
    result = parse(text)
    self.assertEqual(result, {'key': 'value'})
```

## Acceptance Criteria

1. Empty input returns `{}`
2. Comment lines (starting with `#`) are skipped
3. Values with multiple `=` split on first `=` only
4. Inline comments (`#`) after values are stripped
5. Whitespace around keys/values is trimmed

## Pitfalls

- **Don't use `max(coupons)` for negative values** — coupon values are negative (e.g., `-20` means 20 off). Use `min(coupons)` to find best discount.
- **Don't test after implementation** — write failing test first, watch it fail, then implement (TDD).
- **Don't handle all `=` signs** — split on first `=` only, preserve `=` in values.
- **Don't assume comment format** — always strip `#` from values as a general safety measure.

## Related Skills

- `test-driven-development` — write tests before implementation
- `plan` — plan parsing workflow before coding
