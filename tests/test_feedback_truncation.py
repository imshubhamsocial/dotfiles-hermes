#!/usr/bin/env python3
"""
Offline tests for the Tier-2 truncated ruff-feedback engine
(Session 11 follow-up 6). No GPU needed.

Run: python3 tests/test_feedback_truncation.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.feedback_truncation import (  # noqa: E402
    is_ruff_line,
    truncate_lint_feedback,
)


class TestRuffLineDetection(unittest.TestCase):
    def test_default_ruff_format(self):
        self.assertTrue(is_ruff_line("src/app.py:12:5: F821 undefined name 'config'"))
        self.assertTrue(is_ruff_line("calc.py:3:1: E501 line too long (131 > 120)"))

    def test_compact_ruff_format(self):
        self.assertTrue(is_ruff_line("src/app.py:14: F401 'os' imported but unused"))

    def test_multi_letter_codes(self):
        self.assertTrue(is_ruff_line("a.py:1:1: N802 function name should be lowercase"))
        self.assertTrue(is_ruff_line("a.py:2:1: PLR0913 too many arguments"))

    def test_non_ruff_lines(self):
        for line in ("got=1.0 exp=1140.96",
                     "run rc=1 NameError: name 'x' is not defined",
                     "no python code extracted",
                     "hello world",
                     ""):
            self.assertFalse(is_ruff_line(line), line)


class TestTruncation(unittest.TestCase):
    def test_drops_column_and_message(self):
        out = truncate_lint_feedback("src/app.py:12:5: F821 undefined name 'config'")
        self.assertEqual(out, "src/app.py:12: F821")

    def test_compact_form_idempotent(self):
        out = truncate_lint_feedback("src/app.py:14: F401 'os' imported but unused")
        self.assertEqual(out, "src/app.py:14: F401")
        # already-skeleton lines stay put
        out2 = truncate_lint_feedback(out)
        self.assertEqual(out2, out)

    def test_multiline_note_mixed(self):
        note = ("src/app.py:12:5: F821 undefined name 'config'\n"
                "grader: py_stdout\n"
                "src/app.py:14: F401 'os' imported but unused")
        out = truncate_lint_feedback(note)
        lines = out.splitlines()
        self.assertEqual(lines[0], "src/app.py:12: F821")
        self.assertEqual(lines[1], "grader: py_stdout")       # untouched
        self.assertEqual(lines[2], "src/app.py:14: F401")

    def test_non_lint_note_untouched(self):
        for note in ("got=1.0 exp=1140.96",
                     "run rc=1 NameError: name 'x' is not defined",
                     "no python code extracted",
                     ""):
            self.assertEqual(truncate_lint_feedback(note), note)

    def test_drops_variable_names(self):
        # the playbook's exact point: variable names in the message must go
        out = truncate_lint_feedback(
            "app.py:9:1: F841 local variable 'unused_var' is assigned to but never used")
        self.assertEqual(out, "app.py:9: F841")
        self.assertNotIn("unused_var", out)

    def test_whitespace_leading_line(self):
        out = truncate_lint_feedback("  app.py:2:1: W292 no newline at end of file")
        self.assertEqual(out, "app.py:2: W292")


if __name__ == "__main__":
    unittest.main()
