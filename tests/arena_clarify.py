#!/usr/bin/env python3
"""tests/arena_clarify.py — clarification-oracle detector (Benchmark-2 real
project tier, 2026-08-09).

The real-project corpus deliberately marks 1-2 steps per project as
UNDERSPECIFIED (e.g. "the serialization format is intentionally open"). A
harness that recognizes the ambiguity and ASKS is demonstrating real
engineering behavior; one that silently guesses may pick the wrong format.

Deterministic (no LLM judge): `is_clarifying_question(raw, clarify)` returns
True when the model output (a) contains a question mark AND (b) mentions at
least one keyword from the grader's clarify block (format/json/csv/output/…).
The note returned by grade_task then carries the ORACLE answer into the next
adaptive attempt. Pure + unit-testable.
"""

from __future__ import annotations

import re

_QUESTION_WORDS = {
    "what", "which", "how", "should", "does", "do", "is", "are", "can",
    "could", "would", "format", "serialize", "expect", "prefer", "use",
    "want", "mean", "output",
}


def is_clarifying_question(raw_output: str, clarify: dict) -> bool:
    """True when `raw_output` is a question about the underspecified
    requirement (a '?' plus at least one keyword and a question word).

    Conservative by design: a model that answers directly (even mentioning a
    format keyword) without a '?' is NOT a question — it is graded by the
    type grader normally, so asking can never be gamed into skipping the
    actual work.
    """
    if not raw_output or not isinstance(raw_output, str):
        return False
    text = raw_output.strip()
    if "?" not in text:
        return False
    low = text.lower()
    keywords = [k.lower() for k in (clarify or {}).get("keywords", []) if k]
    if not keywords:
        return False
    # must mention at least one oracle keyword (e.g. 'format', 'json', 'csv')
    if not any(k in low for k in keywords):
        return False
    # a code answer rarely contains '?' — but guard against a ternary/code
    # block by requiring a question word in the prose before the first fence
    prose = text.split("```")[0]
    if not prose.strip():
        return False
    words = set(re.findall(r"[a-z]+", prose.lower()))
    return bool(words & _QUESTION_WORDS)
