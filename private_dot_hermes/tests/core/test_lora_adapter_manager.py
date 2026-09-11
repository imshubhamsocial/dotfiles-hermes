"""
Contract & Unit Tests for LoRA Adapter Specifications & QLoRA Fine-Tuning
========================================================================
Verifies:
1. Domain adapter registration and metadata specs (rank=16, alpha=32).
2. Strict VRAM guard (<150 MiB) and hardware envelope ceiling (<= 4,812 MiB).
3. Single Active Adapter Invariant (automatic hot-swap deactivation).
4. Llama-server /lora-adapters hot-swap payload formatting.
5. QLoRA training pipeline non-regression verification and GGUF export.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
import pytest

MAX_ADAPTER_VRAM_MIB = 150.0
HARDWARE_VRAM_CEILING_MIB = 4812.0

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from train_qlora_adapter import QLoRAConfig, QLoRATrainingHarness


@dataclass
class LoRAAdapterSpec:
    name: str
    domain: str
    description: str = ""
    rank: int = 16
    alpha: int = 32
    target_modules: list[str] = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"])
    estimated_vram_mib: float = 65.0
    active: bool = False


BUILTIN_ADAPTER_SPECS = [
    LoRAAdapterSpec("python_core", "python", "Python AST & typing", estimated_vram_mib=65.0),
    LoRAAdapterSpec("javascript_ts", "javascript", "TypeScript & React", estimated_vram_mib=72.0),
    LoRAAdapterSpec("modern_cpp", "cpp", "Modern C++20", estimated_vram_mib=70.0),
    LoRAAdapterSpec("ast_grammar_guard", "safety", "AST syntax guard", estimated_vram_mib=45.0),
    LoRAAdapterSpec("threejs_kinematics", "webgl", "Three.js kinematics", estimated_vram_mib=58.0),
]


class LoRAAdapterManager:
    """Thin manager enforcing adapter VRAM bounds and single-active invariant."""

    def __init__(self, adapters_dir: Path | None = None):
        self.adapters_dir = adapters_dir or Path("/dev/shm/adapters")
        self._adapters: dict[str, LoRAAdapterSpec] = {s.name: s for s in BUILTIN_ADAPTER_SPECS}

    def list_adapters(self) -> list[LoRAAdapterSpec]:
        return list(self._adapters.values())

    def get_adapter(self, name: str) -> LoRAAdapterSpec | None:
        return self._adapters.get(name)

    def get_active_adapter(self) -> LoRAAdapterSpec | None:
        for a in self._adapters.values():
            if a.active:
                return a
        return None

    def register_adapter(self, spec: LoRAAdapterSpec) -> None:
        if spec.estimated_vram_mib >= MAX_ADAPTER_VRAM_MIB:
            raise ValueError(f"exceeds VRAM guard: {spec.estimated_vram_mib} >= {MAX_ADAPTER_VRAM_MIB}")
        self._adapters[spec.name] = spec

    def can_activate(self, name: str, current_system_vram_mib: float) -> tuple[bool, str]:
        spec = self._adapters.get(name)
        if not spec:
            return False, "adapter not found"
        if current_system_vram_mib + spec.estimated_vram_mib > HARDWARE_VRAM_CEILING_MIB:
            return False, "breaches hardware safety ceiling"
        return True, "ok"

    def activate_adapter(self, name: str, current_system_vram_mib: float = 3000.0) -> tuple[bool, str]:
        ok, reason = self.can_activate(name, current_system_vram_mib)
        if not ok:
            return False, reason
        for a in self._adapters.values():
            a.active = False
        self._adapters[name].active = True
        return True, "activated"

    def deactivate_all(self) -> None:
        for a in self._adapters.values():
            a.active = False

    def format_llama_server_payload(self) -> list[dict]:
        active = self.get_active_adapter()
        if not active:
            return []
        return [{
            "name": active.name,
            "scale": 1.0,
            "rank": active.rank,
            "vram_mib": active.estimated_vram_mib,
            "path": str(self.adapters_dir / f"{active.name}.gguf"),
        }]


class TestLoRAAdapterManager:
    """Core tests for LoRA Adapter Manager and runtime routing."""

    def test_builtin_adapter_specs_and_vram_limits(self):
        manager = LoRAAdapterManager()
        adapters = manager.list_adapters()
        assert len(adapters) >= 5

        for spec in adapters:
            assert spec.estimated_vram_mib < MAX_ADAPTER_VRAM_MIB
            assert spec.rank == 16
            assert spec.alpha == 32
            assert len(spec.target_modules) > 0

    def test_adapter_registration_vram_rejection(self):
        manager = LoRAAdapterManager()
        bloated_spec = LoRAAdapterSpec(
            name="bloated_adapter",
            domain="test",
            description="Exceeds VRAM guard",
            estimated_vram_mib=200.0,
        )
        with pytest.raises(ValueError, match="exceeds VRAM guard"):
            manager.register_adapter(bloated_spec)

    def test_single_active_adapter_and_hot_swapping(self):
        manager = LoRAAdapterManager()
        assert manager.get_active_adapter() is None

        ok, _ = manager.activate_adapter("python_core", current_system_vram_mib=3200.0)
        assert ok is True
        active = manager.get_active_adapter()
        assert active is not None and active.name == "python_core"

        ok2, _ = manager.activate_adapter("javascript_ts", current_system_vram_mib=3200.0)
        assert ok2 is True
        new_active = manager.get_active_adapter()
        assert new_active is not None and new_active.name == "javascript_ts"
        assert manager.get_adapter("python_core").active is False

        manager.deactivate_all()
        assert manager.get_active_adapter() is None

    def test_hardware_vram_ceiling_guard(self):
        manager = LoRAAdapterManager()
        ok, reason = manager.can_activate("modern_cpp", current_system_vram_mib=4780.0)
        assert ok is False
        assert "breaches hardware safety ceiling" in reason

        ok_safe, _ = manager.can_activate("modern_cpp", current_system_vram_mib=4000.0)
        assert ok_safe is True

    def test_llama_server_payload_formatting(self, tmp_path):
        manager = LoRAAdapterManager(adapters_dir=tmp_path)
        manager.activate_adapter("python_core")
        payload = manager.format_llama_server_payload()
        assert len(payload) == 1
        entry = payload[0]
        assert entry["name"] == "python_core"
        assert entry["scale"] == 1.0
        assert entry["rank"] == 16
        assert entry["path"].endswith(".gguf")


class TestQLoRATrainingPipeline:
    """Tests for detached QLoRA training harness and GGUF exporter."""

    def test_training_pipeline_dry_run_and_gguf_export(self, tmp_path):
        config = QLoRAConfig(
            adapter_name="test_adapter",
            domain="code_test",
            output_dir=str(tmp_path),
        )
        harness = QLoRATrainingHarness(config)
        result = harness.run_training_pipeline(dry_run=True)
        assert result["status"] == "SUCCESS"
        assert result["non_regression_verified"] is True
        assert result["regression_delta"] <= 0.05
        assert result["adapter_domain_loss"] < result["base_loss"]

        gguf_file = Path(result["gguf_output"])
        assert gguf_file.exists()
        assert gguf_file.stat().st_size > 0
        with open(gguf_file, "rb") as fh:
            magic = fh.read(4)
            assert magic == b"GGUF"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
