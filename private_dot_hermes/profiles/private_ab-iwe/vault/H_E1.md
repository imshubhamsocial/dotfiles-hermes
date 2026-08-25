---
title: H-E1 — task strategy
type: task-strategy
source: H-E1
status: verified
---

# H-E1 — verified strategy

Strategy for Order totals: fix the line-sum bug in total(): a working solution exists — the final attempt (pass) succeeded after 1 attempt(s), 234s. Key evidence: rc=0 OK---

## Subtask H-E1-1 (rc=0 OK)

```
**Verification complete.** All 5 tests pass:

| Test | Expected | Result |
|------|----------|--------|
| `<ID>` | `0.0` | ✓ |
| `<ID>` | `20.0` (1×10 + 2×5) | ✓ |
| `<ID>` | `10.0` | ✓ |
| `<ID>` | `0.0` | ✓ |
| `<ID>` | `0.0` | ✓ |

**Summary:** Fixed `orders.py` by changing `acc += qty + price` to `acc += qty * price`. The `total()` function now correctly computes the sum of `qty × price` for each item, returning `0.0` for empty lists.
```

## Function total — total(...) called in the successful attempt

error class observed: pass; check args/imports

```
**Verification complete.** All 5 tests pass:

| Test | Expected | Result |
|------|----------|--------|
| `<ID>` | `0.0` | ✓ |
| `<ID>` | `20.0` (1×10 +…
```