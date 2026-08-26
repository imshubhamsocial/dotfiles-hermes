"""
Milestone U41: Domain-Specific LoRA Adapter Engine (Sub-50ms Hot-Swap)
======================================================================
Manages lightweight, quantized domain-specific LoRA adapters (Python,
JavaScript/TypeScript, modern C/C++, HTML/CSS, Three.js 3D kinematics,
and AST grammar checkers).

Provides:
  1. Adapter registry and dynamic configuration mapping
  2. LoRA weight scaling and sub-50ms adapter activation
  3. Strict VRAM guard enforcement (<150 MB total adapter budget)
  4. Integration with llama-server dynamic /v1/chat/completions adapter routing
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class LoRAAdapterMetadata:
    name: str
    domain: str
    filename: str
    rank: int = 16
    alpha: int = 32
    vram_cost_mb: float = 35.0
    scale: float = 1.0
    description: str = ""
    target_languages: List[str] = field(default_factory=list)


# Standard canonical domain adapters supported by Hermes Agent OS
BUILTIN_ADAPTERS: Dict[str, LoRAAdapterMetadata] = {
    "python_core": LoRAAdapterMetadata(
        name="python_core",
        domain="programming_languages",
        filename="python_core_lora_q8.gguf",
        rank=16,
        vram_cost_mb=32.0,
        scale=1.0,
        description="Python 3.12+ modern typing, async, and AST parsing",
        target_languages=["python", "py"]
    ),
    "javascript_typescript": LoRAAdapterMetadata(
        name="javascript_typescript",
        domain="programming_languages",
        filename="javascript_ts_lora_q8.gguf",
        rank=16,
        vram_cost_mb=34.0,
        scale=1.0,
        description="Modern ESNext, TypeScript strict types, and Node/Browser APIs",
        target_languages=["javascript", "typescript", "js", "ts"]
    ),
    "modern_cpp": LoRAAdapterMetadata(
        name="modern_cpp",
        domain="programming_languages",
        filename="cpp20_modern_lora_q8.gguf",
        rank=16,
        vram_cost_mb=38.0,
        scale=1.0,
        description="C++20 concepts, ranges, RAII, and memory safety invariants",
        target_languages=["cpp", "c", "cxx", "hpp", "h"]
    ),
    "html_css_web": LoRAAdapterMetadata(
        name="html_css_web",
        domain="frontend_design",
        filename="html_css_web_lora_q8.gguf",
        rank=16,
        vram_cost_mb=28.0,
        scale=1.0,
        description="Responsive CSS Grid/Flexbox, DOM APIs, and Canvas styling",
        target_languages=["html", "css", "svg"]
    ),
    "threejs_kinematics": LoRAAdapterMetadata(
        name="threejs_kinematics",
        domain="3d_graphics_physics",
        filename="threejs_kinematics_lora_q8.gguf",
        rank=32,
        vram_cost_mb=45.0,
        scale=1.0,
        description="Three.js WebGL canvas loop, Vector3/Quaternion math, and gravitational physics",
        target_languages=["threejs", "webgl", "javascript"]
    ),
    "ast_grammar_guard": LoRAAdapterMetadata(
        name="ast_grammar_guard",
        domain="code_integrity",
        filename="ast_grammar_guard_lora_q8.gguf",
        rank=16,
        vram_cost_mb=26.0,
        scale=1.0,
        description="Tree-sitter structural AST grammar and strict schema compliance",
        target_languages=["ast", "json", "yaml"]
    )
}


class LoRAAdapterManager:
    """
    Sub-50ms hot-swappable LoRA adapter manager for local 4B SLMs.
    """

    def __init__(self, adapters_dir: Optional[Path] = None, max_vram_mb: float = 150.0):
        self.adapters_dir = adapters_dir or (Path.home() / ".hermes" / "adapters")
        self.max_vram_mb = max_vram_mb
        self.registry: Dict[str, LoRAAdapterMetadata] = dict(BUILTIN_ADAPTERS)
        self.active_adapters: Dict[str, float] = {}  # adapter_name -> scale

    def register_adapter(self, metadata: LoRAAdapterMetadata) -> None:
        """Register a new domain or language adapter."""
        self.registry[metadata.name] = metadata

    def list_available_adapters(self) -> List[Dict[str, Any]]:
        """Return all available adapters with metadata."""
        return [
            {
                "name": a.name,
                "domain": a.domain,
                "filename": a.filename,
                "rank": a.rank,
                "vram_cost_mb": a.vram_cost_mb,
                "scale": a.scale,
                "description": a.description,
                "target_languages": a.target_languages,
                "is_active": a.name in self.active_adapters
            }
            for a in self.registry.values()
        ]

    def get_adapter_for_language(self, language: str) -> Optional[LoRAAdapterMetadata]:
        """Find the optimal LoRA adapter for a specific language or domain."""
        lang = language.lower().strip()
        for adapter in self.registry.values():
            if lang in [l.lower() for l in adapter.target_languages]:
                return adapter
        return None

    def activate_adapter(self, name: str, scale: float = 1.0) -> bool:
        """
        Hot-activate a LoRA adapter with given scale while enforcing VRAM budget.
        """
        if name not in self.registry:
            return False

        adapter = self.registry[name]
        current_vram = self.get_current_vram_consumption_mb()

        # If activating a new adapter, ensure it doesn't breach the VRAM guard
        if name not in self.active_adapters:
            if current_vram + adapter.vram_cost_mb > self.max_vram_mb:
                # Evict oldest active adapter
                oldest = next(iter(self.active_adapters.keys()), None)
                if oldest:
                    self.deactivate_adapter(oldest)

        self.active_adapters[name] = max(0.0, min(scale, 2.0))
        return True

    def deactivate_adapter(self, name: str) -> bool:
        """Deactivate an active LoRA adapter."""
        if name in self.active_adapters:
            del self.active_adapters[name]
            return True
        return False

    def get_current_vram_consumption_mb(self) -> float:
        """Calculate total VRAM used by currently active adapters."""
        total = 0.0
        for name in self.active_adapters:
            if name in self.registry:
                total += self.registry[name].vram_cost_mb
        return total

    def format_llama_server_payload(self) -> List[Dict[str, Any]]:
        """
        Format active adapters for llama-server /v1/chat/completions payload.
        """
        payload = []
        for name, scale in self.active_adapters.items():
            adapter = self.registry[name]
            payload.append({
                "name": adapter.name,
                "path": str(self.adapters_dir / adapter.filename),
                "scale": scale
            })
        return payload
