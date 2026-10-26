"""Verification test suite for Phase 21 metrics and gate criteria."""

import json
import pathlib
import sys

import pytest

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from taskdag_router import (
    PersonaRole,
    TaskDAGRouter,
    TaskNode,
)


def test_adk_taskdag_metrics():
    """Asserts that benchmark metrics meet all Phase 21 criteria."""
    report_file = testbed_root / "adk_taskdag_metrics.json"
    assert report_file.exists(), "adk_taskdag_metrics.json must be generated prior to verification"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report.get("cuda_vram_delta_mib") == 0, "Must execute with 0 MiB CUDA VRAM delta"
    assert report.get("context_pollution_tokens") == 0, "Context pollution tokens must be strictly 0"
    assert report.get("persona_privilege_violations") == 0, "Persona privilege violations must be 0"
    assert report.get("dag_completion_rate") == 1.0, "DAG completion rate must be 1.0 (100%)"


def test_live_a2a_router_federation():
    """Directly verifies live federation across all 4 sandboxed personas."""
    router = TaskDAGRouter()

    node_arch = TaskNode(node_id="arch", persona=PersonaRole.ARCHITECT.value, action="read_file")
    node_code = TaskNode(node_id="code", persona=PersonaRole.CODER.value, action="apply_patch", dependencies=["arch"])
    node_test = TaskNode(node_id="test", persona=PersonaRole.TESTER.value, action="run_pytest", dependencies=["code"])
    node_crit = TaskNode(node_id="crit", persona=PersonaRole.CRITIC.value, action="compute_reward", dependencies=["test"])

    for n in [node_crit, node_test, node_code, node_arch]:
        router.add_node(n)

    result = router.execute_dag()

    assert result["completion_rate"] == 1.0
    assert len(router.events) == 3
    for ev in router.events:
        assert ev.method == "transfer_to_agent"
        assert ev.params["raw_logs_pruned"] is True
