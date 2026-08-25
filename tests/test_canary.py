#!/usr/bin/env python3
"""
Offline tests for the Tier-2 canary-sequence leak detector
(Session 11 follow-up 6). No GPU needed.

Run: python3 tests/test_canary.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.arena_runner import grade_task  # noqa: E402
from tests.canary import (  # noqa: E402
    CANARYABLE_LANGS,
    inject_canary,
    new_canary,
    scan_output,
)


class TestCanaryCore(unittest.TestCase):
    def test_new_canary_unique_and_prefixed(self):
        a, b = new_canary(), new_canary()
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("CANARY-"))
        self.assertGreater(len(a), 20)  # uuid4 hex

    def test_inject_python_appends_hidden_comment(self):
        body = "def greet(name):\n    return name"
        canaried, canary = inject_canary(body, "python")
        self.assertIn(f"# {canary}", canaried)
        self.assertTrue(canaried.endswith(f"# {canary}"))
        # original body preserved verbatim above the comment
        self.assertIn(body, canaried)

    def test_inject_bash_appends_comment(self):
        body = "printf '%s\\n' 7"
        canaried, canary = inject_canary(body, "bash")
        self.assertIn(f"# {canary}", canaried)

    def test_inject_json_text_untouched(self):
        # a comment would pollute a JSON/text format demo — leave unchanged
        for lang in ("json", "text"):
            body = '{"name": "get_weather"}' if lang == "json" else "10.5"
            out, canary = inject_canary(body, lang)
            self.assertEqual(out, body)
            self.assertFalse(scan_output(out, canary))
        self.assertNotIn("json", CANARYABLE_LANGS)
        self.assertNotIn("text", CANARYABLE_LANGS)

    def test_scan_novel_code_clean(self):
        c = new_canary()
        novel = "def max_rolling(nums, k):\n    return [max(nums[i:i+k]) for i in range(len(nums)-k+1)]"
        self.assertFalse(scan_output(novel, c))

    def test_scan_verbatim_copy_detected(self):
        c = new_canary()
        exemplar, _ = inject_canary("def flatten(x):\n    return x", "python", c)
        # a model copying the exemplar VERBATIM carries the hidden comment
        self.assertTrue(scan_output(exemplar, c))

    def test_scan_partial_uuid_no_false_positive(self):
        c = new_canary()
        self.assertFalse(scan_output(c[:12], c))  # truncated token ≠ full token


class TestArenaCanaryGate(unittest.TestCase):
    def _task(self, canary=None):
        t = {
            "id": "CAN-T1",
            "prompt": "task",
            "grader": {"type": "py_stdout", "mode": "exact_string",
                       "expected": "ok"},
        }
        if canary:
            t["grader"]["canary"] = canary
        return t

    def test_no_canary_no_gate(self):
        # py_stdout runs the extracted script: print('ok') -> stdout 'ok'
        ok, note = grade_task(self._task(), "```python\nprint('ok')\n```")
        self.assertTrue(ok, note)

    def test_leaked_output_fails_with_canary_note(self):
        c = new_canary()
        ok, note = grade_task(self._task(canary=c), f"```python\n# {c}\nprint('x')\n```")
        self.assertFalse(ok)
        self.assertIn("CANARY_LEAK", note)

    def test_clean_output_passes_with_canary_set(self):
        c = new_canary()
        ok, note = grade_task(self._task(canary=c), "```python\nprint('ok')\n```")
        self.assertTrue(ok, note)

    def test_gate_fires_before_type_grader(self):
        # even a task whose TYPE grader would PASS is failed when the canary
        # leaks (proven-copy is a hygiene violation, not a format miss)
        c = new_canary()
        t = self._task(canary=c)
        # exact_string expected 'ok' — the output contains the canary so the
        # gate must fail it even though the content would match otherwise
        ok, note = grade_task(t, f"ok # {c}")
        self.assertFalse(ok)
        self.assertIn("CANARY_LEAK", note)


if __name__ == "__main__":
    unittest.main()
