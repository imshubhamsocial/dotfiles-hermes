#!/usr/bin/env python3
"""
Offline tests for the Tier-2 grader contracts (Session 11 follow-up 5).

Covers tests/grader_contracts.py (negative-constraint AST-hash, hidden-pytest,
stateful mock-API) with reference-solution PASS cases and sabotage FAIL cases
for each contract, plus the arena grade_task dispatch path. No GPU needed.

Run: python3 tests/test_grader_contracts.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.grader_contracts import (  # noqa: E402
    grade_hidden_pytest,
    grade_negative_constraint,
    grade_stateful_api,
)

# A multi-function pricing module: `apply_discount` may be edited, `tax_rate`
# is the preserved function that must NOT change (AST-identical). The
# ORIGINAL has a bug in apply_discount (integer-truncating discount when pct
# is an int), which the fix repairs.
PRICING_ORIG = '''\
def tax_rate(amount):
    """VAT for the given amount (fixed 20%)."""
    return amount * 0.20


def apply_discount(amount, pct):
    discount = amount * pct // 100
    return amount - discount
'''

# Reference fix: apply_discount is repaired (float rounding), tax_rate left
# untouched (same logic, even re-spelled with different whitespace/comments —
# must still hash identical via unparse).
PRICING_FIX = '''\
def tax_rate(amount):
    """VAT for the given amount (fixed 20%)."""
    return amount * 0.20


def apply_discount(amount, pct):
    discount = amount * pct / 100.0
    return round(amount - discount, 2)
'''

# Sabotage: the preserved tax_rate function's BODY changed (0.25 instead of 0.20).
PRICING_SABOTAGE_PRESERVE = '''\
def tax_rate(amount):
    """VAT for the given amount (fixed 25%!)."""
    return amount * 0.25


def apply_discount(amount, pct):
    discount = amount * pct / 100.0
    return round(amount - discount, 2)
'''

# Sabotage: changed function never touched (identical to original).
PRICING_SABOTAGE_NOCHANGE = PRICING_ORIG


def pricing_grader(**over):
    g = {
        "type": "negative_constraint",
        "module": "pricing",
        "fixtures": {"pricing.py": PRICING_ORIG},
        "preserve": ["tax_rate"],
        "changed": ["apply_discount"],
    }
    g.update(over)
    return {"grader": g}


class TestNegativeConstraint(unittest.TestCase):
    def test_reference_fix_passes(self):
        ok, note = grade_negative_constraint(PRICING_FIX, pricing_grader()["grader"])
        self.assertTrue(ok, note)

    def test_preserve_violation_fails(self):
        ok, note = grade_negative_constraint(
            PRICING_SABOTAGE_PRESERVE, pricing_grader()["grader"])
        self.assertFalse(ok)
        self.assertIn("NEGATIVE_CONSTRAINT_VIOLATION", note)

    def test_expected_change_missing_fails(self):
        ok, note = grade_negative_constraint(
            PRICING_SABOTAGE_NOCHANGE, pricing_grader()["grader"])
        self.assertFalse(ok)
        self.assertIn("EXPECTED_CHANGE_MISSING", note)

    def test_whitespace_comment_drift_not_a_violation(self):
        # cosmetic drift (whitespace / comment wording) must NOT trip the hash
        fixed = PRICING_FIX.replace('amount * 0.20', 'amount * 0.20  ').replace(
            '# VAT for the given amount (fixed 20%).',
            '#   VAT  for  the  given  amount  (fixed 20%)  .')
        ok, note = grade_negative_constraint(fixed, pricing_grader()["grader"])
        self.assertTrue(ok, note)

    def test_syntax_error_fails(self):
        ok, note = grade_negative_constraint(
            "def tax_rate(amount):\n  return )", pricing_grader()["grader"])
        self.assertFalse(ok)
        self.assertIn("SYNTAX_ERROR", note)


class TestHiddenPytest(unittest.TestCase):
    # Public tests are shown in the PROMPT only; the grader runs the hidden
    # suite (aggressive edge cases) that hardcoded answers cannot pass.
    HIDDEN = '''\
import solution


def test_basic():
    assert solution.max_rolling([1, 3, 2, 8, 5], 3) == [3, 8, 8]


def test_window_larger_than_list():
    assert solution.max_rolling([1, 2], 5) == [2]


def test_empty_list():
    assert solution.max_rolling([], 3) == []


def test_negatives():
    assert solution.max_rolling([-5, -1, -9], 2) == [-1, -1]


def test_window_one():
    assert solution.max_rolling([4, 7, 1], 1) == [4, 7, 1]
'''

    def _task(self, code):
        return {
            "id": "GC-02",
            "grader": {"type": "hidden_pytest", "module": "solution",
                       "hidden_tests": self.HIDDEN},
            "code": code,
        }

    def test_reference_solution_passes(self):
        # full-window rolling max: one output per complete window; a window
        # larger than the list degenerates to the whole list
        ref = ("def max_rolling(nums, k):\n"
               "    if not nums or k <= 0:\n"
               "        return []\n"
               "    if k > len(nums):\n"
               "        return [max(nums)]\n"
               "    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]\n")
        ok, note = grade_hidden_pytest(ref, self._task(ref)["grader"])
        self.assertTrue(ok, note)

    def test_hardcoded_public_answers_fail(self):
        # only handles the two PUBLIC examples; the hidden suite's empty /
        # negatives / window>len cases expose it
        hard = ("def max_rolling(nums, k):\n"
                "    if nums == [1, 3, 2, 8, 5] and k == 3:\n"
                "        return [3, 8, 8]\n"
                "    return []\n")
        ok, note = grade_hidden_pytest(hard, self._task(hard)["grader"])
        self.assertFalse(ok)

    def test_missing_module_fails(self):
        ok, note = grade_hidden_pytest("x = 1", self._task("x = 1")["grader"])
        self.assertFalse(ok)

    def _without_pytest(self):
        import tests.grader_contracts as gc
        saved = gc.PYTEST_AVAILABLE
        gc.PYTEST_AVAILABLE = False
        self.addCleanup(lambda: setattr(gc, "PYTEST_AVAILABLE", saved))
        return gc

    def test_pytest_less_fallback_still_runs_tests(self):
        # reviewer catch: the pytest-less path must ACTUALLY run the hidden
        # test functions (a bare `python test_hidden.py` executes nothing and
        # exits 0 -> silent false PASS). Reference still passes, hardcoded
        # answers still fail, and a file with no test_* funcs is rejected.
        gc = self._without_pytest()
        ref = ("def max_rolling(nums, k):\n"
               "    if not nums or k <= 0:\n"
               "        return []\n"
               "    if k > len(nums):\n"
               "        return [max(nums)]\n"
               "    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]\n")
        ok, note = gc.grade_hidden_pytest(ref, self._task(ref)["grader"])
        self.assertTrue(ok, note)
        hard = ("def max_rolling(nums, k):\n"
                "    if nums == [1, 3, 2, 8, 5] and k == 3:\n"
                "        return [3, 8, 8]\n"
                "    return []\n")
        ok_bad, note_bad = gc.grade_hidden_pytest(hard, self._task(hard)["grader"])
        self.assertFalse(ok_bad)
        self.assertIn("FAIL", note_bad)
        # no test_* functions anywhere -> runner refuses to pass
        g = self._task("x = 1")["grader"]
        g["hidden_tests"] = "print('no tests here')\n"
        ok_none, note_none = gc.grade_hidden_pytest("x = 1", g)
        self.assertFalse(ok_none)
        self.assertIn("no test_* functions", note_none)


class TestStatefulApi(unittest.TestCase):
    def _task(self, code):
        return {
            "id": "GC-03",
            "grader": {
                "type": "stateful_api",
                "module": "client",
                "config_module": "config",
                "expected_calls": [
                    {"method": "POST", "path": "/api/orders",
                     "body_contains": {"item": "pen", "qty": 2}},
                    {"method": "GET", "path": "/api/orders/1"},
                ],
                "responses": {
                    "POST /api/orders": {"json": {"id": 1, "status": "created"}},
                    "GET /api/orders/1": {"json": {"id": 1, "item": "pen"}},
                },
            },
            "code": code,
        }

    REF_CLIENT = '''\
import config
import json
import urllib.request


def call(method, path, body=None):
    url = config.API_BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


created = call("POST", "/api/orders", {"item": "pen", "qty": 2})
call("GET", "/api/orders/1")
'''

    def test_reference_client_passes(self):
        ok, note = grade_stateful_api(self.REF_CLIENT, self._task("")["grader"])
        self.assertTrue(ok, note)

    def test_wrong_order_fails(self):
        # GET before POST violates the expected sequence
        bad = self.REF_CLIENT.replace(
            'created = call("POST", "/api/orders", {"item": "pen", "qty": 2})\n'
            'call("GET", "/api/orders/1")',
            'call("GET", "/api/orders/1")\n'
            'created = call("POST", "/api/orders", {"item": "pen", "qty": 2})')
        ok, note = grade_stateful_api(bad, self._task("")["grader"])
        self.assertFalse(ok)

    def test_wrong_payload_fails(self):
        bad = self.REF_CLIENT.replace('"qty": 2', '"qty": 5')
        ok, note = grade_stateful_api(bad, self._task("")["grader"])
        self.assertFalse(ok)
        self.assertIn("missing", note)

    def test_crashed_client_fails(self):
        ok, note = grade_stateful_api("raise RuntimeError('boom')",
                                      self._task("")["grader"])
        self.assertFalse(ok)


class TestArenaDispatch(unittest.TestCase):
    def test_grade_task_dispatches_negative_constraint(self):
        from tests.arena_runner import grade_task
        task = pricing_grader()
        task["id"] = "GC-01"
        # code inside the arena's fenced format
        raw = "```python\n" + PRICING_FIX + "\n```"
        ok, note = grade_task(task, raw)
        self.assertTrue(ok, note)
        raw_bad = "```python\n" + PRICING_SABOTAGE_PRESERVE + "\n```"
        ok_bad, _ = grade_task(task, raw_bad)
        self.assertFalse(ok_bad)

    def test_grade_task_dispatch_unknown_contract(self):
        from tests.grader_contracts import grade_contract
        task = {"grader": {"type": "not_a_contract"}}
        ok, note = grade_contract(task, "x = 1")
        self.assertFalse(ok)
        self.assertIn("unknown contract", note)


if __name__ == "__main__":
    unittest.main()
