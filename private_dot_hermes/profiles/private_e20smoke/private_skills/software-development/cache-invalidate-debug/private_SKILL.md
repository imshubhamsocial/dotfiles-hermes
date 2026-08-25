---
name: cache-invalidate-debug
description: Fix caching systems serving stale values when state changes.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [caching, debugging, invalidation]
    related_skills: [test-driven-development]
---

# Cache Invalidation Debugging

## Overview

When a system caches values from mutable state, the cache may serve stale values if state changes occur independently of the caching layer.

## When to Use

- Cache serves stale values despite source state changing
- Override mechanism exists but cache bypasses it incorrectly
- Multiple components interact (flags, cache, evaluation logic)

## Root Cause Pattern

1. Component A stores mutable state
2. Component B stores cached values independently  
3. Evaluation returns cached values without verifying against source

## Debugging Steps

### Step 1: Trace the Data Flow
Identify all components that read/write:
- **Cache layer**: What values are stored, when?
- **Source layer**: What state is being cached?
- **Evaluation logic**: When is cache checked vs. source queried?

### Step 2: Identify the Invalidation Gap
Ask: "When does the cache get invalidated?"
- Is `invalidate()` called explicitly?
- Is there a hook in the source layer that should trigger invalidation?

### Step 3: Choose the Fix Pattern

**Pattern A: Source triggers invalidation**
```python
class Flags:
    def set(self, name, value):
        self.invalidate(name)  # Invalidate when state changes
        self.store[name] = value
```

**Pattern B: Evaluation detects staleness**
```python
def evaluate(flags, cache, name):
    cached = cache.get(name)
    current = flags.get(name)
    if cached is not current:  # Detect stale
        cache.invalidate(name)
```

### Step 4: Verify the Fix
Run tests:
1. Set source state
2. Evaluate and cache
3. Change source state
4. Evaluate again → should return new value, not cached stale

## Pitfalls

1. **Invalidate too early**: Invalidating before setting causes `get()` to return None
2. **Invalidate both flags and cache**: Can cause `get()` to return None after invalidation
3. **Assume flags.set() invalidates**: Often it doesn't

## Verification

Test sequence:
```python
flags.set('flag', True)
evaluate(flags, cache, 'flag')  # Caches True

flags.set('flag', False)
evaluate(flags, cache, 'flag')  # Should return False, not True
```

Expected: `False`

If `None`: Flag removed before set.
If `True`: Cache not invalidated.
