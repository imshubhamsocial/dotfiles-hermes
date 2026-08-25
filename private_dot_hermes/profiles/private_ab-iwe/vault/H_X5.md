---
title: H-X5 — task strategy
type: task-strategy
source: H-X5
status: verified
---

# H-X5 — verified strategy

Strategy for Feature-flag service: precedence and cache staleness are wrong: a working solution exists — the final attempt (pass) succeeded after 1 attempt(s), 1161s. Key evidence: rc=0 OK---

## Subtask H-X5-1 (rc=0 OK)

```
All 9 tests pass. Here's the verification summary:

## ✅ Verification Complete

**Test Results (9/9 passed):**
- `<ID>` - Override value is returned correctly
- `<ID>` - Flags are cached on first evaluation
- `<ID>` - Override invalidates the cached flag
- `<ID>` - Flag changes are reflected on next evaluate
- `<ID>` - Overrides are scoped to specific flags
- `<ID>` - Norm
```

## Function evaluate — evaluate(...) called in the successful attempt

error class observed: pass; check args/imports

```
**All 5 tests passed** (exit code 0).

## Fix Applied

**Bug**: Flag service evaluated cache before flags, serving stale values instead of fresh flag values.

**Root cause**: Evaluation order was `ove…
```

## Function get — get(...) called in the successful attempt

error class observed: pass; check args/imports

```
**All 5 tests passed** (exit code 0).

## Fix Applied

**Bug**: Flag service evaluated cache before flags, serving stale values instead of fresh flag values.

**Root cause**: Evaluation order was `ove…
```