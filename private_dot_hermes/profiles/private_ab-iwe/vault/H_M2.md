---
title: H-M2 — task strategy
type: task-strategy
source: H-M2
status: verified
---

# H-M2 — verified strategy

Strategy for Config parser mishandles inline comments: a working solution exists — the final attempt (pass) succeeded after 1 attempt(s), 314s. Key evidence: rc=0 OK---

## Subtask H-M2-1 (rc=0 OK)

```
**Verification complete — all 5 tests pass (exit code 0)**

```
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
```

**Summary of fix:**
- **Bug:** `parse()` function treated inline comments (`#`) as part of values
- **Root cause:** `v.strip()` only removes leading/trailing whitespace, not inline comments
- **Fix:** `v.strip().split('#')[0].strip()` strips text after `#` from value
```

## Function parse — parse(...) called in the successful attempt

error class observed: pass; check args/imports

```
**Verification complete — all 5 tests pass (exit code 0)**

```
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
test_config.py::<ID>…
```

## Function strip — strip(...) called in the successful attempt

error class observed: pass; check args/imports

```
**Verification complete — all 5 tests pass (exit code 0)**

```
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
test_config.py::<ID>…
```

## Function split — split(...) called in the successful attempt

error class observed: pass; check args/imports

```
**Verification complete — all 5 tests pass (exit code 0)**

```
test_config.py::<ID> PASSED
test_config.py::<ID> PASSED
test_config.py::<ID>…
```