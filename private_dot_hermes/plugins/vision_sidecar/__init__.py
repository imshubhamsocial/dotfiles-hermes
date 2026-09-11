"""
Hermes Plugin: vision_sidecar
=============================
Connects Hermes to a local or containerized vision model daemon on port 8139
(e.g., moondream2 or llava via llama-server / ollama) to enable multimodal visual reasoning,
screenshot analysis, and UI coordinate grounding without bloating the main code SLM context.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


VISION_ENDPOINT = os.environ.get("HERMES_VISION_ENDPOINT", "http://127.0.0.1:8139/v1/chat/completions")


class VisionSidecarClient:
    """Client for local vision inference on port 8139."""

    def __init__(self, endpoint: str = VISION_ENDPOINT):
        self.endpoint = endpoint

    def is_alive(self, timeout: float = 1.0) -> bool:
        health_url = self.endpoint.replace("/v1/chat/completions", "/health")
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "hermes-vision"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    def inspect_image(self, image_path: Path | str, prompt: str = "Describe this image in detail.") -> Dict[str, Any]:
        target = Path(image_path).resolve()
        if not target.exists():
            return {"success": False, "error": f"Image file not found: {target}"}

        try:
            raw_bytes = target.read_bytes()
            b64_data = base64.b64encode(raw_bytes).decode("utf-8")
        except Exception as e:
            return {"success": False, "error": f"Failed to encode image: {e}"}

        payload = {
            "model": "moondream",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                    ]
                }
            ],
            "max_tokens": 512,
            "temperature": 0.1
        }

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "hermes-vision"}
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                choice = res_data.get("choices", [{}])[0]
                text = choice.get("message", {}).get("content", "")
                return {"success": True, "description": text}
        except urllib.error.URLError:
            return {
                "success": False,
                "error": f"Vision sidecar offline at {self.endpoint}. Start server on port 8139.",
                "offline": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def register(ctx=None):
    client = VisionSidecarClient()
    alive = client.is_alive()
    print(f"[vision_sidecar] Vision sidecar plugin registered. Port 8139 active: {alive}")
    return True


__all__ = ["VisionSidecarClient", "register"]
