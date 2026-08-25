# Concrete collapse() Implementation Example

## File: `billing.py`

```python
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def prorate(daily_rate, days):
    """Round to nearest whole cent using round-half-up."""
    total = Decimal(str(daily_rate)) * Decimal(str(days))
    return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def collapse(bill):
    """Deduplicate bill by id, aggregating values (summing duplicates)."""
    seen = defaultdict(float)
    for item in bill:
        if isinstance(item, tuple):
            key = item[0]
            value = item[1]
        elif isinstance(item, dict):
            key = item['id']
            value = item.get('value', item.get('amount'))
        else:
            continue
        if key not in seen:
            seen[key] = value
        else:
            seen[key] += value
    return [(key, seen[key]) for key in seen]
```

## Test File: `test_billing.py`

```python
from billing import prorate, collapse

# Test prorate: rounds to nearest cent (not truncates)
assert prorate(0.335, 10) == 3.35  # 3.35 rounds to 3.35
assert prorate(5.0, 0) == 0  # 0 days = 0

# Test collapse: aggregates values (sums duplicates)
assert collapse([('a',1), ('a',1), ('b',2)]) == [('a', 2), ('b', 2)]
# Wrong: [('a',1), ('b',2)] - keeps first, doesn't sum
```

## Key Pattern
- Use `defaultdict(float)` for accumulation
- Always `+= value`, never `if key not in seen: seen[key] = value`
- Return consolidated list comprehension, don't append during iteration
