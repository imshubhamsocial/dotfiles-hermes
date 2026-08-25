#!/usr/bin/env python3
"""
Tier-2 canary-sequence leak detector (round-2 playbook §"Canary sequence"
/ "Leakage and Hygiene Protocols") — Session 11 follow-up 6.

The playbook's ultimate defense against blind string copying: a highly
specific UUID is injected as a hidden comment inside the few-shot exemplar
prompt; the deterministic grader regex-searches the agent's final output for
that exact UUID. If it appears, the agent is copying the exemplar's STRING
SPACE instead of generating novel code — the attempt is failed with
CANARY_LEAK.

Why it works: exemplars are OUTPUT-FORMAT demos, so a model that reproduces
them verbatim carries the hidden comment into its answer. A model that writes
its own code never emits the UUID.

What this module provides (all pure / stdlib-only, matching the Tier-2
grader contract):
  - new_canary()        — a fresh per-run canary UUID string.
  - inject_canary()     — append the hidden comment to an exemplar body
                          (python/bash get a '#' comment; text/json are NOT
                          canaried — a comment would pollute the format demo).
  - scan_output()       — regex search for the exact canary in raw output.
  - grade_task gate     — tests/arena_runner.grade_task fails any task whose
                          grader carries `"canary": <uuid>` when the uuid is
                          found in the output (opt-in per task).
The live driver is prototypes/tests/probe_canary_live.py (full adaptive-loop
run with canaried exemplars + leak report); offline tests here + in
tests/test_canary.py.

Run: python3 tests/test_canary.py
"""

from __future__ import annotations

import re
import uuid

# Languages whose exemplars are canaried: '#' is a comment in both.
CANARYABLE_LANGS = ("python", "bash")

_CANARY_PREFIX = "CANARY"


def new_canary(prefix: str = _CANARY_PREFIX) -> str:
    """A fresh canary token, e.g. 'CANARY-3f2a9c1e...' (uuid4 hex)."""
    return f"{prefix}-{uuid.uuid4().hex}"


def inject_canary(exemplar: str, lang: str, canary: str | None = None):
    """Append the hidden canary comment to an exemplar body.

    Returns (canaried_text, canary). For python/bash the hidden comment is a
    '# CANARY-<uuid>' line; for other languages the text is returned UNCHANGED
    with a fresh canary token (callers may skip those — see the driver).
    """
    canary = canary or new_canary()
    if lang not in CANARYABLE_LANGS:
        return exemplar, canary
    return f"{exemplar.rstrip()}\n# {canary}", canary


def scan_output(output: str, canary: str) -> bool:
    """True when the exact canary token appears in the raw model output
    (the playbook's 'simple regular expression search')."""
    if not canary:
        return False
    return re.search(re.escape(canary), str(output or "")) is not None


def canary_leak_note(canary: str) -> str:
    """The deterministic note produced when a leak is detected (grader
    contract: the adaptive loop feeds it back and classifies it)."""
    return (f"CANARY_LEAK {canary} — output reproduces the exemplar string "
            f"space verbatim (blind copy), not novel code")


if __name__ == "__main__":
    import sys
    # quick self-check (the real tests live in tests/test_canary.py)
    c = new_canary()
    body, _ = inject_canary("def greet(name):\n    return name", "python", c)
    assert scan_output(body, c), "injected canary must be found in its body"
    assert not scan_output("def greet(name):\n    return name", c), \
        "novel code must not contain the canary"
    print(f"canary.py OK — self-check passed ({c[:20]}...)")
    sys.exit(0)
