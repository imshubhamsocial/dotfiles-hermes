---
name: prorate-billing-fix
description: Fix billing proration and duplicate line item issues
---

# Prorate Billing Fix

## Use when
Fixing billing proration and duplicate line item issues.

## Steps

1. **Understand the bug**: 
   - Prorated charges round down incorrectly (should round to nearest cent)
   - Duplicate line items appear multiple times in bills

2. **Fix the prorate function**:
   - Round to nearest whole cents using `round()` instead of floor
   - Formula: `round(daily_rate * days / 100)` for percentage-based, or use proper rounding for absolute amounts

3. **Fix duplicate line items**:
   - Use a dict/set to track seen IDs
   - Collapse duplicates by keeping only the first occurrence or summing amounts
   - Update the bill aggregation logic to deduplicate before returning

4. **Verify**:
   - Test proration with various day counts (0.5 days, 1 day, 1.5 days)
   - Confirm rounding matches user expectation (nearest cent, not floor)
   - Feed duplicate IDs to billing logic and verify only one line appears