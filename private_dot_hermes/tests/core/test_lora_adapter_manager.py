"""
Contract & Unit Tests for LoRA Adapter Manager & QLoRA Fine-Tuning (Track 4 - Phase 4.2)
========================================================================================
Verifies:
1. Built-in domain adapter registration and metadata specs
2. Per-adapter strict VRAM guard (<150 MiB) and hardware safety ceiling (<= 4,812 MiB)
3. Single Active Adapter Invariant (automatic hot-swap deactivation)
4. Autonomous intent routing via file AST extensions and task keywords
5. Llama-server /lora-adapters hot-swap payload formatting
6. QLoRA training pipeline non-regression verification and GGUF export
"""

import json
import pytest
from pathlib import Path

from hermes_core.lora_adapter import (
    LoRAAdapterManager,
    LoRAAdapterSpec,
    create_lora_adapter_manager,
    BUILTIN_ADAPTER_SPECS,
    MAX_ADAPTER_VRAM_MIB,
    HARDWARE_VRAM_CEILING_MIB,
)
import sys
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from train_qlora_adapter import (
    QLoRAConfig,
    QLoRATrainingHarness,
)


class TestLoRAAdapterManager:
    """Core tests for LoRA Adapter Manager and runtime routing."""

    def test_builtin_adapter_specs_and_vram_limits(self):
        manager = create_lora_adapter_manager()
        adapters = manager.list_adapters()
        assert len(adapters) >= 5

        # Verify all built-in adapters adhere to <150 MiB VRAM guard
        for spec in adapters:
            assert spec.estimated_vram_mib < MAX_ADAPTER_VRAM_MIB, (
                f"Adapter {spec.name} ({spec.estimated_vram_mib} MiB) breaches {MAX_ADAPTER_VRAM_MIB} MiB guard"
            )
            assert spec.rank == 16
            assert spec.alpha == 32
            assert len(spec.target_modules) > 0

    def test_adapter_registration_vram_rejection(self):
        manager = create_lora_adapter_manager()

        # Reject adapter that exceeds 150 MiB limit
        bloated_spec = LoRAAdapterSpec(
            name="bloated_adapter",
            domain="test",
            description="Exceeds VRAM guard",
            estimated_vram_mib=200.0,
        )
        with pytest.raises(ValueError, match="exceeds VRAM guard"):
            manager.register_adapter(bloated_spec)

    def test_single_active_adapter_and_hot_swapping(self):
        manager = create_lora_adapter_manager()
        assert manager.get_active_adapter() is None

        # 1. Activate python_core
        ok, msg = manager.activate_adapter("python_core", current_system_vram_mib=3200.0)
        assert ok is True
        active = manager.get_active_adapter()
        assert active is not None and active.name == "python_core"
        assert active.active is True

        # 2. Hot-swap to javascript_ts (must deactivate python_core)
        ok2, msg2 = manager.activate_adapter("javascript_ts", current_system_vram_mib=3200.0)
        assert ok2 is True
        new_active = manager.get_active_adapter()
        assert new_active is not None and new_active.name == "javascript_ts"
        assert manager.get_adapter("python_core").active is False

        # 3. Deactivate all
        manager.deactivate_all()
        assert manager.get_active_adapter() is None
        assert manager.get_adapter("javascript_ts").active is False

    def test_hardware_vram_ceiling_guard(self):
        manager = create_lora_adapter_manager()

        # Near hardware limit (4,780 MiB allocated, adding 70 MiB would exceed 4,812 MiB)
        ok, reason = manager.can_activate("modern_cpp", current_system_vram_mib=4780.0)
        assert ok is False
        assert "breaches hardware safety ceiling" in reason

        # Within bounds
        ok_safe, reason_safe = manager.can_activate("modern_cpp", current_system_vram_mib=4000.0)
        assert ok_safe is True

    def test_autonomous_intent_routing(self):
        manager = create_lora_adapter_manager()

        # Python routing via file extension
        route_py = manager.route_adapter(task_prompt="Refactor this module", filepaths=["src/core/main.py"])
        assert route_py == "python_core"

        # TypeScript routing via prompt keyword
        route_ts = manager.route_adapter(task_prompt="Create a React TypeScript component with strict props")
        assert route_ts == "javascript_ts"

        # Modern C++ routing via keyword
        route_cpp = manager.route_adapter(task_prompt="Implement RAII pointer management in CMake")
        assert route_cpp == "modern_cpp"

        # AST Grammar Guard routing
        route_ast = manager.route_adapter(task_prompt="Verify AST grammar and catch syntax docstring hallucination")
        assert route_ast == "ast_grammar_guard"

        # Three.js Kinematics routing
        route_three = manager.route_adapter(task_prompt="Compute quaternion kinematic joint rotation in WebGL")
        assert route_three == "threejs_kinematics"

    def test_llama_server_payload_formatting(self, tmp_path):
        manager = create_lora_adapter_manager(adapters_dir=tmp_path)
        manager.activate_adapter("python_core")

        payload = manager.format_llama_server_payload()
        assert len(payload) == 1
        entry = payload[0]
        assert entry["name"] == "python_core"
        assert entry["scale"] == 1.0
        assert entry["rank"] == 16
        assert entry["vram_mib"] == 65.0
        assert entry["path"].endswith(".gguf")


class TestQLoRATrainingPipeline:
    """Tests for the detached QLoRA training harness and GGUF exporter."""

    def test_training_pipeline_dry_run_and_gguf_export(self, tmp_path):
        config = QLoRAConfig(
            adapter_name="test_adapter",
            domain="code_test",
            output_dir=str(tmp_path),
        )
        harness = QLoRATrainingHarness(config)

        # Run pipeline
        result = harness.run_training_pipeline(dry_run=True)
        assert result["status"] == "SUCCESS"
        assert result["non_regression_verified"] is True
        assert result["regression_delta"] <= 0.05
        assert result["adapter_domain_loss"] < result["base_loss"]

        # Verify GGUF output file was written
        gguf_file = Path(result["gguf_output"])
        assert gguf_file.exists()
        assert gguf_file.stat().st_size > 0

        # Verify magic header
        with open(gguf_file, "rb") as fh:
            magic = fh.read(4)
            assert magic == b"GGUF"
