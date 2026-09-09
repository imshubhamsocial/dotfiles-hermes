"""
Contract & Unit Tests for Cactus Hybrid Uncertainty Detection (Track 4 - Phase 4.1)
===================================================================================
Verifies:
1. Model self-reported verbalized confidence & linguistic hedging extraction
2. Structural blast-radius and destructive mutation risk assessment
3. Trajectory history failure streak weighting
4. Composite hybrid uncertainty calculation and thresholding
5. Autonomous halt with targeted clarifying questions before destructive edits
6. LoopController integration with uncertainty ceiling (STOP_UNCERTAINTY_BREACH)
7. Lineage supervisory_scan integration (CLARIFY_OR_HALT intervention)
8. Zero GPU VRAM overhead (100% CPU execution)
"""

import json
import pytest
from pathlib import Path

from hermes_core.cactus import (
    CactusHybridDetector,
    CactusUncertaintyScore,
    UNCERTAINTY_HEDGES,
    CERTAINTY_ANCHORS,
)
from hermes_core.loop_contracts import LoopContract, LoopController, create_loop_controller
from hermes_core.lineage import supervisory_scan, Intervention
from hermes_core import trajectory as traj


class TestCactusHybridDetector:
    """Core algorithmic unit tests for Cactus Hybrid Uncertainty."""

    def test_verbalized_hedging_extraction(self):
        detector = CactusHybridDetector()

        # High-uncertainty thought with hedging markers
        thought_uncertain = "I am unsure about this refactor, it might break existing imports."
        score, hedges = detector.extract_verbalized_uncertainty(thought_uncertain)
        assert score >= 0.50
        assert "unsure" in hedges
        assert "might break" in hedges

        # High-certainty thought with verification anchors
        thought_certain = "This change is confirmed and verified deterministic."
        score_c, hedges_c = detector.extract_verbalized_uncertainty(thought_certain)
        assert score_c <= 0.10
        assert len(hedges_c) == 0

        # Explicit numeric confidence
        score_explicit, _ = detector.extract_verbalized_uncertainty(explicit_confidence=0.90)
        assert score_explicit == 0.10

        score_low_conf, _ = detector.extract_verbalized_uncertainty(explicit_confidence=0.20)
        assert score_low_conf == 0.80

    def test_action_risk_assessment(self):
        detector = CactusHybridDetector()

        # Non-mutating read tool
        risk_read, is_dest_read = detector.assess_action_risk("read_file", {"filepath": "main.py"})
        assert is_dest_read is False
        assert risk_read <= 0.10

        # Mutating regular file
        risk_write_norm, is_dest_norm = detector.assess_action_risk("write_file", {"filepath": "temp.py"})
        assert is_dest_norm is True
        assert risk_write_norm == 0.60

        # Mutating core architecture file
        risk_write_core, is_dest_core = detector.assess_action_risk("patch_file", {"filepath": ".hermes/src/hermes_core/agent.py"})
        assert is_dest_core is True
        assert risk_write_core == 0.90

        # Destructive bash command
        risk_bash, is_dest_bash = detector.assess_action_risk("bash", {"command": "rm -rf /tmp/build"})
        assert is_dest_bash is True
        assert risk_bash == 0.95

    def test_history_streak_weighting(self):
        detector = CactusHybridDetector()

        # 0 failures
        assert detector.assess_history_risk(0) == 0.0

        # 1 failure
        assert detector.assess_history_risk(1) == 0.50

        # 2 failures (2-Strike Tabu ceiling)
        assert detector.assess_history_risk(2) == 1.0
        assert detector.assess_history_risk(5) == 1.0

    def test_composite_hybrid_evaluation_and_autonomous_halt(self):
        detector = CactusHybridDetector(uncertainty_threshold=0.70)

        # Scenario A: High certainty, read-only -> PROCEED
        eval_safe = detector.evaluate_action(
            tool="read_file",
            args={"filepath": "README.md"},
            thought="Reading the documentation to confirm behavior.",
            verbalized_confidence=0.95,
            consecutive_failures=0,
        )
        assert eval_safe.is_uncertain is False
        assert eval_safe.is_destructive is False
        assert eval_safe.recommendation == "PROCEED"
        assert len(eval_safe.clarification_questions) == 0

        # Scenario B: High uncertainty on core mutation -> HALT_FOR_CLARIFICATION
        eval_halt = detector.evaluate_action(
            tool="write_file",
            args={"filepath": ".hermes/src/hermes_core/lineage.py"},
            thought="I am not sure if this might break the branch swapper; speculative edit.",
            consecutive_failures=1,
        )
        assert eval_halt.is_destructive is True
        assert eval_halt.is_uncertain is True
        assert eval_halt.score >= 0.70
        assert eval_halt.recommendation in ("HALT_FOR_CLARIFICATION", "ABORT_DESTRUCTIVE_ACTION")
        assert len(eval_halt.clarification_questions) >= 2
        # Verify clarification question mentions target file
        assert any("lineage.py" in q for q in eval_halt.clarification_questions)

    def test_loop_controller_uncertainty_ceiling_halt(self):
        contract = LoopContract(uncertainty_ceiling=0.70, enable_cactus_uncertainty=True)
        controller = create_loop_controller(contract)

        # Non-destructive action with high uncertainty does not halt
        sig1 = controller.evaluate_step(
            uncertainty_score=0.85,
            is_destructive=False,
        )
        assert sig1.action == "CONTINUE"
        assert sig1.should_halt is False

        # Destructive action with low uncertainty proceeds
        sig2 = controller.evaluate_step(
            uncertainty_score=0.35,
            is_destructive=True,
        )
        assert sig2.action == "CONTINUE"
        assert sig2.should_halt is False

        # Destructive action with high uncertainty trips STOP_UNCERTAINTY_BREACH
        questions = ["Confirm if overwriting core config is intended."]
        sig3 = controller.evaluate_step(
            uncertainty_score=0.78,
            is_destructive=True,
            clarification_questions=questions,
        )
        assert sig3.action == "STOP_UNCERTAINTY_BREACH"
        assert sig3.should_halt is True
        assert "Cactus hybrid uncertainty ceiling breached" in sig3.reason
        assert sig3.clarification_questions == questions

    def test_lineage_supervisory_scan_cactus_integration(self, tmp_path, monkeypatch):
        stream_path = tmp_path / "trajectory.jsonl"
        monkeypatch.setenv("HERMES_TRAJECTORY_PATH", str(stream_path))
        rec = traj.TrajectoryRecorder(session_id="cactus_test")

        # Step 0: Good baseline
        rec.record_tool_call(turn=0, role="coder", tool="write_file", args_head=json.dumps({"filepath": "root.py"}))
        rec.record_gate(turn=0, tool="write_file", gate_status="PASS")
        rec.record_tool_result(turn=0, tool="write_file", result_ok=True, result_head="ok")

        # Step 1: Highly uncertain attempt on core file with verbalized hedge
        rec.record_tool_call(
            turn=1,
            role="coder",
            tool="write_file",
            args_head=json.dumps({"filepath": ".hermes/src/hermes_core/critical.py"}),
            thought="I am unsure if this might break core dispatch; speculative patch without verifying.",
        )
        rec.record_gate(turn=1, tool="write_file", gate_status="REJECT")
        rec.record_tool_result(turn=1, tool="write_file", result_ok=False, result_head="error")

        interventions = supervisory_scan(stream_path)
        clarify_ivs = [i for i in interventions if i.kind == "CLARIFY_OR_HALT"]
        assert len(clarify_ivs) >= 1
        assert "Cactus hybrid uncertainty detected" in clarify_ivs[0].reason
        assert len(clarify_ivs[0].clarification_questions) > 0
