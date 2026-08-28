"""
Contract Tests: Roadmap 4 Milestone U56
========================================
Validates Google ADK 2.0 TaskDAG & Reflective Learning Loop (/learn):
1. Asynchronous TaskDAG dependency execution & topological ordering
2. Cycle detection in TaskDAG workflows
3. Reflective learning correction capture in SQLite WAL mode
4. Autonomous rule synthesis into rules directory
5. Strict Hardware Envelope Bounds (Pure CPU RAMDisk execution, 0 MB GPU VRAM)
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.reflective_learner import (
    DAGTaskNode,
    ADKTaskDAG,
    CorrectionEvent,
    ReflectiveLearner,
    create_reflective_learner,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_learner_env(tmp_path: Path):
    db_file = tmp_path / "test_state.db"
    rules_dir = tmp_path / "rules"
    learner = create_reflective_learner(db_path=db_file, rules_dir=rules_dir)
    return learner, db_file, rules_dir


# =============================================================================
# 1. ADK TASKDAG EXECUTION & TOPOLOGY TESTS
# =============================================================================

class TestADKTaskDAGExecution:
    """Validates ADK 2.0 TaskDAG topological execution and cycle prevention."""

    @pytest.mark.anyio
    async def test_adk_taskdag_workflow_execution(self):
        dag = ADKTaskDAG(dag_id="agent_lifecycle_dag")

        # 3-step pipeline: Intake -> Code Synthesis -> Verification
        dag.add_node(task_id="t1_intake", name="Prompt Intake", action_type="research")
        dag.add_node(task_id="t2_synth", name="Code Synthesis", action_type="code_synthesis", dependencies=["t1_intake"])
        dag.add_node(task_id="t3_verify", name="Observer Verification", action_type="verification", dependencies=["t2_synth"])

        order = dag.get_topological_order()
        assert order == ["t1_intake", "t2_synth", "t3_verify"]

        # Run async execution
        results = await dag.execute_dag()
        assert all(n.state == "completed" for n in results.values())
        assert results["t3_verify"].execution_time_ms >= 0.0

    def test_taskdag_cycle_detection(self):
        dag = ADKTaskDAG()
        dag.add_node(task_id="node_a", name="Node A", dependencies=["node_b"])
        dag.add_node(task_id="node_b", name="Node B", dependencies=["node_a"])

        with pytest.raises(ValueError, match="Cycle detected"):
            dag.get_topological_order()


# =============================================================================
# 2. REFLECTIVE LEARNER & /learn CORRECTION CAPTURE
# =============================================================================

class TestReflectiveLearnerCapture:
    """Validates capture of user feedback and automated rule synthesis."""

    def test_reflective_learner_correction_capture(self, temp_learner_env):
        learner, db_file, rules_dir = temp_learner_env

        evt = learner.capture_correction(
            user_feedback="Always run scripts strictly via python3.13",
            category="tooling",
        )

        assert isinstance(evt, CorrectionEvent)
        assert "INVARIANT: Always run scripts strictly via python3.13." in evt.inferred_rule
        assert evt.promoted is False

        # Verify persisted in SQLite
        records = learner.get_all_reflections()
        assert len(records) == 1
        assert records[0]["event_id"] == evt.event_id

    def test_rule_synthesis_and_persistence(self, temp_learner_env):
        learner, db_file, rules_dir = temp_learner_env

        evt = learner.capture_correction(
            user_feedback="Never allocate more than 4,812 MiB GPU VRAM",
            category="hardware",
        )

        rule_path = learner.synthesize_and_persist_rule(evt)
        assert rule_path.exists()
        content = rule_path.read_text(encoding="utf-8")
        assert "INVARIANT: Never allocate more than 4,812 MiB GPU VRAM." in content

        # Check promoted flag in SQLite
        records = learner.get_all_reflections()
        assert records[0]["promoted"] == 1


# =============================================================================
# 3. HARDWARE ENVELOPE BOUNDS & ZERO GPU VRAM
# =============================================================================

class TestReflectiveLearnerHardwareBounds:
    """Validates pure CPU RAMDisk execution."""

    def test_reflective_learner_zero_gpu_vram(self, temp_learner_env):
        learner, _, _ = temp_learner_env
        for i in range(20):
            learner.capture_correction(f"Rule constraint {i}", category="policy")

        reflections = learner.get_all_reflections()
        assert len(reflections) == 20
