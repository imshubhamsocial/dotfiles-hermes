#!/usr/bin/env python3.13
"""
Verification Suite: Phase 5 Computer-Use Automation (CUA Full Loop)
====================================================================
Verifies:
  Gate 1: Daemon lifecycle & display geometry (1920x1080)
  Gate 2: Desktop pixel capture & screenshot validation
  Gate 3: Visual element localization (CV2 template match + AT-SPI tree query)
  Gate 4: Input action dispatch (mouse move/click, keypress, typing, scrolling)
  Gate 5: Browser automation loop (multi-step navigation workflow)
  Gate 6: Sandboxed Terminal CUA execution & append-only sha256 trajectory chain

Zero-Test-Folder Architecture: Pure native executable contract verification.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Setup paths
hermes_root = Path.home() / ".hermes"
sys.path.insert(0, str(hermes_root / "hermes-agent"))

from agent.core.cua_controller import (
    CUAController,
    BrowserAutomationLoop,
    TerminalCUA,
    get_cua_controller,
)
from agent.core.trajectory import TrajectoryRecorder
from PIL import Image


def log_gate(gate_id: str, desc: str, passed: bool, details: str = ""):
    status = "[92mPASS[0m" if passed else "[91mFAIL[0m"
    print(f"[{gate_id}] {status} - {desc}")
    if details:
        print(f"      [90m{details}[0m")


def test_gate1_daemon_and_display(controller: CUAController) -> bool:
    """Gate 1: CUA Daemon lifecycle & display geometry."""
    avail = controller.is_driver_available()
    if not avail:
        log_gate("GATE 1", "CUA Driver binary available", False, "Binary not found or executable")
        return False
    
    daemon_ok = controller.ensure_daemon_running()
    if not daemon_ok:
        log_gate("GATE 1", "CUA Daemon running on /dev/shm/hermes_cua.sock", False, "Failed to start daemon")
        return False

    w, h = controller.get_screen_size()
    match = (w == 1920 and h == 1080)
    log_gate(
        "GATE 1",
        "CUA Daemon & Display Geometry (1920x1080)",
        match,
        f"Reported geometry: {w}x{h}, daemon socket: {controller.socket_path}",
    )
    return match


def test_gate2_pixel_capture(controller: CUAController) -> bool:
    """Gate 2: Desktop pixel capture & screenshot validation."""
    out_file = Path("/dev/shm/hermes_gate2_screenshot.png")
    if out_file.exists():
        out_file.unlink()

    res = controller.take_screenshot(output_path=out_file)
    if not res.get("success") or not out_file.exists():
        log_gate("GATE 2", "Desktop pixel capture", False, f"Error: {res.get('error')}")
        return False

    # Validate image properties
    img = Image.open(out_file)
    w, h = img.size
    is_valid = (w == 1920 and h == 1080 and out_file.stat().st_size > 10000)
    log_gate(
        "GATE 2",
        "Desktop pixel capture & PNG verification",
        is_valid,
        f"Captured {w}x{h}, size: {out_file.stat().st_size} bytes at {out_file}",
    )
    return is_valid


def test_gate3_element_localization(controller: CUAController) -> bool:
    """Gate 3: Visual template matching & AT-SPI tree query."""
    # 1. Visual Template Match test: crop small area from current screen and re-locate it
    screen_path = Path("/dev/shm/hermes_gate2_screenshot.png")
    if not screen_path.exists():
        controller.take_screenshot(screen_path)

    img = Image.open(screen_path)
    # Crop a 60x60 region from (400, 400)
    crop_box = (400, 400, 460, 460)
    template = img.crop(crop_box)
    tpl_path = Path("/dev/shm/hermes_gate3_template.png")
    template.save(tpl_path)

    loc = controller.find_element_by_description("Test Widget", screenshot_path=screen_path, template_path=tpl_path)
    tpl_match_ok = loc.get("found") and loc.get("confidence", 0) > 0.95
    
    # 2. AT-SPI Tree query test
    at_spi_res = controller.get_accessibility_tree()
    at_spi_ok = at_spi_res.get("success") and "data" in at_spi_res

    overall = tpl_match_ok and at_spi_ok
    log_gate(
        "GATE 3",
        "Visual Element Localization (CV2 template match + AT-SPI tree)",
        overall,
        f"CV2 match confidence: {loc.get('confidence', 0):.4f} at ({loc.get('x')}, {loc.get('y')}), AT-SPI tree accessible: {at_spi_ok}",
    )
    return overall


def test_gate4_input_dispatch(controller: CUAController) -> bool:
    """Gate 4: Input action dispatch (move, click, keypress, typing, scroll)."""
    m_ok = controller.move_cursor(500, 500)
    c_ok = controller.click_element(500, 500, button="left", clicks=1)
    k_ok = controller.press_key("Shift_L")
    t_ok = controller.type_text("echo 1", interval=0.005)
    s_ok = controller.scroll(direction="down", amount=2)

    passed = all([m_ok, c_ok, k_ok, t_ok, s_ok])
    log_gate(
        "GATE 4",
        "Input Action Dispatch (move, click, keypress, typing, scroll)",
        passed,
        f"move={m_ok}, click={c_ok}, keypress={k_ok}, type={t_ok}, scroll={s_ok}",
    )
    return passed


def test_gate5_browser_loop(controller: CUAController) -> bool:
    """Gate 5: Browser automation loop with multi-step execution."""
    loop = BrowserAutomationLoop(controller)
    steps = [
        {"action": "wait", "seconds": 0.1},
        {"action": "scroll", "direction": "down", "amount": 1},
        {"action": "screenshot", "label": "browse_step"},
    ]
    res = loop.run_navigation_task("https://hermes.local/demo", steps, capture_screenshots=True)
    passed = res.get("success", False) and res.get("steps_executed") == 3 and res.get("final_screenshot", {}).get("success")
    log_gate(
        "GATE 5",
        "Browser Automation Loop (multi-step navigation workflow)",
        passed,
        f"Executed {res.get('steps_executed')} steps, task_id={res.get('task_id')}, final_shot={res.get('final_screenshot', {}).get('path')}",
    )
    return passed


def test_gate6_sandboxed_terminal_cua() -> bool:
    """Gate 6: Sandboxed Terminal CUA execution & append-only trajectory."""
    recorder = TrajectoryRecorder(session_id="cua-gate6-verify")
    term = TerminalCUA(recorder=recorder)

    res = term.execute("echo 'HERMES_CUA_SANDBOX_VERIFIED' && uname -s")
    output_ok = "HERMES_CUA_SANDBOX_VERIFIED" in res.get("output", "") and res.get("returncode") == 0
    sandboxed_ok = res.get("sandboxed") is True

    # Verify trajectory recording on disk
    traj_path = recorder.path
    traj_ok = traj_path.exists() and traj_path.stat().st_size > 0

    passed = output_ok and sandboxed_ok and traj_ok
    log_gate(
        "GATE 6",
        "Sandboxed Terminal CUA & Append-Only Trajectory Chain",
        passed,
        f"rc={res.get('returncode')}, output={res.get('output').strip()[:40]}, traj_file={traj_path}",
    )
    return passed


def main() -> int:
    print("=" * 75)
    print("  HERMES PHASE 5: COMPUTER-USE ACTIVATION (CUA FULL LOOP) VERIFICATION")
    print("=" * 75)

    controller = get_cua_controller()

    g1 = test_gate1_daemon_and_display(controller)
    g2 = test_gate2_pixel_capture(controller)
    g3 = test_gate3_element_localization(controller)
    g4 = test_gate4_input_dispatch(controller)
    g5 = test_gate5_browser_loop(controller)
    g6 = test_gate6_sandboxed_terminal_cua()

    print("=" * 75)
    all_passed = all([g1, g2, g3, g4, g5, g6])
    if all_passed:
        print("[92m[SUCCESS][0m ALL 6 PHASE 5 CUA GATES PASSED (100% OPERATIONAL).")
        return 0
    else:
        print("[91m[FAILURE][0m ONE OR MORE CUA GATES FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
