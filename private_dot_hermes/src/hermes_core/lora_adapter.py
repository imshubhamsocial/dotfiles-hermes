"""
Hermes LoRA Adapter Manager & Dynamic Runtime Routing (Milestone U41 & Track 4.2)
=================================================================================
Provides dynamic routing, lifecycle management, and strict VRAM-guarded hot-swapping
for task-specific Low-Rank Adapters (LoRA) on top of the base Gemma 4 model.

Enforces:
1. Strict Per-Adapter VRAM Guard: Active adapter must not exceed 150 MiB.
2. Global VRAM Guard: Combined VRAM (base model + KV cache + active adapter) <= 4,812 MiB.
3. Single Active Domain Adapter Invariant: Swaps out previous adapter to eliminate VRAM creep.
4. Autonomous Intent Routing: Directs tasks to specialized adapters based on file AST and prompt signals.
5. llama.cpp / llama-server API Compatibility: Serializes hot-swap requests for runtime injection.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MAX_ADAPTER_VRAM_MIB = 150.0       # Strict per-adapter limit (<150 MB)
HARDWARE_VRAM_CEILING_MIB = 4812.0  # Hardware safety ceiling on RTX 3050 (6144 MiB physical)
DEFAULT_ADAPTER_DIR = Path.home() / ".hermes" / "adapters"


@dataclass
class LoRAAdapterSpec:
    """Specification and resource profile for a domain-specific LoRA adapter."""
    name: str
    domain: str                          # e.g. "code_python", "web_ts", "systems_cpp", "ast_guard"
    description: str
    rank: int = 16
    alpha: int = 32
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"])
    estimated_vram_mib: float = 65.0     # Typical footprint for Gemma 4 E4B r=16 adapter
    gguf_filename: str = ""
    file_extensions: List[str] = field(default_factory=list)
    trigger_keywords: List[str] = field(default_factory=list)
    active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "rank": self.rank,
            "alpha": self.alpha,
            "target_modules": self.target_modules,
            "estimated_vram_mib": self.estimated_vram_mib,
            "gguf_filename": self.gguf_filename,
            "file_extensions": self.file_extensions,
            "trigger_keywords": self.trigger_keywords,
            "active": self.active,
        }


# Canonical domain adapters pre-registered in Hermes Agent OS
BUILTIN_ADAPTER_SPECS: Dict[str, LoRAAdapterSpec] = {
    "python_core": LoRAAdapterSpec(
        name="python_core",
        domain="code_python",
        description="Python 3.13 standard, typing, AST manipulations, and async uvloop patterns.",
        rank=16,
        alpha=32,
        estimated_vram_mib=65.0,
        gguf_filename="hermes-python-core-qlora-f16.gguf",
        file_extensions=[".py", ".pyi"],
        trigger_keywords=["python", "pytest", "pydantic", "dataclass", "asyncio", "ast"],
    ),
    "javascript_ts": LoRAAdapterSpec(
        name="javascript_ts",
        domain="web_ts",
        description="Modern TypeScript/ESM architecture, Node.js 22 runtime, and strict type narrowing.",
        rank=16,
        alpha=32,
        estimated_vram_mib=62.0,
        gguf_filename="hermes-javascript-ts-qlora-f16.gguf",
        file_extensions=[".ts", ".tsx", ".js", ".jsx", ".mjs"],
        trigger_keywords=["typescript", "javascript", "react", "node", "npm", "esm", "vite"],
    ),
    "modern_cpp": LoRAAdapterSpec(
        name="modern_cpp",
        domain="systems_cpp",
        description="C++20 concepts, RAII, zero-cost abstractions, CMake, and memory-safe idioms.",
        rank=16,
        alpha=32,
        estimated_vram_mib=70.0,
        gguf_filename="hermes-modern-cpp-qlora-f16.gguf",
        file_extensions=[".cpp", ".hpp", ".cc", ".cxx", ".h"],
        trigger_keywords=["c++", "cpp", "cmake", "raii", "pointer", "template", "valgrind"],
    ),
    "ast_grammar_guard": LoRAAdapterSpec(
        name="ast_grammar_guard",
        domain="ast_guard",
        description="Formal AST syntax verification, docstring claim validation, and anti-hallucination checks.",
        rank=16,
        alpha=32,
        estimated_vram_mib=58.0,
        gguf_filename="hermes-ast-guard-qlora-f16.gguf",
        file_extensions=[".py", ".json", ".yaml"],
        trigger_keywords=["grammar", "ast", "syntax_gate", "docstring", "proposition", "linter"],
    ),
    "threejs_kinematics": LoRAAdapterSpec(
        name="threejs_kinematics",
        domain="graphics_webgl",
        description="Three.js WebGL rendering, kinematic joint hierarchies, quaternions, and canvas shading.",
        rank=16,
        alpha=32,
        estimated_vram_mib=68.0,
        gguf_filename="hermes-threejs-kinematics-qlora-f16.gguf",
        file_extensions=[".js", ".ts", ".html"],
        trigger_keywords=["threejs", "webgl", "quaternion", "mesh", "kinematics", "shader", "canvas"],
    ),
}


class LoRAAdapterManager:
    """
    Manages LoRA adapter discovery, intent routing, VRAM safety bounds,
    and hot-swapping execution.
    """

    def __init__(
        self,
        adapters_dir: Optional[Path] = None,
        max_adapter_vram_mib: float = MAX_ADAPTER_VRAM_MIB,
        hardware_vram_ceiling_mib: float = HARDWARE_VRAM_CEILING_MIB,
    ):
        self.adapters_dir = Path(adapters_dir) if adapters_dir else DEFAULT_ADAPTER_DIR
        self.max_adapter_vram_mib = max_adapter_vram_mib
        self.hardware_vram_ceiling_mib = hardware_vram_ceiling_mib
        self._registry: Dict[str, LoRAAdapterSpec] = {
            k: LoRAAdapterSpec(**vars(v)) for k, v in BUILTIN_ADAPTER_SPECS.items()
        }
        self._active_adapter_name: Optional[str] = None

    def register_adapter(self, spec: LoRAAdapterSpec) -> bool:
        """Registers or updates an adapter spec after validating VRAM budget."""
        if spec.estimated_vram_mib > self.max_adapter_vram_mib:
            raise ValueError(
                f"Adapter '{spec.name}' exceeds VRAM guard: "
                f"{spec.estimated_vram_mib} MiB > {self.max_adapter_vram_mib} MiB ceiling."
            )
        self._registry[spec.name] = spec
        return True

    def get_adapter(self, name: str) -> Optional[LoRAAdapterSpec]:
        return self._registry.get(name)

    def list_adapters(self) -> List[LoRAAdapterSpec]:
        return list(self._registry.values())

    def get_active_adapter(self) -> Optional[LoRAAdapterSpec]:
        if self._active_adapter_name:
            return self._registry.get(self._active_adapter_name)
        return None

    def can_activate(
        self,
        name: str,
        current_system_vram_mib: float = 0.0,
    ) -> Tuple[bool, str]:
        """
        Validates whether the requested adapter can be safely loaded without
        breaching per-adapter limit or global hardware ceiling.
        """
        spec = self._registry.get(name)
        if not spec:
            return False, f"Unknown adapter '{name}'"

        if spec.estimated_vram_mib > self.max_adapter_vram_mib:
            return False, (
                f"Adapter '{name}' VRAM ({spec.estimated_vram_mib} MiB) "
                f"exceeds per-adapter limit ({self.max_adapter_vram_mib} MiB)"
            )

        projected_total = current_system_vram_mib + spec.estimated_vram_mib
        if projected_total > self.hardware_vram_ceiling_mib:
            return False, (
                f"Projected total VRAM ({projected_total:.1f} MiB) breaches "
                f"hardware safety ceiling ({self.hardware_vram_ceiling_mib:.1f} MiB)"
            )

        return True, "Safe to activate"

    def activate_adapter(
        self,
        name: str,
        current_system_vram_mib: float = 0.0,
    ) -> Tuple[bool, str]:
        """
        Activates the specified adapter while deactivating any previously active adapter
        (Single Active Adapter Invariant).
        """
        can_load, reason = self.can_activate(name, current_system_vram_mib)
        if not can_load:
            return False, reason

        # Deactivate previous active adapter
        if self._active_adapter_name and self._active_adapter_name in self._registry:
            self._registry[self._active_adapter_name].active = False

        self._registry[name].active = True
        self._active_adapter_name = name
        return True, f"Adapter '{name}' activated successfully"

    def deactivate_all(self) -> None:
        """Deactivates all adapters, resetting model to pure base state."""
        for spec in self._registry.values():
            spec.active = False
        self._active_adapter_name = None

    def route_adapter(
        self,
        task_prompt: str = "",
        filepaths: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Determines the optimal domain adapter to activate based on file AST extensions
        and prompt intent keywords.
        """
        filepaths = filepaths or []
        scores: Dict[str, int] = {k: 0 for k in self._registry}

        # 1. Route by file extensions
        for fp in filepaths:
            ext = Path(fp).suffix.lower()
            for name, spec in self._registry.items():
                if ext in spec.file_extensions:
                    scores[name] += 3

        # 2. Route by trigger keywords in prompt
        prompt_lower = task_prompt.lower()
        for name, spec in self._registry.items():
            for kw in spec.trigger_keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", prompt_lower):
                    scores[name] += 2

        best_name = None
        best_score = 0
        for name, score in scores.items():
            if score > best_score:
                best_score = score
                best_name = name

        return best_name if best_score > 0 else None

    def format_llama_server_payload(self) -> List[Dict[str, Any]]:
        """
        Generates the standard payload for llama-server /lora-adapters endpoint.
        Returns a list of adapter activation descriptors.
        """
        active_spec = self.get_active_adapter()
        if not active_spec:
            return []
        return [
            {
                "name": active_spec.name,
                "path": str(self.adapters_dir / active_spec.gguf_filename),
                "scale": 1.0,
                "rank": active_spec.rank,
                "vram_mib": active_spec.estimated_vram_mib,
            }
        ]


def create_lora_adapter_manager(
    adapters_dir: Optional[Path] = None,
    max_adapter_vram_mib: float = MAX_ADAPTER_VRAM_MIB,
) -> LoRAAdapterManager:
    """Factory helper to instantiate a configured LoRAAdapterManager."""
    return LoRAAdapterManager(
        adapters_dir=adapters_dir,
        max_adapter_vram_mib=max_adapter_vram_mib,
    )
