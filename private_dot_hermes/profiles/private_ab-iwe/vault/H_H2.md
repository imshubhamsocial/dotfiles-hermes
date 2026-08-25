---
title: H-H2 — task strategy
type: task-strategy
source: H-H2
status: verified
---

# H-H2 — verified strategy

Strategy for Reorder alerts fire at the wrong threshold and repeat: a working solution exists — the final attempt (pass) succeeded after 3 attempt(s), 360s. Key evidence: rc=0 OK---

## Subtask H-H2-3 (rc=0 OK)

```
## ✅ Verification Complete

**Test Result:** `python3 test_alerts.py` → **`"OK"` (exit code 0)**

**Changes made:**
- **File:** `alerts.py` line 5
- **Change:** `if stock < threshold` → `if stock <= threshold`

**What this fixes:**
- Items now alert when stock **equals OR goes below** the threshold (not just strictly below)
- Each item alerts only **once** when it first crosses the threshold
- Prevents duplicate alerts for the same item

**Acceptance criteria verified:**
1. ✅ `check([('a',5),('b',5),('a',2)], 5)` returns `['a','b']` - both items at threshold alert once
2. ✅ `check([('a',6)], 5
```

## Function check — check(...) called in the successful attempt

error class observed: pass; check args/imports

```
## ✅ Verification Complete

**Test Result:** `python3 test_alerts.py` → **`"OK"` (exit code 0)**

**Changes made:**
- **File:** `alerts.py` line 5
- **Change:** `if stock < threshold` → `if stock <= t…
```