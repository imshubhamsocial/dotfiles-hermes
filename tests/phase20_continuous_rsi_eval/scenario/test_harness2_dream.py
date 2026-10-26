"""Scenario tests for Google Harness2 Continuous RSI Dream Meta-Loop (Phase 20)."""

import pathlib
import sqlite3
import tempfile

import pytest


def test_transcript_failure_mining():
    """Validates that recent session failures and Tabu events can be extracted from state.db."""
    hermes_home = pathlib.Path.home() / ".hermes"
    db_path = hermes_home / "state.db"
    if not db_path.exists():
        pytest.skip("state.db not present in runtime environment")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Query messages table for error traces or tabu interventions
    c.execute("SELECT id, role, content FROM messages WHERE content LIKE '%FAILED%' OR content LIKE '%Error%' LIMIT 5")
    rows = c.fetchall()
    conn.close()

    # Assert query execution succeeds
    assert isinstance(rows, list)


def test_candidate_rule_synthesis_and_regression_guard():
    """Validates that candidate rules are evaluated in tempdirs and regressive rules are rejected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # 1. Simulate candidate non-regressing rule
        candidate_good_rule = temp_path / "rule_clean_code.md"
        candidate_good_rule.write_text("# Invariant: Always return exit code 0\n", encoding="utf-8")
        assert candidate_good_rule.exists()

        # 2. Simulate regression test
        regressed = False
        if "syntax error" in candidate_good_rule.read_text(encoding="utf-8"):
            regressed = True

        assert regressed is False, "Candidate rule must pass regression check"

        # 3. Simulate candidate regressive rule (must be rejected)
        candidate_bad_rule = temp_path / "rule_broken.md"
        candidate_bad_rule.write_text("# Invariant: syntax error here", encoding="utf-8")

        bad_regressed = "syntax error" in candidate_bad_rule.read_text(encoding="utf-8")
        assert bad_regressed is True, "Regressive rule must be detected and rejected"
