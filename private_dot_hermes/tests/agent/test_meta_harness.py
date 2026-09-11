"""
Contract Tests: Meta-Harness Outer-Loop Autonomous Self-Evolution Engine
=======================================================================
Validates:
  1. TraceFailureAnalyzer error clustering (SYNTAX_ERROR, SEARCH_REPLACE_MISMATCH, TEST_REGRESSION).
  2. HarnessProposalEngine proposal formulation and target plugin mapping.
  3. SpecVerificationGate dry-run mutation diff calculation.
  4. SpecVerificationGate automatic rollback on test regression.
  5. SpecVerificationGate successful mutation commit when tests pass.
"""

from pathlib import Path
import pytest

from plugins.self_evolution.meta_harness import (
    TraceFailureAnalyzer,
    HarnessProposalEngine,
    SpecVerificationGate,
)


class TestMetaHarness:
    def test_trace_failure_clustering(self):
        sample_traces = [
            {"windowed_output": "SyntaxError: unexpected EOF while parsing", "test_status": "FAIL", "exit_code": 1},
            {"windowed_output": "Ambiguous match: search block found 3 times", "test_status": "FAIL", "exit_code": 1},
            {"windowed_output": "SyntaxError: invalid syntax", "test_status": "FAIL", "exit_code": 1},
            {"windowed_output": "AssertionError: expected 42 got 0", "test_status": "FAIL", "exit_code": 1},
        ]
        clusters = TraceFailureAnalyzer.analyze_traces(sample_traces)
        assert len(clusters) >= 3

        cluster_map = {c["cluster_id"]: c["count"] for c in clusters}
        assert cluster_map.get("SYNTAX_ERROR") == 2
        assert cluster_map.get("SEARCH_REPLACE_MISMATCH") == 1
        assert cluster_map.get("TEST_REGRESSION") == 1

    def test_harness_proposal_engine(self):
        cluster = {
            "cluster_id": "SYNTAX_ERROR",
            "target_plugin": "mcp_tools",
            "remedy": "Enforce AST preflight check before script execution",
        }
        proposal = HarnessProposalEngine.generate_proposal(cluster)
        assert proposal["proposal_id"].startswith("PROP-")
        assert proposal["cluster_id"] == "SYNTAX_ERROR"
        assert proposal["target_plugin"] == "mcp_tools"
        assert proposal["status"] == "PROPOSED"
        assert "AST preflight" in proposal["description"]

    def test_spec_verification_gate_dry_run(self, tmp_path: Path):
        test_file = tmp_path / "helper.py"
        test_file.write_text("def run():\n    return False\n")

        res = SpecVerificationGate.apply_mutation_safely(
            target_file=test_file,
            search_block="    return False",
            replace_block="    return True",
            dry_run=True,
        )
        assert res["success"] is True
        assert res["status"] == "DRY_RUN_PASS"
        assert "+    return True" in res["diff"]
        # In dry run, file must NOT be modified
        assert "return False" in test_file.read_text()

    def test_spec_verification_gate_rollback_on_regression(self, tmp_path: Path, monkeypatch):
        test_file = tmp_path / "helper.py"
        test_file.write_text("def run():\n    return 'original'\n")

        # Mock run_tests to simulate a test regression
        monkeypatch.setattr(
            SpecVerificationGate,
            "run_tests",
            staticmethod(lambda target=None: (False, "FAILED test_something.py: regression detected")),
        )

        res = SpecVerificationGate.apply_mutation_safely(
            target_file=test_file,
            search_block="    return 'original'",
            replace_block="    return 'broken_mutation'",
            dry_run=False,
        )
        assert res["success"] is False
        assert res["status"] == "ROLLED_BACK"
        assert "Regression detected" in res["message"]
        # Original content must be fully restored by rollback
        assert "return 'original'" in test_file.read_text()
        assert not test_file.with_suffix(".py.bak").exists()

    def test_spec_verification_gate_commit_on_success(self, tmp_path: Path, monkeypatch):
        test_file = tmp_path / "helper.py"
        test_file.write_text("VALUE = 1\n")

        # Mock run_tests to simulate 100% green test pass
        monkeypatch.setattr(
            SpecVerificationGate,
            "run_tests",
            staticmethod(lambda target=None: (True, "225 passed in 5.2s")),
        )

        res = SpecVerificationGate.apply_mutation_safely(
            target_file=test_file,
            search_block="VALUE = 1",
            replace_block="VALUE = 2",
            dry_run=False,
        )
        assert res["success"] is True
        assert res["status"] == "COMMITTED"
        assert "Zero-regression gate passed" in res["message"]
        # Modified content must be committed
        assert "VALUE = 2" in test_file.read_text()
        assert not test_file.with_suffix(".py.bak").exists()
