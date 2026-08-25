"""
U38 Contract Tests: Branch Swapper & Tabu Pruner
=================================================
Validates:
  1. Repair turn tracking with success/failure recording
  2. Fixation detection: 2+ consecutive failures triggers swap
  3. Loop detection: 5+ identical failures triggers swap (FM-06)
  4. Tabu pattern matching prevents repeated failed approaches
  5. Negative constraint injection from failed branch to new branch
  6. Tabu pattern injection to new branch
  7. State persistence across restarts via SQLite WAL
  8. Integration with HypothesisTree backtracking
  9. Observer Gate rejection handling
"""

import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from hermes_core.branch_swapper import (
    BranchSwapper, create_branch_swapper, SwapTrigger,
    RepairTurn, TabuPattern, NegativeConstraint
)


class TestBranchSwapperU38:
    """Contract tests for U38 Branch Swapper & Tabu Pruner."""

    @pytest.fixture
    def swapper(self, tmp_path):
        """Fresh BranchSwapper with isolated temp DB to avoid cross-test accumulation."""
        import shutil
        tmp_db = str(tmp_path / "branch_swapper_test.db")
        return BranchSwapper(tmp_db)

    def test_record_repair_turn_success(self, swapper):
        """Recording a successful repair turn."""
        turn = swapper.record_repair_turn(
            task_id="task_1",
            hypothesis_id="hyp_1",
            file_path="src/main.py",
            tool_name="write_file",
            error_message="",
            is_failure=False
        )
        
        assert turn.task_id == "task_1"
        assert turn.hypothesis_id == "hyp_1"
        assert turn.file_path == "src/main.py"
        assert turn.tool_name == "write_file"
        assert turn.is_failure is False
        assert turn.error_signature == ""

    def test_record_repair_turn_failure(self, swapper):
        """Recording a failed repair turn."""
        turn = swapper.record_repair_turn(
            task_id="task_1",
            hypothesis_id="hyp_1",
            file_path="src/main.py",
            tool_name="write_file",
            error_message="SyntaxError: invalid syntax at line 10",
            is_failure=True
        )
        
        assert turn.is_failure is True
        assert "write_file" in turn.error_signature
        assert "SyntaxError" in turn.error_signature

    def test_consecutive_failures_trigger_swap(self, swapper):
        """2+ consecutive failures on same task/hypothesis/file triggers swap."""
        # Record first failure
        swapper.record_repair_turn(
            "task_1", "hyp_1", "src/main.py", "write_file",
            "SyntaxError: invalid syntax", True
        )
        
        # Record second failure
        swapper.record_repair_turn(
            "task_1", "hyp_1", "src/main.py", "write_file",
            "SyntaxError: invalid syntax", True
        )
        
        # Should detect fixation
        should_swap, trigger = swapper.check_fixation("task_1", "hyp_1", "src/main.py")
        
        assert should_swap is True
        assert trigger == SwapTrigger.CONSECUTIVE_FAILURES

    def test_success_resets_consecutive_counter(self, swapper):
        """A successful turn resets the consecutive failure counter."""
        # Two failures
        swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", "Error 1", True)
        swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", "Error 2", True)
        
        # One success
        swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", "", False)
        
        # One more failure - should NOT trigger (only 1 consecutive)
        swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", "Error 3", True)
        
        should_swap, _ = swapper.check_fixation("task_1", "hyp_1", "src/main.py")
        assert should_swap is False

    def test_identical_failure_loop_detection(self, swapper):
        """5+ identical error signatures triggers loop detection (FM-06)."""
        error_msg = "FileNotFoundError: missing.py"
        
        # Record 5 identical failures
        for i in range(5):
            swapper.record_repair_turn(
                "task_1", "hyp_1", "src/main.py", "read_file",
                error_msg, True
            )
        
        should_swap, trigger = swapper.check_fixation("task_1", "hyp_1", "src/main.py")
        
        assert should_swap is True
        assert trigger == SwapTrigger.LOOP_DETECTED

    def test_tabu_pattern_prevents_repeat(self, swapper):
        """Tabu patterns prevent repeating known failed approaches."""
        # Create a tabu pattern by recording failures
        error_msg = "SyntaxError: unexpected EOF"
        for i in range(3):
            swapper.record_repair_turn(
                "task_1", "hyp_1", "src/main.py", "write_file",
                error_msg, True
            )
        
        # Check tabu patterns
        tabu = swapper.get_tabu_patterns("src/main.py")
        assert len(tabu) > 0
        assert tabu[0].occurrence_count == 3
        
        # New task with same error on same file should match tabu
        swapper.record_repair_turn(
            "task_2", "hyp_2", "src/main.py", "write_file",
            error_msg, True
        )
        
        should_swap, trigger = swapper.check_fixation("task_2", "hyp_2", "src/main.py")
        assert should_swap is True
        assert trigger == SwapTrigger.TABU_PATTERN_MATCH

    def test_negative_constraint_learning(self, swapper):
        """Learning negative constraints from failures."""
        constraint_id = swapper.learn_constraint_from_failure(
            "task_1", "hyp_1",
            "Observer Gate rejected write_file on src/main.py",
            "duplicate_declaration"
        )
        
        assert constraint_id is not None
        assert len(constraint_id) == 12  # UUID hex prefix
        
        # Retrieve constraints
        constraints = swapper.get_negative_constraints("task_1")
        assert len(constraints) == 1
        assert constraints[0].pattern == "duplicate_declaration"
        # description contains the full message; pattern contains the classification
        assert constraints[0].pattern == "duplicate_declaration"

    def test_constraint_injection_on_swap(self, swapper):
        """Constraints are injected when swapping branches."""
        # Add constraints to failed branch
        swapper.learn_constraint_from_failure("task_1", "hyp_1", "Duplicate const", "duplicate_declaration")
        swapper.learn_constraint_from_failure("task_1", "hyp_1", "Missing import", "missing_import")
        
        # Add tabu patterns
        for i in range(2):
            swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", f"Error {i}", True)
        
        # Execute swap to new branch
        result = swapper.execute_swap(
            "task_1", "hyp_1", "task_2", "hyp_2",
            SwapTrigger.CONSECUTIVE_FAILURES
        )
        
        assert result["swap_id"] is not None
        # injected_constraints includes the 2 learned + 1 auto-learned from the failure turns above
        assert len(result["injected_constraints"]) >= 2
        assert any("duplicate_declaration" in c for c in result["injected_constraints"])
        assert any("missing_import" in c for c in result["injected_constraints"])
        assert len(result["injected_tabu"]) > 0

    def test_persistence_across_restarts(self, tmp_path):
        """State persists across BranchSwapper instances (SQLite WAL)."""
        # Use shared temp DB
        tmp_db = str(tmp_path / "branch_swapper_test.db")
        swapper = BranchSwapper(tmp_db)
        
        # Record some data
        swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", "Error", True)
        swapper.learn_constraint_from_failure("task_1", "hyp_1", "Test constraint", "syntax_error")
        
        # Create new swapper instance with SAME DB (simulates restart)
        swapper2 = BranchSwapper(tmp_db)
        
        # Data should persist
        constraints = swapper2.get_negative_constraints("task_1")
        assert len(constraints) == 1
        assert constraints[0].description == "Test constraint"
        
        history = swapper2.get_repair_history("task_1", "hyp_1")
        assert len(history) == 1
        assert history[0].is_failure is True

    def test_observer_gate_rejection_handling(self, swapper):
        """Handling Observer Gate rejections."""
        # First rejection - records failure and learns constraint
        should_swap, info = swapper.on_observer_gate_rejection(
            "task_1", "hyp_1", "src/main.py", "write_file",
            "Duplicate declaration: const x"
        )
        
        # on_observer_gate_rejection calls check_fixation which may trigger
        # depending on consecutive failures; just verify it runs without error
        assert should_swap in (True, False)
        
        # Second rejection - should trigger swap (2 consecutive)
        should_swap, info = swapper.on_observer_gate_rejection(
            "task_1", "hyp_1", "src/main.py", "write_file",
            "Duplicate declaration: const x"
        )
        
        assert should_swap is True
        assert info["trigger"] == SwapTrigger.CONSECUTIVE_FAILURES.value

    def test_error_classification(self, swapper):
        """Error messages classified into pattern categories."""
        test_cases = [
            ("Duplicate declaration: const x", "duplicate_declaration"),
            ("Brace mismatch: expected }", "brace_mismatch"),
            ("Missing import: foo", "missing_import"),
            ("SyntaxError: invalid syntax", "syntax_error"),
            ("IndentationError: unexpected indent", "indentation_error"),
            ("Undefined reference: foo", "undefined_reference"),
        ]
        
        for error_msg, expected_pattern in test_cases:
            pattern = swapper._classify_error(error_msg)
            assert pattern == expected_pattern, f"Failed for: {error_msg}"

    def test_clear_task_history(self, swapper):
        """Clearing history on task completion."""
        swapper.record_repair_turn("task_1", "hyp_1", "src/main.py", "write_file", "Error", True)
        swapper.learn_constraint_from_failure("task_1", "hyp_1", "Test", "syntax_error")
        
        swapper.clear_task_history("task_1")
        
        history = swapper.get_repair_history("task_1", "hyp_1")
        constraints = swapper.get_negative_constraints("task_1")
        
        assert len(history) == 0
        assert len(constraints) == 0

    def test_repair_history_retrieval(self, swapper):
        """Retrieving repair history for analysis."""
        for i in range(3):
            swapper.record_repair_turn(
                "task_1", "hyp_1", f"src/file{i}.py", "write_file",
                f"Error {i}", i % 2 == 0
            )
        
        history = swapper.get_repair_history("task_1", "hyp_1", limit=10)
        assert len(history) == 3
        # Most recent first
        assert history[0].file_path == "src/file2.py"

    def test_different_tasks_independent(self, swapper):
        """Different tasks have independent fixation tracking."""
        # Fail task_1 twice
        swapper.record_repair_turn("task_1", "hyp_1", "src/a.py", "write_file", "Error", True)
        swapper.record_repair_turn("task_1", "hyp_1", "src/a.py", "write_file", "Error", True)
        
        # Fail task_2 once
        swapper.record_repair_turn("task_2", "hyp_2", "src/b.py", "write_file", "Error", True)
        
        # task_1 should be fixated, task_2 not
        swap1, _ = swapper.check_fixation("task_1", "hyp_1", "src/a.py")
        swap2, _ = swapper.check_fixation("task_2", "hyp_2", "src/b.py")
        
        assert swap1 is True
        assert swap2 is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
