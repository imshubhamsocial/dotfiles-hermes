#!/usr/bin/env python3
"""
Tier-2 truncated ruff-feedback engine (round-2 playbook §"Leakage and
Hygiene Protocols" — "The threat of ruff-overfitting... The truncated
feedback mechanism must become the default operational standard to force
genuine algorithmic repair") — Session 11 follow-up 6.

The concern: when the EXACT verbose linter error string is fed back in the
adaptive loop, models can learn to appease the linter by blindly stripping
variables or suppressing warnings — string-matching the message instead of
understanding the underlying defect.

The playbook's A/B + default: one arm receives the exact verbose linter
error; the other receives a HEAVILY TRUNCATED error that isolates only
  - the filename,
  - the line number,
  - the specific error code,
brutally stripping the verbose description and the variable names. If the
model can resolve the error from filename+line+code alone, it demonstrates
genuine structural understanding; if it needs the verbose text, it is merely
matching strings.

What this module provides (pure, stdlib-only):
  - truncate_lint_feedback(note) — rewrite each ruff-style line to
    'file.py:LINE: CODE' (dropping the column + message + variable names);
    any line that is NOT a ruff-style linter line is passed through UNCHANGED
    (a non-lint grader note like 'got=1.0 exp=1140.96' must never be
    mangled).
  - is_ruff_line(line)         — ruff-format detector for tests/audit.
The live A/B driver is prototypes/tests/probe_feedback_ab_live.py
(arm A = verbose notes, arm B = truncated notes, full adaptive loop);
offline tests here + in tests/test_feedback_truncation.py.

Run: python3 tests/test_feedback_truncation.py
"""

from __future__ import annotations

import re

# ruff compact format:  file.py:LINE:COL: CODE message        (default)
#                        file.py:LINE: CODE message           (compact)
# Codes are letters+digits with 1-3 letter prefixes, e.g. E501 / F401 /
# F821 / I001 / N802 / PLR0913 / UP009.
_RUFF_LINE = re.compile(
    r"^(?P<file>\S+\.py):(?P<line>\d+)(?::(?P<col>\d+))?:\s*"
    r"(?P<code>[A-Z]{1,3}[0-9]{2,4})(?:\s|$)"
)


def is_ruff_line(line: str) -> bool:
    """True when `line` looks like a ruff/pyflakes linter diagnostic
    ('path.py:LINE:COL: CODE message'). Pure."""
    return _RUFF_LINE.match(line.strip()) is not None


def truncate_lint_feedback(note: str) -> str:
    """Rewrite every ruff-style line in `note` to its skeleton —
    'file.py:LINE: CODE' with the column, verbose description, and variable
    names dropped. All non-lint lines pass through UNCHANGED (safety: a
    grader note that is not a linter diagnostic must not be altered).

    Lines already in skeleton form are idempotent. Pure.
    """
    if not note:
        return note
    out = []
    for line in str(note).splitlines():
        m = _RUFF_LINE.match(line.strip())
        if m:
            out.append(f"{m.group('file')}:{m.group('line')}: "
                       f"{m.group('code')}")
        else:
            out.append(line)
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    # quick self-check (the real tests live in tests/test_feedback_truncation.py)
    sample = ("src/app.py:12:5: F821 undefined name 'config'\n"
              "src/app.py:14: F401 'os' imported but unused")
    print(truncate_lint_feedback(sample))
    sys.exit(0)
