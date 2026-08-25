---
title: H-H1 — task strategy
type: task-strategy
source: H-H1
status: verified
---

# H-H1 — verified strategy

Strategy for Payment splitter: the split is losing cents and crashes on zero names: a working solution exists — the final attempt (pass) succeeded after 1 attempt(s), 419s. Key evidence: rc=0 OK---

## Subtask H-H1-1 (rc=0 OK)

```
## Complete ✅

**All tests pass (9/9)**

### Summary of changes:

**`payments.py`** - Fixed the payment split algorithm:
- Added empty names check to prevent `<ID>`
- Calculates base amount with integer division
- Calculates remainder cents
- Distributes remainder by adding 1 cent to the first N people where N = remainder

**Key fixes:**
1. `split(100, [])` → `[]` (no crash)
2. `split(100, ['A', 'B'])` → `[50, 50]` (sum = 100)
3. `split(101, ['A', 'B'])` → `[51, 50]` (sum = 101)
4. `split(1001, ['A', 'B', 'C', 'D', 'E'])` → `[201, 200, 200, 200, 200]` (sum = 1001)

All amounts are
```

## Function split — split(...) called in the successful attempt

error class observed: pass; check args/imports

```
## Complete ✅

**All tests pass (9/9)**

### Summary of changes:

**`payments.py`** - Fixed the payment split algorithm:
- Added empty names check to prevent `<ID>`
- Calculates base amou…
```