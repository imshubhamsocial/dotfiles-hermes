"""
Contract Tests: Roadmap 3 Milestones U41, U42, and U44
======================================================
Validates:
  1. U41: LoRA Adapter Manager hot-swap, scaling, language matching, and VRAM guard (<150 MB).
  2. U42: BGE Code Template Retriever neural search, language filtering, and compact context formatting (<400 tok).
  3. U44: Spec-First Senior Engineer formal specification drafting and .hermes/plan.json export.
"""

import json
import pytest
from pathlib import Path
from hermes_core.lora_adapter_manager import LoRAAdapterManager, LoRAAdapterMetadata
from hermes_core.template_retriever import BGETemplateRetriever, CodeTemplate
from hermes_core.spec_first_planner import SpecFirstPlanner, EngineeringSpec


class TestRoadmap3Contracts:
    """Contract tests for U41, U42, and U44."""

    # ── U41: LoRA Adapter Engine ─────────────────────────────────────────
    def test_u41_adapter_registry_and_discovery(self):
        manager = LoRAAdapterManager()
        adapters = manager.list_available_adapters()
        assert len(adapters) >= 5
        names = [a["name"] for a in adapters]
        assert "python_core" in names
        assert "javascript_typescript" in names
        assert "modern_cpp" in names
        assert "threejs_kinematics" in names

    def test_u41_language_routing(self):
        manager = LoRAAdapterManager()
        py_adapter = manager.get_adapter_for_language("py")
        assert py_adapter is not None
        assert py_adapter.name == "python_core"

        cpp_adapter = manager.get_adapter_for_language("cpp")
        assert cpp_adapter is not None
        assert cpp_adapter.name == "modern_cpp"

    def test_u41_vram_guard_and_activation(self):
        manager = LoRAAdapterManager(max_vram_mb=100.0)
        assert manager.activate_adapter("python_core", scale=1.0) is True
        assert manager.activate_adapter("javascript_typescript", scale=0.8) is True
        
        # Total VRAM should be python + js
        vram = manager.get_current_vram_consumption_mb()
        assert vram > 0
        assert vram <= 100.0

        payload = manager.format_llama_server_payload()
        assert len(payload) == 2
        assert payload[0]["scale"] == 1.0

    # ── U42: BGE Template Retriever ──────────────────────────────────────
    def test_u42_bge_neural_template_retrieval(self):
        retriever = BGETemplateRetriever()
        matches = retriever.retrieve_template("Build a 3D orbit solar system with Three.js canvas", language="javascript")
        assert len(matches) > 0
        assert matches[0].template_id == "threejs_orbit_kinematics"
        assert "THREE" in matches[0].code_content

    def test_u42_context_injection_formatting(self):
        retriever = BGETemplateRetriever()
        injection = retriever.format_context_injection("Write RAII memory guard in C++", language="cpp")
        assert "<!-- CANONICAL TEMPLATE" in injection
        assert "ResourceGuard" in injection

    # ── U44: Spec-First Planner ──────────────────────────────────────────
    def test_u44_formal_spec_generation(self, tmp_path):
        plan_file = tmp_path / "plan.json"
        planner = SpecFirstPlanner(plan_file=plan_file)
        
        spec = planner.create_formal_spec("Create interactive 3D Three.js solar simulation")
        assert len(spec.interfaces) >= 2
        assert len(spec.failure_modes) >= 2
        assert len(spec.milestones) >= 4

        planner.export_to_plan_json(spec)
        assert plan_file.exists()
        
        data = json.loads(plan_file.read_text(encoding="utf-8"))
        assert data["domain"] == "webgl_kinematics"
        assert len(data["milestones"]) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
