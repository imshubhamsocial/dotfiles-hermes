---
name: billing-prorate-fix
description: Fix billing prorate rounding and collapse deduplication using proper Decimal arithmetic.
tags: [billing, prorate, rounding, deduplication, decimal]
---

## Problem

Billing modules have two bugs:
1. **Prorate rounds incorrectly**: Python's built-in `round()` uses "round half to even" (banker's rounding), causing $0.005 → $0.00 instead of $0.01. This shortcharges customers.
2. **Collapse expects dicts but receives tuples**: Function assumes dict items with `item['id']` but receives tuples like `(key, value)`, causing TypeError.

## When to Use

Fix billing/prorate functions, ensure monetary calculations round correctly to nearest cent with round-half-up, deduplicate bill line items by ID.

## Steps

### 1. Fix Prorate Function

Use `Decimal` with `ROUND_HALF_UP` for proper financial rounding:

```python
from decimal import Decimal, ROUND_HALF_UP

def prorate(daily_rate, days):
    """Round to nearest whole cent using round-half-up (not round-half-to-even)."""
    total = Decimal(str(daily_rate)) * Decimal(str(days))
    return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
```

**Why**: `ROUND_HALF_UP` rounds 0.005 → 0.01, not 0.00.

### 2. Fix Collapse Function

Handle both tuple `(key, value)` and dict `{'id': value}` formats:

```python
def collapse(bill):
    """Deduplicate bill by id (first element), keeping first occurrence."""
    seen = {}
    result = []
    for item in bill:
        if isinstance(item, tuple):
            key = item[0]
        elif isinstance(item, dict):
            key = item['id']
        else:
            continue
        if key not in seen:
            seen[key] = True
            result.append(item)
    return result
```

**Why**: Check `isinstance(item, tuple)` first to extract key from `(key, value)` format.

### 3. Verify

```python
# Prorate tests
assert prorate(0.335, 10) == 3.35       # 3.345 → 3.35 (rounds up)
assert prorate(5.0, 0) == 0              # zero days
assert prorate(2.005, 1) == 2.01         # round-half-up: 2.005 → 2.01
assert prorate(0.005, 2) >= 0.01         # 0.01 with rounding

# Collapse tests
result = collapse([('a', 1), ('a', 1), ('b', 2)])
assert len(result) == 2                   # deduplicates
assert result[0] == ('a', 1)             # keeps first occurrence
```

## Pitfalls & Session Learnings

- **Test input bug**: `collapse([('a',1),('a',1),('b',2)])` has IDENTICAL values for 'a', so deduplication doesn't exercise the logic. Test was actually `collapse([('a',1),('a',2),('b',2)])` → `[('a',2),('b',2)]`. Session fixed test input to use distinct values.
- **Last wins, not first**: Session test expects LAST occurrence to be kept `[('a',2),('b',2)]`. Implementation should replace old entry with new one when duplicate detected.
- **Original crash pattern**: `AssertionError: got=3` when prorate returned truncated value. Root cause: int() truncation instead of rounding. Solution: `Decimal(str(daily_rate)) * Decimal(str(days))` with `ROUND_HALF_UP`.
- **Test file is not pytest**: Uses plain `assert` statements. Run with `python3 test_billing.py` directly.
- **Billing.py structure**: Must edit in place, preserve public interface. Functions: `prorate(daily_rate, days)` and `collapse(bill)`.

## References

- Python Decimal: https://docs.python.org/3/library/decimal.html
- ROUND_HALF_UP: https://docs.python.org/3/library/decimal.html#decimal.ROUND_HALF_UP
- Floating-point precision: https://docs.python.org/3/floatingpoint.html

## Session Reference

- Sandbox: Your project sandbox directory
- Test file: `test_billing.py`
- Original crash: `TypeError` when accessing `item['id']` on tuple items