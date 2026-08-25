---
name: billing-aggregation-pattern
description: "Aggregate numeric values by key (sum duplicates)."
---

# Billing Aggregation Pattern

## When to Use
Deduplicating bill lines by ID where amounts should be summed.

## Workflow

### Step 1: Use defaultdict for Accumulation
```python
from collections import defaultdict
seen = defaultdict(float)
for item in items:
    key, value = extract(item)
    seen[key] += value  # Always add, not keep-first
```

### Step 2: Return Consolidated List
```python
return [(key, seen[key]) for key in seen]
```

## Pitfalls
- Don't use dict - it keeps only first value
- Don't append to result during iteration
- Use float for decimal accumulation

## Example
Input: `[('a',1), ('a',1), ('b',2)]` → Output: `[('a',2), ('b',2)]`
