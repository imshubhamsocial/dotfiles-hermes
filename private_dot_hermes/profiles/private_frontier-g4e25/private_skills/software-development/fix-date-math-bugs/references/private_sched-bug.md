# Session Bug: next_occurrence Off-By-One Error

## Problem
`next_occurrence(weekday, start, holidays)` returned the start date itself if it matched the weekday, instead of returning the NEXT matching weekday.

### Example from Session
```python
# Input
next_occurrence(1, date(2024, 1, 1), [])  # Start is Monday

# Buggy output
date(2024, 1, 1)  # WRONG: returned start date itself

# Correct output  
date(2024, 1, 8)  # RIGHT: next Monday after start
```

## Root Cause
Function definition:
```python
def next_occurrence(weekday, start, holidays):
    d = start  # BUG: should exclude start date
    while True:
        if d.weekday() == weekday and d not in holidays:
            return d
        d += timedelta(days=1)
```

## Fix
```python
def next_occurrence(weekday, start, holidays):
    d = start + timedelta(days=1)  # FIXED: start from next day
    while True:
        if d.weekday() == weekday and d not in holidays:
            return d
        d += timedelta(days=1)
```

## Test Cases to Verify
1. `next_occurrence(1, date(2024, 1, 1), [])` → `date(2024, 1, 8)`
2. `next_occurrence(2, date(2024, 1, 1), [])` → `date(2024, 1, 3)` (Tuesday after Monday start)
3. `next_occurrence(1, date(2024, 1, 1), [date(2024, 1, 1)])` → `date(2024, 1, 8)` (skip holiday start)
4. `next_occurrence(1, date(2024, 1, 1), [date(2024, 1, 8)])` → `date(2024, 1, 15)` (skip holiday next Monday)
