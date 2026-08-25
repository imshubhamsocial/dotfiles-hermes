Checkout pricing fix: coupon values are negative (e.g., -20 = 20 off). Use min(coupons) to find best discount, not max(). Formula is cart_total + best (adding the negative value).
§
User prefers TDD workflow in order: PLAN -> TESTS -> IMPLEMENT -> VERIFY. Always write implementation plan in PLAN.md before any code.
§
Alerts.py fix: When tests expect items to fire when stock < threshold (not crossing from >= to <), use simple "fire if below" logic, NOT "fire only when crossing". Test assertions override test comments. Pattern: check() should return items where stock < threshold, track seen to fire once per run.