"""
Hermes Plugin: cua_bridge
=========================
Computer-Use Automation (CUA) Driver Bridge for Hermes.
Binds to ~/.cua-driver/packages/releases/0.21.0-x86_64-unknown-linux-gnu/cua-driver
to expose desktop observation, mouse/keyboard interaction, AT-SPI tree inspection,
and autonomous UI navigation safely through Hermes Agent OS.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


CUA_DRIVER_PATH = Path.home() / ".cua-driver" / "packages" / "releases" / "0.21.0-x86_64-unknown-linux-gnu" / "cua-driver"


class CUADriverBridge:
    """Interface to local cua-driver CLI/MCP subsystem."""

    def __init__(self, binary_path: Optional[Path] = None):
        self.binary_path = binary_path or CUA_DRIVER_PATH

    def is_available(self) -> bool:
        return self.binary_path.exists() and os.access(self.binary_path, os.X_OK)

    def run_cmd(self, args: List[str], timeout: float = 15.0) -> Dict[str, Any]:
        if not self.is_available():
            return {"success": False, "error": f"cua-driver not found at {self.binary_path}"}
        cmd = [str(self.binary_path)] + args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "success": res.returncode == 0,
                "returncode": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_screen_size(self) -> Dict[str, Any]:
        return self.run_cmd(["call", "get_screen_size"])

    def get_accessibility_tree(self) -> Dict[str, Any]:
        return self.run_cmd(["call", "get_accessibility_tree"])

    def get_desktop_state(self) -> Dict[str, Any]:
        return self.run_cmd(["call", "get_desktop_state"])


def register(ctx=None):
    bridge = CUADriverBridge()
    available = bridge.is_available()
    print(f"[cua_bridge] Computer-Use Automation Driver registered. Available: {available}")
    return True


__all__ = ["CUADriverBridge", "register"]
