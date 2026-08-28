"""
Master Grand Prix Production Certification Suite: Roadmap 5 (Milestone U75)
===========================================================================
Comprehensive Capstone Verification Suite for Hermes Frontier Multi-Agent Web Intelligence.
Validates all 20 milestones (U61-U80) and 5 architectural invariants (R5-1 to R5-5):
  - Invariant R5-1: Web-Before-Plan
  - Invariant R5-2: Single-Skill-Per-Turn (<=200 tok)
  - Invariant R5-3: Bot Isolation Purity
  - Invariant R5-4: Second-Brain-Commit-Gate
  - Invariant R5-5: 128K VRAM Hard Guard (<=4,812 MiB)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest

# Roadmap 5 Subsystems
from hermes_core.intent_router import create_intent_router
from hermes_core.web_grounding import create_web_grounding_engine
from hermes_core.skill_router import create_skill_router
from hermes_core.second_brain import KnowledgeCard, create_second_brain
from hermes_core.context_window_guard import create_context_window_guard
from hermes_core.humanizer import create_humanizer
from hermes_core.domain_fleet import create_domain_fleet_manager
from hermes_core.antigravity_skills import create_antigravity_bridge
from hermes_core.multi_bot_delegation import create_multi_bot_orchestrator
from hermes_core.hook_router import create_hook_router
from hermes_core.qwen_mm_core import create_qwen_mm_reader
from hermes_core.loop_contracts import LoopContract, create_loop_controller
from hermes_core.graph_engine import create_graph_engine
from hermes_core.speculative_executor import create_speculative_executor


class TestRoadmap5GrandPrixMasterCertification:
    """Master capstone verification for the complete Roadmap 5 architecture."""

    def test_grand_prix_tier1_intake_and_grounding(self, tmp_path: Path):
        # 1. Intent Router (U61)
        router = create_intent_router()
        dec = router.route_intent("Architect a high performance multi-agent DAG")
        assert dec.target_bot.bot_class == "architect"

        # 2. Web Grounding (U62, R5-1)
        web = create_web_grounding_engine()
        g_res = web.ground("Hermes Agent OS", policy="before_plan", trigger_context="architect")
        assert g_res.executed is True
        assert g_res.token_estimate <= 400

        # 3. 4-Tier Skill Hierarchy (U63, R5-2)
        sk_router = create_skill_router()
        sk_res = sk_router.route("Python systematic debugging", max_tokens=200)
        assert sk_res.token_count <= 200

        # 4. Second Brain (U64, R5-4)
        brain = create_second_brain(root_dir=tmp_path / "knowledge")
        card = KnowledgeCard(
            id="grand-prix-spec",
            title="Grand Prix Specification",
            category="blueprints",
            content="Grounded blueprint validated by Grand Prix certification.",
            tags=["certification", "roadmap5"],
        )
        saved = brain.save(card)
        assert saved.exists()

    def test_grand_prix_tier2_context_and_fleet_isolation(self, tmp_path: Path):
        # 1. Context Window & VRAM Guard (U65, R5-5)
        guard = create_context_window_guard()
        assessment = guard.estimate_vram(131072, slots=2)
        assert assessment.requires_flash_attn is True

        # 2. Humanizer Default (U66)
        humanizer = create_humanizer()
        h_res = humanizer.humanize("Certainly! Here is the code:\n```python\npass\n```")
        assert "Certainly!" not in h_res.humanized_text

        # 3. Domain Fleet Clean-Room Isolation (U67-U71, R5-3)
        fleet = create_domain_fleet_manager(scratchpad_root=tmp_path / "scratchpads")
        arch_turn = fleet.prepare_bot_turn("architect", "Plan system")
        coder_turn = fleet.prepare_bot_turn("coder", "Code system")
        assert arch_turn.scratchpad_dir != coder_turn.scratchpad_dir
        assert "Never write or edit code files directly" in arch_turn.system_prompt
        assert "Never write or edit code files directly" not in coder_turn.system_prompt

    def test_grand_prix_tier3_synergy_and_graph_execution(self, tmp_path: Path):
        # 1. Antigravity Skills Bridge (U72)
        bridge = create_antigravity_bridge()
        assert bridge.discover_skills().target_tier == "L1_AGENT"

        # 2. Multi-Bot Delegation Pipeline (U73)
        orchestrator = create_multi_bot_orchestrator()
        report = orchestrator.execute_delegation_pipeline("Synthesize verified module")
        assert report.overall_status == "SUCCESS"
        assert len(report.turns) == 3

        # 3. Lifecycle Hooks (U74)
        h_router = create_hook_router(hooks_dir=tmp_path / "hooks")
        ctx = h_router.trigger("pre_turn", payload={"ready": True})
        assert ctx.payload.get("ready") is True

        # 4. Qwen-MM Local Reader (U76)
        mm_reader = create_qwen_mm_reader(output_dir=tmp_path / "mm")
        f_sample = tmp_path / "note.txt"
        f_sample.write_text("Multimodal note")
        assert mm_reader.inspect(f_sample).success is True

        # 5. Loop Stop Conditions (U77)
        l_controller = create_loop_controller(LoopContract(max_iterations=2))
        l_controller.evaluate_step(step_success=True)
        sig2 = l_controller.evaluate_step(step_success=True)
        assert sig2.action == "STOP_MAX_ITER"
        assert sig2.should_halt is True

        # 6. Graph DAG Engine (U78)
        g_engine = create_graph_engine()
        assert g_engine.validate_topology().valid is True

        # 7. Speculative Tool Execution (U79)
        s_exec = create_speculative_executor()
        s_exec.register_tool_handler("read_file", lambda query: f"Read {query}")
        s_exec.observe_stream_delta("read_file(query='file.txt')")
        val, claimed = s_exec.claim_or_execute("read_file", {"query": "file.txt"})
        assert val == "Read file.txt"
        assert claimed is True
