---
title: H-X1 — task strategy
type: task-strategy
source: H-X1
status: verified
---

# H-X1 — verified strategy

Strategy for Checkout pipeline: coupons stack wrong and shipping tiers mis-price: a working solution exists — the final attempt (pass) succeeded after 1 attempt(s), 1187s. Key evidence: rc=0 OK---

## Subtask H-X1-1 (rc=0 OK)

```
**Verification Complete - All 4 tests PASSED**

```
<ID>      PASSED  (100 - 20 + 5 = 85)
<ID>     PASSED  (100 - (-5) + 5 = 110)
<ID>            PASSED  (100 - 15 + 5 = 90)
<ID>            PASSED  (100 - 0 + 5 = 105)
```

**Fix Summary:**
- **Bug:** `checkout.py` was summing all coupons (`best += c`) instead of applying the maximum single coupon
- **Fix:** Changed to `best = max(coupons) if coupons else 0`
- **Result:** Checkout now correctly applies the best (maximum) coupon discount, ali
```

## Function max — max(...) called in the successful attempt

error class observed: pass; check args/imports

```
**Verification Complete - All 4 tests PASSED**

```
<ID>      PASSED  (100 - 20 + 5 = 85)
<ID>     PASSED  (100 - (-5) + 5 = 110)
test_checko…
```