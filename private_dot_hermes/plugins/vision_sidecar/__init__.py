"""
Hermes Plugin: vision_sidecar
=============================
Production Multimodal Vision Sidecar for Hermes Agent OS.
Binds to local llama-server on port 8139 running SmolVLM2-256M-Video-Instruct (GGUF + mmproj)
in 100% CPU mode (0 MB GPU VRAM overhead) to provide:
  - High-precision visual reasoning & scene description.
  - UI coordinate and actionable control grounding.
  - Architecture diagram / flowchart parsing into Mermaid.
  - Seamless multimodal context injection into agent prompts.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import sys
hermes_core = Path.home() / ".hermes/hermes-agent"
if str(hermes_core) not in sys.path:
    sys.path.insert(0, str(hermes_core))

from agent.core.vision_engine import (
    VisionEngine,
    VisionServerSupervisor,
    get_vision_engine,
)
from agent.core.vision_context import (
    MultimodalContextInjector,
    get_context_injector,
)

logger = logging.getLogger("hermes.plugin.vision_sidecar")
VISION_ENDPOINT = os.environ.get("HERMES_VISION_ENDPOINT", "http://127.0.0.1:8139/v1/chat/completions")


class VisionSidecarClient:
    """Production client for local vision inference on port 8139."""

    def __init__(self, endpoint: str = VISION_ENDPOINT):
        self.endpoint = endpoint
        self.engine = get_vision_engine()
        self.context_injector = get_context_injector()

    def is_alive(self, timeout: float = 1.0) -> bool:
        return self.engine.supervisor.is_healthy(timeout=timeout)

    def inspect_image(self, image_path: Path | str, prompt: str = "Describe this image in detail.") -> Dict[str, Any]:
        return self.engine.describe_image(image_path, prompt=prompt)

    def analyze_ui(self, image_path: Path | str, query: str = "Locate all actionable UI elements: buttons, input fields, navigation links, and menus.") -> Dict[str, Any]:
        return self.engine.analyze_ui(image_path, query=query)

    def extract_diagram(self, image_path: Path | str) -> Dict[str, Any]:
        return self.engine.extract_diagram_structure(image_path)

    def inject_context(self, prompt: str) -> Tuple[str, List[Dict[str, Any]]]:
        return self.context_injector.inject_visual_context(prompt)


def register(ctx=None):
    client = VisionSidecarClient()
    alive = client.is_alive()
    print(f"[vision_sidecar] Multimodal Vision sidecar registered. Port 8139 active: {alive}")
    if ctx and hasattr(ctx, "register_tool"):
        ctx.register_tool("vision_describe", client.inspect_image)
        ctx.register_tool("vision_analyze_ui", client.analyze_ui)
        ctx.register_tool("vision_extract_diagram", client.extract_diagram)
        ctx.register_tool("vision_inject_context", client.inject_context)
    return True


__all__ = [
    "VisionSidecarClient",
    "VisionEngine",
    "MultimodalContextInjector",
    "get_vision_engine",
    "get_context_injector",
    "register",
]
