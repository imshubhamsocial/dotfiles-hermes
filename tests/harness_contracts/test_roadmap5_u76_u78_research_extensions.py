"""
Harness Contract: Milestones U76-U78 — Qwen MM Local Reader, Loop Contracts & Graph DAG
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.graph_engine import GraphEngine, create_graph_engine
from hermes_core.loop_contracts import LoopContract, LoopController, create_loop_controller
from hermes_core.qwen_mm_core import QwenMMCoreReader, create_qwen_mm_reader


class TestResearchExtensionsContract:
    def test_qwen_mm_local_reader(self, tmp_path: Path):
        reader = create_qwen_mm_reader(output_dir=tmp_path / "mm_out")

        # Test document inspection
        doc_file = tmp_path / "spec.md"
        doc_file.write_text("# High Concurrency Spec\nDetails here.")
        res_doc = reader.inspect(doc_file)
        assert res_doc.success is True
        assert res_doc.media_type == "document"
        assert "High Concurrency Spec" in res_doc.extracted_text

    def test_loop_contract_stop_conditions(self):
        controller = create_loop_controller(LoopContract(max_iterations=3, vram_ceiling_mib=4812))

        # Iteration 1: Normal step
        sig1 = controller.evaluate_step(vram_usage_mib=3800, step_success=True)
        assert sig1.action == "CONTINUE"
        assert sig1.should_halt is False

        # VRAM Breach trigger
        sig_vram = controller.evaluate_step(vram_usage_mib=4900, step_success=True)
        assert sig_vram.action == "STOP_VRAM_BREACH"
        assert sig_vram.should_halt is True

        # Success Signal trigger
        controller_success = create_loop_controller(LoopContract(required_success_signals=["pytest_pass"]))
        sig_ok = controller_success.evaluate_step(step_success=True, signals={"pytest_pass": True})
        assert sig_ok.action == "STOP_SUCCESS"
        assert sig_ok.should_halt is True

        # Tabu 2-Strike trigger
        controller_tabu = create_loop_controller(LoopContract(consecutive_failure_limit=2))
        controller_tabu.evaluate_step(step_success=False)
        sig_tabu = controller_tabu.evaluate_step(step_success=False)
        assert sig_tabu.action == "STOP_TABU_TRIP"
        assert sig_tabu.should_halt is True

    def test_graph_dag_topology_and_typed_contracts(self):
        engine = create_graph_engine()
        topo_res = engine.validate_topology()
        assert topo_res.valid is True
        assert "intake" in topo_res.topological_order
        assert "plan" in topo_res.topological_order
        assert "synthesis" in topo_res.topological_order
        assert "verification" in topo_res.topological_order

        # Validate typed node output
        valid, errs = engine.validate_node_output(
            "intake",
            {"goal": "Build system", "grounding_evidence": ["https://example.com"]},
        )
        assert valid is True
        assert len(errs) == 0

        # Validate invalid payload rejection
        invalid, errs_bad = engine.validate_node_output("intake", {"wrong_field": 123})
        assert invalid is False
        assert len(errs_bad) > 0
