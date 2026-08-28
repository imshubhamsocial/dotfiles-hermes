"""
Harness Contract: Milestones U72-U74 — Synergy, Antigravity Bridge & Hooks
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.antigravity_skills import AntigravitySkillsBridge, create_antigravity_bridge
from hermes_core.hook_router import HookExecutionContext, HookRouter, create_hook_router
from hermes_core.multi_bot_delegation import MultiBotOrchestrator, create_multi_bot_orchestrator


class TestSynergyAndHooksContract:
    def test_antigravity_bridge_discovery(self):
        bridge = create_antigravity_bridge()
        res = bridge.discover_skills()
        assert res.target_tier == "L1_AGENT"
        assert res.mounted_count >= 0

    def test_multi_bot_delegation_pipeline(self):
        orchestrator = create_multi_bot_orchestrator()
        report = orchestrator.execute_delegation_pipeline(
            goal="Design and verify lock-free concurrent ringbuffer",
            session_id="integration_test_sess",
        )
        assert report.overall_status == "SUCCESS"
        assert len(report.turns) == 3  # architect -> coder -> tester
        stages = [t.stage for t in report.turns]
        assert "Phase 1: Spec-First Decomposition" in stages[0]
        assert "Phase 2: Modular Code Synthesis" in stages[1]
        assert "Phase 3: Dynamic Invariant Testing" in stages[2]

    def test_hook_router_dispatch(self, tmp_path: Path):
        router = create_hook_router(hooks_dir=tmp_path / "hooks")
        events_captured = []

        def test_handler(ctx: HookExecutionContext):
            events_captured.append(ctx.event_name)
            ctx.payload["processed"] = True

        router.register_handler("pre_turn", test_handler)
        ctx = router.trigger("pre_turn", session_id="test_hook", payload={"prompt": "hello"})
        assert "pre_turn" in events_captured
        assert ctx.payload.get("processed") is True
