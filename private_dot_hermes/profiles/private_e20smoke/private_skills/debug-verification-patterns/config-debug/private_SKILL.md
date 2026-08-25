---
name: config-debug
description: Debug Python config parser with comment handling bugs
tags: [python, config, debug]
---

## Use when
Debugging `config.py` parse() function that fails to handle comments correctly after values.

## Problem
Lines starting with `#` should be skipped. The current implementation incorrectly strips trailing `# comment` from VALUES instead of keeping them as-is.

## Root cause
The code at line 10-11 strips `#` from `v` (the value), but the comment says it should strip from the key `k`. 

## Fix
Change the comment stripping from `v` (value) to `k` (key):
- Remove lines 9-11 (the incorrect comment stripping from value)

## Files to fix
`config.py` (in your project sandbox)

## Acceptance criteria
1. Lines starting with `#` are skipped entirely
2. Comments after `=` are NOT stripped from values
3. `parse(text)` returns correct dict
4. `parse("# KEY = value\n")` returns `{'KEY': 'value'}`

## Code changes
Remove lines 9-11 from config.py:
```python
# Strip trailing comment (# comment) from value  <-- REMOVE THIS
if '#' in v:  <-- REMOVE THIS
    v = v.split('#')[0].strip()  <-- REMOVE THIS
```

## Test expectations
- `parse("# KEY = value\n")` → `{'KEY': 'value'}`
- `parse("# KEY=value # comment\n")` → `{'KEY': 'value'}`
- `parse("# COMMENT\n")` → `{}`