"""
Hermes Agent: Multimodal Context Injection Layer (Phase VI)
===========================================================
Automatically scans agent prompts and dialogue turns for image attachments,
screenshots, and diagram files, executes multimodal inspection via VisionEngine,
and injects structured visual grounding blocks into model context.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from agent.core.vision_engine import VisionEngine, get_vision_engine
except (ImportError, ModuleNotFoundError):
    from vision_engine import VisionEngine, get_vision_engine

logger = logging.getLogger("hermes.core.vision_context")

# Common image path regex pattern
IMAGE_PATH_PATTERN = re.compile(
    r"(?:^|\s)(/(?:[a-zA-Z0-9_.-]+/)+[a-zA-Z0-9_.-]+\.(?:png|jpg|jpeg|webp|bmp|gif))(?=\s|$|[.,;:!?])",
    re.IGNORECASE,
)


class MultimodalContextInjector:
    """Scans conversation context for visual references and injects grounded descriptions."""

    def __init__(self, vision_engine: Optional[VisionEngine] = None):
        self.vision_engine = vision_engine or get_vision_engine()

    def extract_image_paths(self, text: str) -> List[Path]:
        """Find valid on-disk image file paths referenced in prompt text."""
        matches = IMAGE_PATH_PATTERN.findall(text)
        valid_paths = []
        for m in matches:
            p = Path(m).expanduser().resolve()
            if p.exists() and p.is_file():
                valid_paths.append(p)
        return valid_paths

    def inject_visual_context(
        self,
        prompt: str,
        explicit_images: Optional[List[Union[str, Path]]] = None,
        max_image_tokens: int = 512,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Scan prompt for image paths or explicit attachments, describe via VisionEngine,
        and inject structured visual observations into the prompt context.
        """
        found_images = self.extract_image_paths(prompt)
        if explicit_images:
            for exp in explicit_images:
                ep = Path(exp).expanduser().resolve()
                if ep.exists() and ep not in found_images:
                    found_images.append(ep)

        if not found_images:
            return prompt, []

        injected_records: List[Dict[str, Any]] = []
        visual_blocks: List[str] = ["\n--- [MULTIMODAL VISUAL GROUNDING] ---"]

        for img_path in found_images[:3]:  # Bound to max 3 images per turn
            try:
                desc_res = self.vision_engine.describe_image(img_path)
                if desc_res.get("success"):
                    text_desc = desc_res.get("text", "").strip()
                    dims = desc_res.get("dimensions", {})
                    dim_str = f"{dims.get('width', 0)}x{dims.get('height', 0)}"

                    # Check for diagram / UI keywords
                    is_diagram = any(k in prompt.lower() or k in text_desc.lower() for k in ["diagram", "flowchart", "graph", "architecture"])
                    diagram_mermaid = ""
                    if is_diagram:
                        diag_res = self.vision_engine.extract_diagram_structure(img_path)
                        if diag_res.get("mermaid"):
                            diagram_mermaid = "\nStructured Diagram:\n" + diag_res["mermaid"]

                    block = (
                        f"Image: {img_path.name} ({dim_str})\n"
                        f"Visual Analysis: {text_desc}"
                        f"{diagram_mermaid}"
                    )
                    visual_blocks.append(block)
                    injected_records.append({
                        "path": str(img_path),
                        "dimensions": dims,
                        "description": text_desc,
                        "is_diagram": is_diagram,
                    })
            except Exception as e:
                logger.warning("Failed to inject visual context for %s: %s", img_path, e)

        visual_blocks.append("--- [END VISUAL GROUNDING] ---\n")
        augmented_prompt = "\n".join(visual_blocks) + "\n" + prompt
        return augmented_prompt, injected_records


# Global Singleton
_GLOBAL_CONTEXT_INJECTOR: Optional[MultimodalContextInjector] = None


def get_context_injector() -> MultimodalContextInjector:
    """Retrieve shared global MultimodalContextInjector instance."""
    global _GLOBAL_CONTEXT_INJECTOR
    if _GLOBAL_CONTEXT_INJECTOR is None:
        _GLOBAL_CONTEXT_INJECTOR = MultimodalContextInjector()
    return _GLOBAL_CONTEXT_INJECTOR


__all__ = [
    "MultimodalContextInjector",
    "get_context_injector",
]
