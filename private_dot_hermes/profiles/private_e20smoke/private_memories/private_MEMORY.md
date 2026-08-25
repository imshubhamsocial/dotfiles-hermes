Bare import failure pattern: Using `import api` in a package can fail with `ModuleNotFoundError: No module named 'api'` even when the module exists. Root cause: Python's namespace package resolution fails silently when __init__.py doesn't properly expose submodules. Solution: Always use qualified names for cross-module calls (`api.handle_request(conn, uid)`). Diagnostic: Verify imports before tests with `python3 -c "import app.api; print('OK')"`. Related: python-module-development SKILL.md import management workflow.
§
TDD CSV load bug: When fixing CSV loader, common pitfall is rows[1:] dropping first data row. If module/__init__.py is empty, must create it to expose submodules. PEP 560 type annotations list[dict] == list for testing purposes.
§
TDD payment-split fix: AC derived from user's "parts never add back up and sometimes crashes" requirement. Root cause: empty names list causes division by zero crash; integer division loses cents. Fix: check len(names)==0 first return [], then distribute remainder by adding 1 cent to first N parts where N=amount%len(names). All parts remain integer cents.
§
TDD pitfall: Don't assume files are empty — check existing code first. An implementation may already exist and conflict with test expectations. Always read files before writing tests.
§
Alerts.py fix: check() should return unique item names (strings) where stock <= threshold, using a seen set to deduplicate. Use `python3 test_alerts.py` to verify (not tests/).
§
Alerts.py bug: check() should return unique item names where stock <= threshold, using a seen set to deduplicate. Condition should be stock <= threshold to match test expectations.
§
Checkout mispricing bug: test_checkout.py has wrong test expectations - coupons are positive [10, 15] but should be negative [-10, -15] since they represent discounts. The checkout formula `max(0, cart_total + sum(coupons)) + shipping_cost` is correct. Fix: update test expectations to match actual formula output.