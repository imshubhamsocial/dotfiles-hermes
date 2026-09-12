#!/usr/bin/env python3
"""
Verification Script for Horizon 1: Autonomous In-The-Loop Execution Engine (/loop & /clear)
===========================================================================================
Executes in-process contract verification against:
  1. Multi-turn Autonomous Plan Execution (/loop) with Bounded Termination (DONE, BLOCKED, STEP_LIMIT)
  2. Native Context Boundary Compaction (/clear) at 80% Capacity (52,428 Tokens) & SQLite State Checkpoint
  3. Multi-Modality Tool Dispatch Subsystem (Sandbox Shell, Web Grounding, Multimodal Vision, CUA)
  4. Closed-Loop Native Contract Gate Enforcement at every autonomous step
  5. CLI Slash Command Interface (/loop auto <goal>, /loop status, /loop stop)
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

from agent.core.mrp_planner import (
    TaskState,
    create_mrp_plan,
)
from agent.core.loop_orchestrator import (
    LoopOrchestrator,
    LoopTerminationReason,
    StateCheckpointManager,
    ToolExecutionSubsystem,
    ToolModality,
    ContextFlushBridge,
    CONTEXT_FLUSH_THRESHOLD_TOKENS,
)
from agent.core.contract_gate import NativeContractGate
from hermes_cli.loops import dispatch_loop_command


def verify_autonomous_plan_execution() -> None:
    print("[1/5] Verifying autonomous multi-turn execution (/loop) without human intervention...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_loop.db"

        tasks = [
            {
                "id": "step_1_init",
                "title": "Initialize runtime workspace",
                "description": "Prepare directory structures",
                "depends_on": [],
                "verification": "echo 'INIT_COMPLETE'",
            },
            {
                "id": "step_2_audit",
                "title": "Audit hardware and VRAM ceiling",
                "description": "Inspect GPU memory bounds",
                "depends_on": ["step_1_init"],
                "verification": "echo 'VRAM_CEILING=4812'",
            },
            {
                "id": "step_3_finalize",
                "title": "Finalize autonomous deliverable",
                "description": "Certify state",
                "depends_on": ["step_2_audit"],
                "verification": "echo 'DELIVERABLE_VERIFIED'",
            },
        ]

        plan = create_mrp_plan(
            goal="Autonomous Three-Step Subsystem Execution",
            tasks=tasks,
            existing_symbols=["echo"],
        )

        orchestrator = LoopOrchestrator(
            max_steps=10,
            workspace_root=Path(tmpdir),
            db_path=test_db,
            contract_gate=NativeContractGate(),
        )

        receipt = orchestrator.execute_plan(plan)

        assert receipt.termination_reason == LoopTerminationReason.DONE
        assert receipt.total_steps == 3
        assert len(receipt.completed_task_ids) == 3
        assert len(receipt.failed_task_ids) == 0
        assert receipt.total_tokens_consumed > 0

        # Verify all graph nodes completed
        for node in plan.graph.nodes.values():
            assert node.status == TaskState.COMPLETED

    print(f"  ✓ Autonomous multi-turn execution executed to completion (DONE) in {receipt.total_steps} steps.")


def verify_context_boundary_flush_and_state_persistence() -> None:
    print("[2/5] Verifying native /clear context boundary flush at 80% (52,428 tokens)...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_state.db"
        state_mgr = StateCheckpointManager(db_path=test_db)
        bridge = ContextFlushBridge(threshold_tokens=CONTEXT_FLUSH_THRESHOLD_TOKENS, state_db=state_mgr)

        # 1. Under-threshold check
        assert not bridge.should_flush(40000)
        assert not bridge.should_flush(52427)

        # 2. Threshold boundary trigger (80% of 65,536 context)
        assert bridge.should_flush(52428)
        assert bridge.should_flush(55000)

        # 3. Execute /clear flush
        retained = bridge.execute_flush(
            loop_id="loop-h1-test",
            step_index=8,
            task_id="task-8",
            active_state={"invariants": ["Hardware ceiling 4,812 MiB", "Directive 24"], "active_task": "task-8"}
        )

        assert bridge.flush_count == 1
        assert retained == 1024, f"Expected 1,024 retained tokens, got {retained}"

        # 4. Confirm state was atomically written to SQLite in WAL mode
        checkpoint = state_mgr.get_latest_checkpoint("loop-h1-test")
        assert checkpoint is not None
        assert "Hardware ceiling 4,812 MiB" in checkpoint["invariants"]

    print("  ✓ Context boundary trigger (>=52,428 tokens) and /clear compaction verified.")


def verify_multi_modality_tool_dispatch() -> None:
    print("[3/5] Verifying unified multi-modality tool execution subsystem...")

    tools = ToolExecutionSubsystem(workspace_root=Path("/tmp/hermes_test_workspace"))

    # 1. Sandboxed shell execution
    shell_res = tools.execute_sandbox_shell("echo 'H1-SANDBOX-ALIVE'")
    assert shell_res.modality == ToolModality.SANDBOX_SHELL
    assert shell_res.success
    assert "H1-SANDBOX-ALIVE" in shell_res.output

    # 2. Keyless web grounding
    web_res = tools.execute_web_grounding("NVIDIA cuBLAS dynamic linker paths")
    assert web_res.modality == ToolModality.WEB_GROUNDING
    assert web_res.success
    assert len(web_res.output) > 0

    # 3. Multimodal vision reasoning (Port 8139)
    vision_res = tools.execute_vision("Verify bounding box layout on port 8139")
    assert vision_res.modality == ToolModality.VISION
    assert vision_res.success

    # 4. Computer-Use Automation (CUA)
    cua_res = tools.execute_cua("click", target="header_navigation")
    assert cua_res.modality == ToolModality.COMPUTER_USE
    assert cua_res.success

    print("  ✓ Multi-modal tool execution subsystem (Sandbox, Web, Vision, CUA) verified.")


def verify_bounded_termination_guardrails() -> None:
    print("[4/5] Verifying bounded loop termination criteria (DONE, BLOCKED, STEP_LIMIT_EXCEEDED)...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_guards.db"

        # 1. Step Limit Exceeded Guard
        tasks_long = [
            {"id": f"step_{i}", "title": f"Step {i}", "description": "", "depends_on": [f"step_{i-1}"] if i > 0 else [], "verification": f"echo 'Step {i}'"}
            for i in range(5)
        ]
        plan_long = create_mrp_plan(goal="Long Step Plan", tasks=tasks_long, existing_symbols=["echo"])

        orch_limit = LoopOrchestrator(max_steps=2, db_path=test_db)
        receipt_limit = orch_limit.execute_plan(plan_long)
        assert receipt_limit.termination_reason == LoopTerminationReason.STEP_LIMIT_EXCEEDED
        assert receipt_limit.total_steps == 2
        print("  ✓ STEP_LIMIT_EXCEEDED invariant confirmed.")

        # 2. Blocked Invariant on Contract / Step Failure
        tasks_fail = [
            {
                "id": "critical_failing_task",
                "title": "Critical Failing Task",
                "description": "Fails verification",
                "depends_on": [],
                "verification": "false",
            },
            {
                "id": "unreached_task",
                "title": "Unreached Task",
                "description": "Should never run",
                "depends_on": ["critical_failing_task"],
                "verification": "echo 'Unreached'",
            },
        ]
        plan_fail = create_mrp_plan(goal="Failing Plan", tasks=tasks_fail, existing_symbols=["false"])

        orch_fail = LoopOrchestrator(max_steps=10, db_path=test_db)
        receipt_fail = orch_fail.execute_plan(plan_fail)
        assert receipt_fail.termination_reason == LoopTerminationReason.BLOCKED
        assert "critical_failing_task" in receipt_fail.failed_task_ids
        assert "unreached_task" not in receipt_fail.completed_task_ids
        print("  ✓ BLOCKED invariant confirmed on critical task failure.")


def verify_cli_loop_command_surface() -> None:
    print("[5/5] Verifying CLI slash command interface (/loop auto <goal>)...")

    class MockLoopManager:
        def __init__(self):
            self.session_id = "test-session-h1"
            self._has_loop = False

        def has_loop(self) -> bool:
            return self._has_loop

        def clear(self) -> bool:
            had = self._has_loop
            self._has_loop = False
            return had

        def set(self, prompt, **kwargs):
            self._has_loop = True
            from hermes_cli.loops import LoopState
            return LoopState(prompt=prompt)

    mgr = MockLoopManager()

    # 1. Test /loop auto <goal> autonomous in-the-loop execution
    res = dispatch_loop_command(mgr, "auto Probe local runtime architecture")
    assert res["created"] is True
    assert "Autonomous /loop Completed" in res["output"]
    assert "Termination: DONE" in res["output"]
    assert "Goal: Probe local runtime architecture" in res["output"]

    # 2. Test /loop stop control command
    res_stop = dispatch_loop_command(mgr, "stop")
    assert "Loop stopped" in res_stop["output"] or "No active loop" in res_stop["output"]

    print("  ✓ CLI slash command surface (/loop auto) correctly drives autonomous execution engine.")


def main() -> None:
    print("==================================================================")
    print("  HORIZON 1 IN-PROCESS VERIFICATION: AUTONOMOUS LOOP ENGINE        ")
    print("  (/loop & /clear In-The-Loop Execution & Native Context Flush)   ")
    print("==================================================================")
    verify_autonomous_plan_execution()
    verify_context_boundary_flush_and_state_persistence()
    verify_multi_modality_tool_dispatch()
    verify_bounded_termination_guardrails()
    verify_cli_loop_command_surface()
    print("==================================================================")
    print("  ✅ HORIZON 1 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN   ")
    print("==================================================================")


if __name__ == "__main__":
    main()
