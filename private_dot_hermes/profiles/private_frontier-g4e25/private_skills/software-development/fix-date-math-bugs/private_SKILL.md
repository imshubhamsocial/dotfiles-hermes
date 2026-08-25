---
name: fix-date-math-bugs
category: software-development
description: Fix off-by-one errors in date/weekday functions
---

# Fix Date/Weekday Logic Bugs

**Trigger:** When `next_occurrence`, `next_weekday`, or similar date-finding functions return incorrect results due to off-by-one errors, boundary conditions, or holiday collisions.

**Use when:** A datetime function is supposed to find the NEXT matching weekday (excluding start date) but returns the wrong date.

**Behavior:**
1. Derive expected output from tests BEFORE implementing the fix.
2. Patch the function to exclude start date from search (`d = start + timedelta(days=1)` instead of `d = start`).
3. Verify all tests pass.

**Pitfalls:**
- Functions with `while True: if d.weekday() == weekday and d not in holidays: return d; d += timedelta(days=1)` and `d = start` will return `start` if it matches.
- Correct pattern is `d = start + timedelta(days=1)` to find the NEXT matching weekday.
- Always verify expected date mathematically before patching.

**References:**
- `references/sched-bug.md` — `next_occurrence` returned `2024-08-10` when expected `2024-08-17`.
- `scripts/verify_date_math.py` — Deterministic check script for expected weekday progression.
