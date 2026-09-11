"""
Hermes Plugin: cua_bridge
=========================
Computer-Use Automation (CUA) Driver Bridge for Hermes.
Binds to ~/.cua-driver/packages/releases/0.21.0-x86_64-unknown-linux-gnu/cua-driver
and agent.core.cua_controller to expose desktop observation, mouse/keyboard interaction,
AT-SPI tree inspection, browser navigation loop, and sandboxed terminal execution
safely through Hermes Agent OS.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import Core CUA Controller
import sys
core_path = Path.home() / ".hermes/hermes-agent"
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from agent.core.cua_controller import (
    CUAController,
    BrowserAutomationLoop,
    TerminalCUA,
    get_cua_controller,
)

CUA_DRIVER_PATH = Path.home() / ".cua-driver" / "packages" / "releases" / "0.21.0-x86_64-unknown-linux-gnu" / "cua-driver"


class CUADriverBridge:
    """Interface to local cua-driver CLI/MCP subsystem and CUAController."""

    def __init__(self, binary_path: Optional[Path] = None):
        self.binary_path = binary_path or CUA_DRIVER_PATH
        self.controller = get_cua_controller()

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

    def get_screen_size(self) -> Tuple[int, int]:
        return self.controller.get_screen_size()

    def get_accessibility_tree(self) -> Dict[str, Any]:
        return self.controller.get_accessibility_tree()

    def get_desktop_state(self) -> Dict[str, Any]:
        return self.controller.take_screenshot()

    def take_screenshot(self, output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        return self.controller.take_screenshot(output_path=output_path)

    def click(self, x: int, y: int, button: str = "left") -> bool:
        return self.controller.click_element(x, y, button=button)

    def type(self, text: str) -> bool:
        return self.controller.type_text(text)

    def press(self, key: str) -> bool:
        return self.controller.press_key(key)

    def scroll(self, direction: str = "down", amount: int = 3) -> bool:
        return self.controller.scroll(direction=direction, amount=amount)

    def find_element(self, description: str, template_path: Optional[str] = None) -> Dict[str, Any]:
        return self.controller.find_element_by_description(description, template_path=template_path)

    def run_browser_loop(self, url: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        loop = BrowserAutomationLoop(self.controller)
        return loop.run_navigation_task(url, steps)

    def run_terminal_cua(self, command: str, timeout_sec: int = 120) -> Dict[str, Any]:
        tcua = TerminalCUA()
        return tcua.execute(command, timeout_sec=timeout_sec)


def register(ctx=None):
    bridge = CUADriverBridge()
    available = bridge.is_available()
    print(f"[cua_bridge] Computer-Use Automation Driver registered. Available: {available}")
    if ctx and hasattr(ctx, "register_tool"):
        ctx.register_tool("cua_take_screenshot", bridge.take_screenshot)
        ctx.register_tool("cua_click", bridge.click)
        ctx.register_tool("cua_type", bridge.type)
        ctx.register_tool("cua_scroll", bridge.scroll)
        ctx.register_tool("cua_find_element", bridge.find_element)
        ctx.register_tool("cua_browser_loop", bridge.run_browser_loop)
        ctx.register_tool("cua_terminal", bridge.run_terminal_cua)
    return True


__all__ = [
    "CUADriverBridge",
    "CUAController",
    "BrowserAutomationLoop",
    "TerminalCUA",
    "get_cua_controller",
    "register",
]
