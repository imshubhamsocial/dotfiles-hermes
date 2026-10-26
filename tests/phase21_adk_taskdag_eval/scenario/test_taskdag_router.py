"""Unit tests for TaskDAGRouter and A2A Federation (Phase 21)."""

import pathlib
import sys

import pytest

scenario_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(scenario_dir))

from taskdag_router import (
    CycleDetectedException,
    PersonaPrivilegeViolationError,
    PersonaRole,
    TaskDAGRouter,
    TaskNode,
)


def test_topological_schedule_diamond_dag():
    """Asserts that diamond DAG topologies are scheduled correctly."""
    router = TaskDAGRouter()
    # Diamond graph:
    #      A (@architect)
    #     / \
    #    B   C (@coder_1, @coder_2)
    #     \ /
    #      D (@tester)
    node_a = TaskNode(node_id="plan_spec", persona=PersonaRole.ARCHITECT.value, action="inspect_symbols")
    node_b = TaskNode(node_id="patch_auth", persona=PersonaRole.CODER.value, action="apply_patch", dependencies=["plan_spec"])
    node_c = TaskNode(node_id="patch_db", persona=PersonaRole.CODER.value, action="edit_file", dependencies=["plan_spec"])
    node_d = TaskNode(node_id="verify_all", persona=PersonaRole.TESTER.value, action="run_pytest", dependencies=["patch_auth", "patch_db"])

    for n in [node_d, node_c, node_b, node_a]:
        router.add_node(n)

    schedule = router.topological_schedule()

    assert schedule[0] == "plan_spec"
    assert schedule[-1] == "verify_all"
    assert set(schedule[1:3]) == {"patch_auth", "patch_db"}


def test_cycle_detection_in_taskdag():
    """Asserts that circular dependencies are trapped and raise CycleDetectedException."""
    router = TaskDAGRouter()
    # Cycle: A -> B -> C -> A
    node_a = TaskNode(node_id="A", persona=PersonaRole.ARCHITECT.value, action="read_file", dependencies=["C"])
    node_b = TaskNode(node_id="B", persona=PersonaRole.CODER.value, action="apply_patch", dependencies=["A"])
    node_c = TaskNode(node_id="C", persona=PersonaRole.TESTER.value, action="run_pytest", dependencies=["B"])

    for n in [node_a, node_b, node_c]:
        router.add_node(n)

    with pytest.raises(CycleDetectedException) as exc_info:
        router.topological_schedule()

    assert "Cycle detected" in str(exc_info.value)


def test_persona_sandboxing_privilege_enforcement():
    """Asserts that unauthorized actions trigger PersonaPrivilegeViolationError."""
    router = TaskDAGRouter()
    
    # Architect attempting code edit
    with pytest.raises(PersonaPrivilegeViolationError):
        router.validate_persona_action(PersonaRole.ARCHITECT.value, "apply_patch")
    
    # Coder attempting test runner
    with pytest.raises(PersonaPrivilegeViolationError):
        router.validate_persona_action(PersonaRole.CODER.value, "run_pytest")

    # Tester attempting code surgery
    with pytest.raises(PersonaPrivilegeViolationError):
        router.validate_persona_action(PersonaRole.TESTER.value, "surgical_replace")

    # Critic attempting file edit
    with pytest.raises(PersonaPrivilegeViolationError):
        router.validate_persona_action(PersonaRole.CRITIC.value, "edit_file")

    assert router.metrics["persona_privilege_violations"] == 4


def test_zero_context_pollution_a2a_transfer():
    """Asserts that raw terminal dumps are pruned, maintaining 0 context pollution tokens."""
    router = TaskDAGRouter()

    raw_payload = {
        "status": "success",
        "raw_terminal_output": "FATAL: Traceback (most recent call last):\n" * 100,
        "stdout_dump": "DEBUG: " * 500,
        "clean_diff": "+ def authenticate(): return True",
    }

    # With sanitization enabled (standard A2A protocol)
    event = router.transfer_to_agent(
        sender=PersonaRole.ARCHITECT.value,
        recipient=PersonaRole.CODER.value,
        task_id="step_1",
        payload=raw_payload,
        sanitize_logs=True,
    )

    assert event.params["raw_logs_pruned"] is True
    assert "raw_terminal_output" not in event.params["structured_payload"]
    assert "stdout_dump" not in event.params["structured_payload"]
    assert event.params["structured_payload"]["clean_diff"] == "+ def authenticate(): return True"
    assert router.metrics["context_pollution_tokens"] == 0


def test_end_to_end_dag_execution():
    """Asserts complete 4-persona TaskDAG execution pipeline."""
    router = TaskDAGRouter()

    node_1 = TaskNode(node_id="spec", persona=PersonaRole.ARCHITECT.value, action="ast_grep_outline")
    node_2 = TaskNode(node_id="impl", persona=PersonaRole.CODER.value, action="surgical_replace", dependencies=["spec"])
    node_3 = TaskNode(node_id="test", persona=PersonaRole.TESTER.value, action="run_pytest", dependencies=["impl"])
    node_4 = TaskNode(node_id="score", persona=PersonaRole.CRITIC.value, action="evaluate_trajectory", dependencies=["test"])

    for n in [node_4, node_2, node_3, node_1]:
        router.add_node(n)

    result = router.execute_dag()

    assert result["completion_rate"] == 1.0
    assert result["executed_count"] == 4
    assert router.metrics["persona_privilege_violations"] == 0
    assert router.metrics["context_pollution_tokens"] == 0
    assert router.metrics["cuda_vram_delta_mib"] == 0
    assert router.metrics["dag_completion_rate"] == 1.0
