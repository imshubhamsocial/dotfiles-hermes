---
name: sandbox-checkout-fix
description: Fix checkout bugs where coupons add instead of subtract
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [bug-fix, pricing, checkout, tdd, sandbox]
    category: software-development
    related_skills: [test-driven-development, systematic-debugging, plan]
---

# Sandbox Checkout Pricing Fix

## Overview

Debug and fix pricing misalignments in checkout modules where coupons are added instead of subtracted.

**Core issue:** Double-negative bug - `best -= c` creates negative discount, then `cart - best` adds it.

```python
# BEFORE (BUGGY):
best -= c          # negative → cart - (-discount) = cart + discount
return max(0, cart - best) + shipping

# AFTER (FIXED):
best += c          # positive → cart - discount
return max(0, cart - best) + shipping
```

## When to Use

- Checkout pipeline mispricing (totals don't match)
- Independent sandbox modules with cart/shipping/checkout
- Coupon/discount logic causing unexpected overpayment

## The Bug

**Symptoms:**
- Empty coupons → correct (accidental)
- One coupon → cart + coupon + shipping (WRONG)
- Multiple coupons → cart + all + shipping (WRONG)

**Root Cause:** `best -= c` creates negative discount. `cart - best` subtracts negative = adds.

**The Fix:** Change `best -= c` to `best += c`.

## Red-Green-Refactor Cycle

### RED — Write Failing Test

Tests must pass values, not functions:

```python
items = [("item1", 10, 2), ("item2", 5, 3)]  # cart = 35
total = cart_total(items)
shipping_val = shipping(5)
result = checkout(total, shipping_val, [5])
assert result == 38  # 35 - 5 + 8
```

**Critical:** Tests compute values (`cart_total(items)`), don't pass functions.

### Verify RED — Watch It Fail

```bash
pytest test_checkout.py::test_one_coupon -v
# Should show: assert 48 == 38
```

### GREEN — Minimal Fix

```python
# checkout.py
def checkout(cart, shipping, coupons):
    best = 0
    for c in coupons:
        best += c  # FIX: was -= c
    return max(0, cart - best) + shipping
```

### Verify GREEN — All Tests Pass

```bash
pytest test_checkout.py -v
# All 6 tests should pass
```

## Acceptance Criteria

1. **Empty coupons:** `cart + shipping` (no discount)
2. **One coupon:** `cart - coupon + shipping`
3. **Multiple coupons:** `cart - sum(coupons) + shipping`
4. **Zero coupons:** `cart + shipping` (baseline)

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Passing functions to `checkout()` | Pass computed values: `cart_total(items)`, `shipping(weight)` |
| Double-negative (`best -= c` then `cart - best`) | Use `best += c` so discount is positive |
| Wrong arithmetic: `cart - (-5)` instead of `cart - 5` | Ensure discount accumulates positively |

## Verification Command

```bash
pytest test_checkout.py -v
```

Expected: All tests pass with correct arithmetic.

## Related Skills

- `test-driven-development`: Core TDD cycle (RED-GREEN-REFACTOR)
- `systematic-debugging`: Root cause analysis of pricing bugs
- `plan`: Document acceptance criteria before coding