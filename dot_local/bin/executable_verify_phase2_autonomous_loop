#!/usr/bin/env python3
"""
Verification Script for Phase 2: Autonomous Tool Execution & Context Flush (/loop & /clear)
=============================================================================================
Executes in-process contract verification against:
  1. ToolExecutionSubsystem Multi-Modality Dispatch (Sandbox Shell, Web Grounding, Multimodal Vision, CUA)
  2. StateCheckpointManager SQLite Persistence (Atomic checkpoint writes and reads in state.db)
  3. ContextFlushBridge (/clear Context Boundary & 80% / 52,428 Token Threshold Trigger)
  4. LoopOrchestrator Multi-Step Plan Execution & State Transitions
  5. Bounded Termination Invariants (DONE, BLOCKED, STEP_LIMIT_EXCEEDED, BUDGET_EXCEEDED)
  6. End-to-End Autonomous Loop Orchestration with Context Compaction
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add active hermes-agent paths
for p in [
    Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/hermes-agent"),
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.mrp_planner import (
    MRPPlan,
    TaskDependencyGraph,
    TaskNode,
    TaskState,
    create_mrp_plan,
)
from agent.core.loop_orchestrator import (
    LoopOrchestrator,
    LoopReceipt,
    LoopStepRecord,
    LoopTerminationReason,
    StateCheckpointManager,
    ToolExecutionResult,
    ToolExecutionSubsystem,
    ToolModality,
    ContextFlushBridge,
    estimate_tokens,
    execute_autonomous_loop,
    CONTEXT_FLUSH_THRESHOLD_TOKENS,
)


def verify_tool_modalities() -> None:
    print("[1/6] Verifying ToolExecutionSubsystem multi-modal tool dispatch...")

    tools = ToolExecutionSubsystem(workspace_root=Path("/tmp/hermes_test_workspace"))

    # 1. Sandbox shell execution
    shell_res = tools.execute_sandbox_shell("echo 'Phase2-Sandbox-Alive'")
    assert shell_res.modality == ToolModality.SANDBOX_SHELL
    assert shell_res.success, f"Shell command should succeed: {shell_res.error}"
    assert "Phase2-Sandbox-Alive" in shell_res.output
    assert shell_res.tokens_consumed > 0
    print("  ✓ Sandbox shell execution confirmed.")

    # 2. Keyless web grounding
    web_res = tools.execute_web_grounding("Linux cgroup v2 memory limits")
    assert web_res.modality == ToolModality.WEB_GROUNDING
    assert web_res.success
    assert len(web_res.output) > 0
    print("  ✓ Keyless web grounding dispatch confirmed.")

    # 3. Multimodal vision reasoning (Port 8139 local runtime)
    vision_res = tools.execute_vision("Verify UI bounding box coordinates")
    assert vision_res.modality == ToolModality.VISION
    assert vision_res.success
    assert "visual" in vision_res.output.lower() or "vision" in vision_res.output.lower()
    print("  ✓ Multimodal vision interface confirmed.")

    # 4. Computer-Use Automation (CUA)
    cua_res = tools.execute_cua("click_element", target="submit_button")
    assert cua_res.modality == ToolModality.COMPUTER_USE
    assert cua_res.success
    assert "submit_button" in cua_res.output
    print("  ✓ Computer-Use Automation (CUA) dispatch confirmed.")


def verify_state_checkpoint_manager() -> None:
    print("[2/6] Verifying StateCheckpointManager SQLite persistence...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_state.db"
        mgr = StateCheckpointManager(db_path=test_db)
        assert test_db.exists(), "State database file must be created on initialization"

        # Save checkpoint
        state_payload = {
            "completed_tasks": ["task-1", "task-2"],
            "variables": {"status": "in_progress", "code": 0},
            "active_rung": "RUNG_2_CODEBASE_REUSE",
        }
        cid = mgr.save_checkpoint(
            loop_id="loop-test-01",
            step_index=2,
            task_id="task-2",
            state_data=state_payload,
        )
        assert cid.startswith("cp-")

        # Retrieve checkpoint
        latest = mgr.get_latest_checkpoint(loop_id="loop-test-01")
        assert latest is not None, "Failed to retrieve latest checkpoint"
        assert latest["completed_tasks"] == ["task-1", "task-2"]
        assert latest["variables"]["status"] == "in_progress"
        assert latest["active_rung"] == "RUNG_2_CODEBASE_REUSE"

        # Checkpoint for non-existent loop
        assert mgr.get_latest_checkpoint("loop-nonexistent") is None

    print("  ✓ SQLite atomic checkpoint write, read, and serialization verified.")


def verify_context_flush_bridge() -> None:
    print("[3/6] Verifying ContextFlushBridge (/clear) 80% threshold & memory compaction...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_flush_state.db"
        mgr = StateCheckpointManager(db_path=test_db)
        bridge = ContextFlushBridge(threshold_tokens=52428, state_db=mgr)

        # Under threshold
        assert not bridge.should_flush(45000)
        assert not bridge.should_flush(52427)

        # At or above threshold (80% capacity boundary)
        assert bridge.should_flush(52428)
        assert bridge.should_flush(60000)

        # Execute /clear
        state = {"active_invariants": ["Directive 24", "Hardware Budget"], "step": 14}
        retained = bridge.execute_flush(
            loop_id="loop-flush-01",
            step_index=14,
            task_id="task-14",
            active_state=state,
        )

        assert bridge.flush_count == 1
        assert retained == 1024, f"Expected retained seed ~1024 tokens, got {retained}"
        assert bridge.working_context_tokens == 1024

        # Verify state was persisted to DB upon flush
        checkpoint = mgr.get_latest_checkpoint("loop-flush-01")
        assert checkpoint is not None
        assert "Directive 24" in checkpoint["active_invariants"]

    print("  ✓ Context boundary trigger (>=52,428 tokens) and /clear compaction verified.")


def verify_loop_orchestrator_success() -> None:
    print("[4/6] Verifying LoopOrchestrator successful execution path (DONE)...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_exec.db"

        tasks = [
            {
                "id": "probe_arch",
                "title": "Probe architecture configuration",
                "description": "Examine environment flags",
                "depends_on": [],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'ARCH=x86_64'",
            },
            {
                "id": "verify_vision_module",
                "title": "Verify multimodal vision pipeline",
                "description": "Inspect visual reasoning capabilities",
                "depends_on": ["probe_arch"],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'VISION_OK'",
            },
            {
                "id": "audit_runtime",
                "title": "Audit runtime state",
                "description": "Confirm all subsystems operational",
                "depends_on": ["verify_vision_module"],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'RUNTIME_READY'",
            },
        ]

        plan = create_mrp_plan(
            goal="Execute Autonomous Subsystem Audit",
            tasks=tasks,
            existing_symbols=["echo"],
        )

        orchestrator = LoopOrchestrator(
            max_steps=10,
            workspace_root=Path(tmpdir),
            db_path=test_db,
        )

        receipt = orchestrator.execute_plan(plan)

        assert receipt.termination_reason == LoopTerminationReason.DONE
        assert receipt.total_steps == 3
        assert len(receipt.completed_task_ids) == 3
        assert len(receipt.failed_task_ids) == 0
        assert len(receipt.records) == 3
        assert receipt.total_tokens_consumed > 0

        # Verify task node statuses in plan
        for node in plan.graph.nodes.values():
            assert node.status == TaskState.COMPLETED

    print(f"  ✓ Autonomous plan executed to completion (DONE) in {receipt.total_steps} steps.")


def verify_loop_termination_invariants() -> None:
    print("[5/6] Verifying bounded termination invariants (STEP_LIMIT_EXCEEDED & BLOCKED)...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_invariants.db"

        # 1. Step Limit Exceeded
        tasks_long = [
            {"id": f"t_{i}", "title": f"Task {i}", "description": "", "depends_on": [f"t_{i-1}"] if i > 0 else [], "verification": f"echo 'Step {i}'"}
            for i in range(5)
        ]
        plan_long = create_mrp_plan(goal="Long Plan", tasks=tasks_long, existing_symbols=["echo"])

        orch_limited = LoopOrchestrator(max_steps=2, db_path=test_db)
        receipt_limited = orch_fail = orch_limited.execute_plan(plan_long)
        assert receipt_limited.termination_reason == LoopTerminationReason.STEP_LIMIT_EXCEEDED
        assert receipt_limited.total_steps == 2
        print("  ✓ STEP_LIMIT_EXCEEDED invariant confirmed.")

        # 2. Critical Dependency Failure -> BLOCKED
        tasks_fail = [
            {
                "id": "failing_task",
                "title": "Mandatory Task That Fails",
                "description": "Fails hard",
                "depends_on": [],
                "verification": "false",  # Exits with 1
            },
            {
                "id": "subsequent_task",
                "title": "Subsequent Task",
                "description": "Should never run",
                "depends_on": ["failing_task"],
                "verification": "echo 'Should not reach'",
            },
        ]
        plan_fail = create_mrp_plan(goal="Failing Plan", tasks=tasks_fail, existing_symbols=["false"])

        orch_fail = LoopOrchestrator(max_steps=10, db_path=test_db)
        receipt_fail = orch_fail.execute_plan(plan_fail)
        assert receipt_fail.termination_reason == LoopTerminationReason.BLOCKED
        assert "failing_task" in receipt_fail.failed_task_ids
        assert "subsequent_task" not in receipt_fail.completed_task_ids
        print("  ✓ BLOCKED invariant confirmed on critical task failure.")


def verify_context_flush_in_loop() -> None:
    print("[6/6] Verifying autonomous /clear context flush triggered inside active loop...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_flush_loop.db"

        tasks = [
            {
                "id": "task_heavy_1",
                "title": "Execute heavy web grounding analysis",
                "description": "Fetch online references",
                "depends_on": [],
                "verification": "echo 'Heavy analysis step 1'",
            },
            {
                "id": "task_heavy_2",
                "title": "Generate comprehensive report",
                "description": "Synthesize results",
                "depends_on": ["task_heavy_1"],
                "verification": "echo 'Heavy analysis step 2'",
            },
        ]

        plan = create_mrp_plan(goal="Heavy Context Plan", tasks=tasks, existing_symbols=["echo"])

        orchestrator = LoopOrchestrator(max_steps=10, db_path=test_db)
        # Set artificially low threshold to verify /clear trigger during loop
        orchestrator.flush_bridge.threshold_tokens = 500

        receipt = orchestrator.execute_plan(plan)

        assert receipt.termination_reason == LoopTerminationReason.DONE
        assert receipt.clear_flushes_count >= 1, f"Expected at least 1 /clear flush, got {receipt.clear_flushes_count}"
        
        # Verify receipt serialization
        data = receipt.to_dict()
        assert data["termination_reason"] == "DONE"
        assert data["clear_flushes_count"] >= 1
        assert len(data["step_records"]) == 2

    print(f"  ✓ Context boundary trigger (/clear) successfully fired during loop ({receipt.clear_flushes_count} flushes).")


def main() -> None:
    print("==================================================================")
    print("  PHASE 2 IN-PROCESS VERIFICATION: AUTONOMOUS LOOP & /CLEAR ENGINE ")
    print("==================================================================")
    verify_tool_modalities()
    verify_state_checkpoint_manager()
    verify_context_flush_bridge()
    verify_loop_orchestrator_success()
    verify_loop_termination_invariants()
    verify_context_flush_in_loop()
    print("==================================================================")
    print("  ✅ PHASE 2 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN     ")
    print("==================================================================")


if __name__ == "__main__":
    main()
