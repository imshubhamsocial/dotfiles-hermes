#!/usr/bin/env python3
"""
Verification Script for Phase 0: Faraday Director Mode (Research Direction Assessment)
========================================================================================
Executes in-process contract verification against:
  1. Multi-Domain Intent Classification (Systems, Data, Algorithmic, Web, Ops, AI)
  2. The 4 Faraday Director Invariants (What to Build, What to Skip, What to Validate First, Experiment Sequence)
  3. Pre-Flight Falsification Probing (Sub-second runtime viability validation & fatal condition halt)
  4. Candidate Task Decomposition & YAGNI Exclusion
  5. End-to-End Closed-Loop Pipeline Bridge: Phase 0 (Faraday) -> Phase 1 (MRP) -> Phase 2 (Loop) -> Phase 3 (Contract Gate)
"""

import os
import sys
import tempfile
from pathlib import Path

# Resolve hermes-agent path dynamically
_hermes_dir = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parents[1]))
for p in [
    _hermes_dir / "hermes-agent",
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.faraday_director import (
    FaradayDirector,
    GoalDomain,
)
from agent.core.mrp_planner import MRPPlan, TaskState
from agent.core.loop_orchestrator import LoopOrchestrator, LoopTerminationReason
from agent.core.contract_gate import NativeContractGate


def verify_domain_classification() -> None:
    print("[1/5] Verifying multi-domain classification heuristics...")

    director = FaradayDirector()

    assert director.classify_domain("Build a bwrap sandbox jail for daemon processes") == GoalDomain.SYSTEMS_PROGRAMMING
    assert director.classify_domain("Ingest semantic triples into persistent sqlite database") == GoalDomain.DATA_ENGINEERING
    assert director.classify_domain("Verify symbolic equation derivation and bounds with sympy") == GoalDomain.SCIENTIFIC_ALGORITHMIC
    assert director.classify_domain("Click button and automate headless web browser via cua") == GoalDomain.WEB_BROWSER_AUTOMATION
    assert director.classify_domain("Evolve moba router rules and prompt harness for agent") == GoalDomain.AI_HARNESS_EVOLUTION
    assert director.classify_domain("Format text document into tabular markdown") == GoalDomain.GENERAL_TASK

    print("  ✓ All operational domains classified accurately.")


def verify_faraday_invariants_formulation() -> None:
    print("[2/5] Verifying the 4 Faraday Director Invariants formulation...")

    director = FaradayDirector()

    assessment = director.assess_goal(
        goal="Design persistent SQLite relational graph for semantic triples",
        existing_symbols=["sqlite3", "pathlib"],
        installed_packages=["sqlite3", "rich"],
    )

    assert assessment.assessment_id.startswith("faraday-")
    assert assessment.domain == GoalDomain.DATA_ENGINEERING

    # 1. WHAT TO BUILD
    assert len(assessment.what_to_build) >= 2
    assert any("sqlite" in b.lower() for b in assessment.what_to_build)

    # 2. WHAT TO SKIP
    assert len(assessment.what_to_skip) >= 2
    assert any("orm" in s.lower() or "distributed" in s.lower() for s in assessment.what_to_skip)

    # 3. WHAT TO VALIDATE FIRST
    assert "sqlite" in assessment.what_to_validate_first.lower()

    # 4. EXPERIMENT SEQUENCE
    assert len(assessment.experiment_sequence) == 3
    assert assessment.cheapest_falsification_probe["type"] == "command"
    assert "sqlite3" in assessment.cheapest_falsification_probe["command"]

    # Markdown rendering
    md = assessment.to_markdown()
    assert "Phase 0: Faraday Director Assessment" in md
    assert "What to Build" in md
    assert "What to Skip" in md
    assert "What to Validate First" in md

    print(f"  ✓ Faraday assessment synthesized ({assessment.duration_ms:.1f}ms): 4 invariants formulated.")


def verify_preflight_falsification_probes() -> None:
    print("[3/5] Verifying pre-flight sub-second falsification probes...")

    director = FaradayDirector()

    # 1. Sound, passing probe
    assessment_ok = director.assess_goal("Execute local algorithmic calculation with sympy")
    ok, out_ok = director.run_falsification_probe(assessment_ok)
    assert ok, f"Passing probe should succeed: {out_ok}"
    assert assessment_ok.viable
    assert assessment_ok.falsification_result is not None
    assert assessment_ok.falsification_result["passed"]

    # 2. Failing probe: fatal boundary condition disproved immediately
    assessment_bad = director.assess_goal("Launch quantum cluster on non-existent driver")
    # Invalidate probe deliberately to test falsification interception
    assessment_bad.cheapest_falsification_probe = {
        "command": "non_existent_quantum_daemon --status",
        "timeout_sec": 1,
    }
    bad_ok, bad_out = director.run_falsification_probe(assessment_bad)
    assert not bad_ok, "Invalid probe must fail"
    assert not assessment_bad.viable
    assert assessment_bad.falsification_result["exit_code"] != 0

    print("  ✓ Pre-flight falsification probe confirmed: valid runtime confirmed, doomed runtime halted.")


def verify_candidate_task_decomposition() -> None:
    print("[4/5] Verifying candidate task decomposition & YAGNI exclusion...")

    director = FaradayDirector()
    assessment = director.assess_goal("Build a bwrap sandbox jail for daemon processes")

    tasks = director.synthesize_mrp_candidate_tasks(assessment)

    # Step 0 must be the preflight probe
    assert tasks[0]["id"] == "t0_preflight_probe"
    assert tasks[0]["metadata"]["critical"] is True

    # Total tasks = 1 (preflight) + len(what_to_build)
    assert len(tasks) == 1 + len(assessment.what_to_build)

    # Confirm strict topological dependency chain
    for i in range(1, len(tasks)):
        assert tasks[i]["depends_on"] == [tasks[i-1]["id"]]

    # Ensure none of the 'what_to_skip' items leaked into the candidate build tasks
    task_titles = [t["title"].lower() for t in tasks]
    for skipped in assessment.what_to_skip:
        assert skipped.lower() not in task_titles, f"Skipped item '{skipped}' leaked into tasks"

    print(f"  ✓ Decomposed into {len(tasks)} tasks; gold-plating strictly excluded from build horizon.")


def verify_end_to_end_closed_loop_pipeline() -> None:
    print("[5/5] Verifying end-to-end pipeline: Phase 0 -> Phase 1 -> Phase 2 -> Phase 3...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_p0_closed_loop.db"
        ws = Path(tmpdir)

        # 1. Phase 0: Faraday Director Assessment
        director = FaradayDirector(workspace_root=ws)
        assessment = director.assess_goal(
            goal="Establish local system environment probe",
            existing_symbols=["echo"],
        )
        assert assessment.viable

        # Run preflight probe
        probe_passed, probe_msg = director.run_falsification_probe(assessment, workspace_root=ws)
        assert probe_passed

        # 2. Bridge to Phase 1: MRP Plan
        mrp_plan = director.bridge_to_mrp_plan(assessment, existing_symbols=["echo"])
        assert isinstance(mrp_plan, MRPPlan)
        assert len(mrp_plan.execution_waves) >= 1
        assert "faraday_assessment" in mrp_plan.metadata

        # 3. Execute through Phase 2 (/loop) & Phase 3 (Native Contract Gate)
        gate = NativeContractGate()
        orchestrator = LoopOrchestrator(
            max_steps=10,
            workspace_root=ws,
            db_path=test_db,
            contract_gate=gate,
        )

        receipt = orchestrator.execute_plan(mrp_plan)

        assert receipt.termination_reason == LoopTerminationReason.DONE
        assert len(receipt.completed_task_ids) == len(mrp_plan.graph.nodes)
        assert len(receipt.failed_task_ids) == 0

        # Verify all task nodes passed
        for node in mrp_plan.graph.nodes.values():
            assert node.status == TaskState.COMPLETED

    print(f"  ✓ Complete Closed-Loop Pipeline (P0 -> P1 -> P2 -> P3) executed autonomously to DONE in {receipt.total_steps} steps.")


def main() -> None:
    print("==================================================================")
    print("  PHASE 0 IN-PROCESS VERIFICATION: FARADAY DIRECTOR MODE           ")
    print("  (What to build, What to skip, What to validate first)           ")
    print("==================================================================")
    verify_domain_classification()
    verify_faraday_invariants_formulation()
    verify_preflight_falsification_probes()
    verify_candidate_task_decomposition()
    verify_end_to_end_closed_loop_pipeline()
    print("==================================================================")
    print("  ✅ PHASE 0 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN     ")
    print("==================================================================")


if __name__ == "__main__":
    main()
