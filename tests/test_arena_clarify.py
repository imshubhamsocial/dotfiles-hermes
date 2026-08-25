#!/usr/bin/env python3
"""tests/test_arena_clarify.py — offline tests for the real-project
clarification oracle (tests/arena_clarify.py, Benchmark-2 real tier)."""

import unittest

from tests.arena_clarify import is_clarifying_question

CLARIFY = {"keywords": ["format", "json", "csv", "serialize", "output"],
           "answer": "JSON is preferred."}


class TestClarifyDetector(unittest.TestCase):
    def test_question_with_keyword_is_detected(self):
        self.assertTrue(is_clarifying_question(
            "What format should the report use?", CLARIFY))

    def test_question_with_keyword_any_case(self):
        self.assertTrue(is_clarifying_question(
            "Should the OUTPUT be CSV or JSON?", CLARIFY))

    def test_no_question_mark_is_not_question(self):
        self.assertFalse(is_clarifying_question(
            "I will output JSON because it is parseable.", CLARIFY))

    def test_keyword_but_no_question_word(self):
        # 'format' + '?' present, but no question word before the fence — the
        # conservative guard treats a ternary-ish/odd line as NOT a question
        self.assertFalse(is_clarifying_question(
            "```python\nx = a if b else c\n```", CLARIFY))

    def test_empty_or_none_input(self):
        self.assertFalse(is_clarifying_question("", CLARIFY))
        self.assertFalse(is_clarifying_question(None, CLARIFY))

    def test_no_keywords_block_never_fires(self):
        self.assertFalse(is_clarifying_question(
            "What should I do?", {"keywords": [], "answer": "x"}))

    def test_code_first_then_question_in_prose(self):
        # prose BEFORE the fence is what the detector reads
        self.assertTrue(is_clarifying_question(
            "Which format is expected? ```python\npass\n```", CLARIFY))

    def test_answer_only_after_question_is_also_detected(self):
        self.assertTrue(is_clarifying_question(
            "Can you tell me the expected output format?", CLARIFY))


if __name__ == "__main__":
    unittest.main()
