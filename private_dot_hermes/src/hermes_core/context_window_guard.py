"""
Context Window Guard & Invariant R5-5 VRAM Validator (Milestone U65)
====================================================================
Evaluates and validates context window expansion (128K target) against the
hard physical VRAM ceiling (<= 4,812 MiB on NVIDIA RTX 3050 6GB).

Implements empirical tier evaluation:
  Option A: 131,072 (Native 128K Default)
  Option B: 98,304  (96K Fallback)
  Option C: 65,536  (64K Baseline)
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import yaml


HARD_VRAM_CEILING_MIB = 4812
CONTEXT_OPTIONS = [131072, 98304, 65536]


@dataclass
class ContextVRAMAssessment:
    context_tokens: int
    estimated_kv_mib: float
    estimated_total_vram_mib: float
    headroom_mib: float
    safe: bool
    requires_flash_attn: bool
    recommendation: str


class ContextWindowGuard:
    """Evaluates context capacity and applies safe configuration updates."""

    def __init__(self, vram_ceiling_mib: int = HARD_VRAM_CEILING_MIB):
        self.ceiling = vram_ceiling_mib
        # Gemma-4-E4B architecture constants: 18 layers, 4 kv heads, 256 head_dim
        self.num_layers = 18
        self.num_kv_heads = 4
        self.head_dim = 256
        self.model_weights_mib = 2540.0
        # Hybrid attention discount: Gemma-4 uses sliding-window on majority layers
        self.hybrid_attn_ratio = 0.70

    def estimate_vram(self, context_tokens: int, kv_quant: str = "q4_0", slots: int = 2) -> ContextVRAMAssessment:
        bytes_per_el = 0.5 if kv_quant in ("q4_0", "q4_1") else 1.0 if kv_quant in ("q8_0", "q8_1") else 2.0
        # Full dense KV bytes per slot
        full_kv_bytes = 2 * self.num_layers * self.num_kv_heads * self.head_dim * context_tokens * bytes_per_el
        # Hybrid attention effective KV cache
        hybrid_kv_bytes = full_kv_bytes * self.hybrid_attn_ratio
        kv_mib = (hybrid_kv_bytes * slots) / (1024 * 1024)

        total_vram = self.model_weights_mib + kv_mib
        headroom = self.ceiling - total_vram
        is_safe = headroom >= 150.0  # Require >= 150 MiB margin

        if is_safe:
            rec = f"APPROVED: Safe with {headroom:.1f} MiB headroom."
        else:
            rec = f"BLOCKED: Exceeds safety margin ({headroom:.1f} MiB). Fall back to next lower tier."

        return ContextVRAMAssessment(
            context_tokens=context_tokens,
            estimated_kv_mib=kv_mib,
            estimated_total_vram_mib=total_vram,
            headroom_mib=headroom,
            safe=is_safe,
            requires_flash_attn=context_tokens > 32768,
            recommendation=rec,
        )

    def select_best_safe_context(self, slots: int = 2) -> int:
        for opt in CONTEXT_OPTIONS:
            assessment = self.estimate_vram(opt, slots=slots)
            if assessment.safe:
                return opt
        return 65536

    def read_live_gpu_vram(self) -> Optional[int]:
        """Query nvidia-smi for current allocated VRAM in MiB."""
        try:
            cmd = ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"]
            out = subprocess.check_output(cmd, text=True).strip()
            return int(out.splitlines()[0])
        except Exception:
            return None

    def update_config_context_length(self, config_path: Path, context_length: int) -> bool:
        if not config_path.exists():
            return False
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            data["context_length"] = context_length
            if "auxiliary" in data and "compression" in data["auxiliary"]:
                data["auxiliary"]["compression"]["context_length"] = context_length

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False)
            return True
        except Exception:
            return False


def create_context_window_guard() -> ContextWindowGuard:
    return ContextWindowGuard()
