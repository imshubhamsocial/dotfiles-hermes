"""
Contract Tests for U21: Transactional SQLite-backed DAG Task Engine
====================================================================
Tests the TaskDAG class with SQLite WAL mode, dependency resolution,
retry tracking, and git rollback coordination.
"""

from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import os

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.task_graph import (
    TaskDAG,
    TaskStatus,
    CycleDetectedError,
    create_persistent_dag,
    create_ephemeral_dag,
    create_memory_dag,
)


class TestTaskDAGLinearSequence:
    """Test 1: Linear task sequence (A → B → C) dependency resolution."""

    def test_linear_sequence_dependency_resolution(self):
        dag = create_memory_dag()
        
        # Add tasks A → B → C
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        dag.add_task("C", "Task C", "Prompt for C")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("B", "C")
        
        # Initially only A should be ready
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "A"
        
        # Complete A
        dag.mark_running("A")
        dag.mark_completed("A", "Result A")
        
        # Now B should be ready
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "B"
        
        # Complete B
        dag.mark_running("B")
        dag.mark_completed("B", "Result B")
        
        # Now C should be ready
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "C"
        
        # Complete C
        dag.mark_running("C")
        dag.mark_completed("C", "Result C")
        
        # DAG should be complete
        assert dag.is_dag_complete() is True
        
        dag.close()


class TestTaskDAGDiamondBranching:
    """Test 2: Diamond/branched DAG (A → B, A → C, [B, C] → D)."""

    def test_diamond_dag_dependency_resolution(self):
        dag = create_memory_dag()
        
        # Add tasks: A → B, A → C, B → D, C → D
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        dag.add_task("C", "Task C", "Prompt for C")
        dag.add_task("D", "Task D", "Prompt for D")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("A", "C")
        dag.add_dependency("B", "D")
        dag.add_dependency("C", "D")
        
        # Initially only A should be ready
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "A"
        
        # Complete A
        dag.mark_running("A")
        dag.mark_completed("A", "Result A")
        
        # Now B and C should be ready (parallel)
        ready = dag.get_ready_tasks()
        ready_ids = {t['id'] for t in ready}
        assert ready_ids == {"B", "C"}
        assert len(ready) == 2
        
        # Complete B
        dag.mark_running("B")
        dag.mark_completed("B", "Result B")
        
        # C still ready, D not ready yet (needs C too)
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "C"
        
        # Complete C
        dag.mark_running("C")
        dag.mark_completed("C", "Result C")
        
        # Now D should be ready
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "D"
        
        # Complete D
        dag.mark_running("D")
        dag.mark_completed("D", "Result D")
        
        assert dag.is_dag_complete() is True
        
        dag.close()


class TestTaskDAGCycleDetection:
    """Test 3: Cycle detection raising CycleDetectedError."""

    def test_cycle_detection_raises_error(self):
        dag = create_memory_dag()
        
        # Add tasks with circular dependency: A → B → A
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("B", "A")  # Creates cycle
        
        # get_topological_order should raise CycleDetectedError
        with pytest.raises(CycleDetectedError):
            dag.get_topological_order()
        
        dag.close()

    def test_self_dependency_cycle(self):
        dag = create_memory_dag()
        
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_dependency("A", "A")  # Self-cycle
        
        with pytest.raises(CycleDetectedError):
            dag.get_topological_order()
        
        dag.close()

    def test_three_node_cycle(self):
        dag = create_memory_dag()
        
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        dag.add_task("C", "Task C", "Prompt for C")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("B", "C")
        dag.add_dependency("C", "A")  # Creates 3-node cycle
        
        with pytest.raises(CycleDetectedError):
            dag.get_topological_order()
        
        dag.close()


class TestTaskDAGRetryExhaustion:
    """Test 4: Retry exhaustion (3 retries → FAILED state → has_fatal_failure())."""

    def test_retry_exhaustion_marks_failed(self):
        dag = create_memory_dag()
        
        dag.add_task("A", "Task A", "Prompt for A", max_retries=3)
        
        # Initially ready
        ready = dag.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0]['id'] == "A"
        
        # Mark running
        dag.mark_running("A")
        
        # First failure - should retry (retry_count=1 < max_retries=3)
        can_retry = dag.mark_failed("A", "Error 1")
        assert can_retry is True
        
        # Task should be PENDING again
        task = dag.get_task("A")
        assert task['status'] == TaskStatus.PENDING.value
        assert task['retry_count'] == 1
        
        # Second failure - should retry (retry_count=2 < max_retries=3)
        dag.mark_running("A")
        can_retry = dag.mark_failed("A", "Error 2")
        assert can_retry is True
        
        task = dag.get_task("A")
        assert task['status'] == TaskStatus.PENDING.value
        assert task['retry_count'] == 2
        
        # Third failure - should retry (retry_count=3 < max_retries=3 is False, 3 >= 3)
        dag.mark_running("A")
        can_retry = dag.mark_failed("A", "Error 3")
        assert can_retry is False  # Exhausted retries
        
        # Task should be FAILED
        task = dag.get_task("A")
        assert task['status'] == TaskStatus.FAILED.value
        assert task['retry_count'] == 3
        
        # has_fatal_failure should return True
        assert dag.has_fatal_failure() is True
        
        dag.close()

    def test_retry_within_limit(self):
        dag = create_memory_dag()
        
        dag.add_task("A", "Task A", "Prompt for A", max_retries=5)
        
        dag.mark_running("A")
        can_retry = dag.mark_failed("A", "Error")
        assert can_retry is True
        
        task = dag.get_task("A")
        assert task['status'] == TaskStatus.PENDING.value
        assert task['retry_count'] == 1
        assert dag.has_fatal_failure() is False
        
        dag.close()


class TestTaskDAGSnapshotRecording:
    """Test 5: Snapshot recording and DAG execution summary export."""

    def test_snapshot_recording(self):
        dag = create_memory_dag()
        
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        dag.add_dependency("A", "B")
        
        dag.mark_running("A")
        dag.mark_completed("A", "Result A")
        
        # Record snapshot
        dag.record_snapshot("A", "abc123def456")
        
        # Verify snapshot was recorded
        conn = dag._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dag_snapshots WHERE task_id = ?", ("A",))
        snapshots = cursor.fetchall()
        
        assert len(snapshots) == 1
        assert snapshots[0]['task_id'] == "A"
        assert snapshots[0]['git_commit_hash'] == "abc123def456"
        
        dag.close()

    def test_export_summary(self):
        dag = create_memory_dag()
        
        # Add 4 tasks
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        dag.add_task("C", "Task C", "Prompt for C")
        dag.add_task("D", "Task D", "Prompt for D")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("A", "C")
        dag.add_dependency("B", "D")
        dag.add_dependency("C", "D")
        
        # Initial summary
        summary = dag.export_summary()
        assert summary['total_tasks'] == 4
        assert summary['completed_tasks'] == 0
        assert summary['failed_tasks'] == 0
        assert summary['pending_tasks'] == 4
        assert summary['running_tasks'] == 0
        assert summary['progress_percentage'] == 0.0
        
        # Complete A and B
        dag.mark_running("A")
        dag.mark_completed("A", "Result A")
        
        dag.mark_running("B")
        dag.mark_completed("B", "Result B")
        
        summary = dag.export_summary()
        assert summary['total_tasks'] == 4
        assert summary['completed_tasks'] == 2
        assert summary['pending_tasks'] == 2
        assert summary['progress_percentage'] == 50.0
        
        # Fail C
        dag.mark_running("C")
        dag.mark_failed("C", "Error")  # First retry
        dag.mark_running("C")
        dag.mark_failed("C", "Error")  # Second retry
        dag.mark_running("C")
        dag.mark_failed("C", "Error")  # Third retry - exhausted
        
        summary = dag.export_summary()
        assert summary['completed_tasks'] == 2
        assert summary['failed_tasks'] == 1
        assert summary['pending_tasks'] == 1  # D is pending
        
        dag.close()


class TestTaskDAGWALPersistence:
    """Test 6: WAL-mode persistence and reconnection to existing SQLite file."""

    def test_wal_mode_persistence(self):
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create DAG and add tasks
            dag1 = TaskDAG(db_path)
            dag1.add_task("A", "Task A", "Prompt for A")
            dag1.add_task("B", "Task B", "Prompt for B")
            dag1.add_dependency("A", "B")
            dag1.mark_running("A")
            dag1.mark_completed("A", "Result A")
            dag1.record_snapshot("A", "commit_hash_1")
            dag1.close()
            
            # Reconnect to same database
            dag2 = TaskDAG(db_path)
            
            # Verify data persisted
            task_a = dag2.get_task("A")
            assert task_a is not None
            assert task_a['id'] == "A"
            assert task_a['title'] == "Task A"
            assert task_a['status'] == TaskStatus.COMPLETED.value
            assert task_a['result'] == "Result A"
            
            task_b = dag2.get_task("B")
            assert task_b is not None
            assert task_b['status'] == TaskStatus.PENDING.value
            
            # Verify edges persisted
            deps = dag2.get_dependencies("B")
            assert "A" in deps
            
            # Verify snapshots persisted
            conn = dag2._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dag_snapshots WHERE task_id = ?", ("A",))
            snapshots = cursor.fetchall()
            assert len(snapshots) == 1
            assert snapshots[0]['git_commit_hash'] == "commit_hash_1"
            
            # Continue working
            dag2.mark_running("B")
            dag2.mark_completed("B", "Result B")
            
            assert dag2.is_dag_complete() is True
            
            dag2.close()
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
            # Also cleanup WAL files
            for suffix in ['-wal', '-shm']:
                wal_path = db_path + suffix
                if os.path.exists(wal_path):
                    os.unlink(wal_path)

    def test_ephemeral_path_persistence(self):
        """Test persistence with /dev/shm path."""
        db_path = "/dev/shm/test_harness_brain.db"
        
        dag1 = TaskDAG(db_path)
        dag1.add_task("A", "Task A", "Prompt for A")
        dag1.mark_running("A")
        dag1.mark_completed("A", "Result A")
        dag1.close()
        
        # Reconnect
        dag2 = TaskDAG(db_path)
        task = dag2.get_task("A")
        assert task is not None
        assert task['status'] == TaskStatus.COMPLETED.value
        assert task['result'] == "Result A"
        dag2.close()
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        for suffix in ['-wal', '-shm']:
            wal_path = db_path + suffix
            if os.path.exists(wal_path):
                os.unlink(wal_path)


class TestTaskDAGEdgeCases:
    """Additional edge case tests."""

    def test_add_dependency_nonexistent_task_raises(self):
        dag = create_memory_dag()
        dag.add_task("A", "Task A", "Prompt for A")
        
        with pytest.raises(ValueError, match="Parent task 'B' does not exist"):
            dag.add_dependency("B", "A")
        
        with pytest.raises(ValueError, match="Child task 'C' does not exist"):
            dag.add_dependency("A", "C")
        
        dag.close()

    def test_mark_running_nonexistent_task(self):
        dag = create_memory_dag()
        # Should not raise, just no-op or handle gracefully
        dag.mark_running("nonexistent")
        dag.close()

    def test_get_topological_order_empty(self):
        dag = create_memory_dag()
        order = dag.get_topological_order()
        assert order == []
        dag.close()

    def test_get_topological_order_single_task(self):
        dag = create_memory_dag()
        dag.add_task("A", "Task A", "Prompt for A")
        order = dag.get_topological_order()
        assert order == ["A"]
        dag.close()

    def test_get_topological_order_complex(self):
        dag = create_memory_dag()
        
        # Build a more complex DAG
        # A → B, A → C, B → D, C → D, D → E
        for tid in ["A", "B", "C", "D", "E"]:
            dag.add_task(tid, f"Task {tid}", f"Prompt for {tid}")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("A", "C")
        dag.add_dependency("B", "D")
        dag.add_dependency("C", "D")
        dag.add_dependency("D", "E")
        
        order = dag.get_topological_order()
        
        # A must come first
        assert order[0] == "A"
        # E must come last
        assert order[-1] == "E"
        # B and C must come before D
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")
        # D must come before E
        assert order.index("D") < order.index("E")
        
        dag.close()

    def test_get_all_tasks(self):
        dag = create_memory_dag()
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        
        tasks = dag.get_all_tasks()
        assert len(tasks) == 2
        assert tasks[0]['id'] == "A"
        assert tasks[1]['id'] == "B"
        
        dag.close()

    def test_get_dependencies_and_dependents(self):
        dag = create_memory_dag()
        dag.add_task("A", "Task A", "Prompt for A")
        dag.add_task("B", "Task B", "Prompt for B")
        dag.add_task("C", "Task C", "Prompt for C")
        
        dag.add_dependency("A", "B")
        dag.add_dependency("A", "C")
        
        deps_b = dag.get_dependencies("B")
        assert deps_b == ["A"]
        
        deps_c = dag.get_dependencies("C")
        assert deps_c == ["A"]
        
        dependents_a = dag.get_dependents("A")
        assert set(dependents_a) == {"B", "C"}
        
        dag.close()

    def test_context_manager(self):
        with create_memory_dag() as dag:
            dag.add_task("A", "Task A", "Prompt for A")
            dag.mark_running("A")
            dag.mark_completed("A", "Result A")
        
        # Connection should be closed automatically
        # No explicit close needed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
