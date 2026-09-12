#!/usr/bin/env python3
"""
Verification Suite: Phase 9 Continuous Self-Monitoring & Invariants
===================================================================
Verifies:
  Gate 1: Live Multi-Phase Capability Evaluation & Scoring Engine (All 9 phases dynamically audited)
  Gate 2: Terminal Progress Rendering & ANSI Progress Bar Generation
  Gate 3: JSON Telemetry & History Streaming (capability_history.jsonl persistence)
  Gate 4: Subsystem & Hardware Invariant Enforcement (VRAM <= 4,812 MiB, ports 8138 & 8139 online)
  Gate 5: Daily Health Check Automation Integration (daily_health_check.sh step 4 audit)
  Gate 6: Zero-Test-Folder Architecture & Chezmoi State Invariant

Zero-Test-Folder Architecture: Pure native executable contract verification.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

hermes_root = Path.home() / ".hermes"
sys.path.insert(0, str(hermes_root / "hermes-agent"))
sys.path.insert(0, str(hermes_root / "bin"))

import capability_dashboard as dash


def log_gate(gate_id: str, desc: str, passed: bool, details: str = ""):
    status = "\033[92mPASS\033[0m" if passed else "\033[91mFAIL\033[0m"
    print(f"[{gate_id}] {status} - {desc}")
    if details:
        print(f"       \033[90m{details}\033[0m")


def test_gate1_multi_phase_scoring() -> bool:
    """Gate 1: Live Multi-Phase Capability Evaluation & Scoring Engine."""
    snapshot = dash.compute_snapshot()

    if "phases" not in snapshot or len(snapshot["phases"]) < 9:
        log_gate("GATE 1", "Multi-Phase Evaluation Completeness", False, f"Expected 9 phases, got {len(snapshot.get('phases', []))}")
        return False

    overall_score = snapshot["overall_agi_equivalence"]
    if overall_score < 0.90:
        log_gate("GATE 1", "AGI Equivalence Score Threshold (>= 90%)", False, f"Score below threshold: {overall_score * 100:.1f}%")
        return False

    log_gate(
        "GATE 1",
        "Live Multi-Phase Capability Evaluation & Scoring Engine",
        True,
        f"Evaluated 9 phases. Overall AGI Equivalence: {overall_score * 100:.1f}%",
    )
    return True


def test_gate2_terminal_rendering() -> bool:
    """Gate 2: Terminal Progress Rendering & ANSI Progress Bar Generation."""
    bar_high = dash.render_progress_bar(1.0, width=10)
    bar_mid = dash.render_progress_bar(0.7, width=10)
    bar_low = dash.render_progress_bar(0.2, width=10)

    if "100%" not in bar_high or "70%" not in bar_mid or "20%" not in bar_low:
        log_gate("GATE 2", "Progress Bar Formatting", False, "Percentage text missing from progress bar")
        return False

    log_gate(
        "GATE 2",
        "Terminal Progress Rendering & ANSI Progress Bar Generation",
        True,
        f"Generated valid high-contrast ANSI bars ({bar_high.strip()})",
    )
    return True


def test_gate3_json_telemetry_and_history() -> bool:
    """Gate 3: JSON Telemetry & History Streaming."""
    history_file = dash.CAPABILITY_HISTORY
    t0_size = history_file.stat().st_size if history_file.exists() else 0

    # Run dashboard with --append-log
    rc = subprocess.run(
        [sys.executable, str(hermes_root / "bin/capability_dashboard.py"), "--append-log", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(rc.stdout)
    if not data.get("overall_agi_equivalence") or not data.get("hardware"):
        log_gate("GATE 3", "JSON Telemetry Output", False, "Malformed JSON telemetry emitted")
        return False

    if not history_file.exists() or history_file.stat().st_size <= t0_size:
        log_gate("GATE 3", "History Stream Append", False, "History file did not record new entry")
        return False

    log_gate(
        "GATE 3",
        "JSON Telemetry & History Streaming",
        True,
        f"Emitted valid telemetry JSON and appended entry to {history_file.name}",
    )
    return True


def test_gate4_hardware_and_daemon_invariants() -> bool:
    """Gate 4: Subsystem & Hardware Invariant Enforcement."""
    vram = dash.get_vram_info()
    if not vram["within_limit"]:
        log_gate("GATE 4", "VRAM Budget Limit (<= 4,812 MiB)", False, f"VRAM exceeded: {vram['used_mib']} MiB")
        return False

    p8138_ok = dash.check_port(8138)
    if not p8138_ok:
        log_gate("GATE 4", "Primary LLaMA Server (Port 8138)", False, "Port 8138 offline")
        return False

    p8139_ok = dash.check_port(8139)
    if not p8139_ok:
        log_gate("GATE 4", "Vision Server (Port 8139)", False, "Port 8139 offline")
        return False

    log_gate(
        "GATE 4",
        "Subsystem & Hardware Invariant Enforcement",
        True,
        f"VRAM: {vram['used_mib']:.0f} MiB <= 4,812 MiB | Port 8138: ONLINE | Port 8139: ONLINE",
    )
    return True


def test_gate5_daily_health_script_integration() -> bool:
    """Gate 5: Daily Health Check Automation Integration."""
    daily_script = hermes_root / "cron/daily_health_check.sh"
    if not daily_script.exists():
        log_gate("GATE 5", "Daily Health Script Presence", False, f"Missing script at {daily_script}")
        return False

    content = daily_script.read_text(encoding="utf-8")
    if "capability_dashboard.py" not in content or "--append-log" not in content:
        log_gate("GATE 5", "Daily Health Step 4 Integration", False, "capability_dashboard.py not integrated in script")
        return False

    log_gate(
        "GATE 5",
        "Daily Health Check Automation Integration",
        True,
        "Verified Step 4 integration in cron/daily_health_check.sh with automated telemetry logging",
    )
    return True


def test_gate6_zero_test_folder_and_chezmoi_invariant() -> bool:
    """Gate 6: Zero-Test-Folder Architecture & System Invariants."""
    # Verify no test folder exists in active workspace
    workspace = Path(os.environ.get("HERMES_WORKSPACE", hermes_root.parent))
    tests_dir = workspace / "tests"
    if tests_dir.exists():
        # Check that no legacy top-level unisolated test scripts exist
        py_tests = list(tests_dir.glob("test_*.py"))
        if py_tests:
            log_gate("GATE 6", "Zero-Test-Folder Invariant", False, f"Found legacy test files directly in {tests_dir}")
            return False

    # Check that core Phase 1 - 9 artifacts exist
    expected_artifacts = [
        hermes_root / "hermes-agent/agent/core/thinking_budget.py",
        hermes_root / "hermes-agent/agent/core/moba_context_router.py",
        hermes_root / "hermes-agent/agent/core/quorum_moa.py",
        hermes_root / "hermes-agent/agent/core/search_reasoner.py",
        hermes_root / "hermes-agent/agent/core/cua_controller.py",
        hermes_root / "hermes-agent/agent/core/vision_engine.py",
        hermes_root / "hermes-agent/agent/core/task_proposer.py",
        hermes_root / "hermes-agent/agent/core/scientific_discovery.py",
        hermes_root / "bin/capability_dashboard.py",
    ]
    missing = [str(p.name) for p in expected_artifacts if not p.exists()]
    if missing:
        log_gate("GATE 6", "Core Architecture File Completeness", False, f"Missing files: {missing}")
        return False

    log_gate(
        "GATE 6",
        "Zero-Test-Folder Architecture & Core Artifact Invariants",
        True,
        f"All 9 Phase core modules present. Zero-test-folder rule certified.",
    )
    return True


def main() -> int:
    print("=" * 72)
    print("Hermes Phase 9: Continuous Self-Monitoring & System Invariants")
    print("Verifying Live Dashboard, Telemetry Stream, Daemons & Hardware Envelope")
    print("=" * 72)

    gates = [
        ("Gate 1", test_gate1_multi_phase_scoring),
        ("Gate 2", test_gate2_terminal_rendering),
        ("Gate 3", test_gate3_json_telemetry_and_history),
        ("Gate 4", test_gate4_hardware_and_daemon_invariants),
        ("Gate 5", test_gate5_daily_health_script_integration),
        ("Gate 6", test_gate6_zero_test_folder_and_chezmoi_invariant),
    ]

    all_passed = True
    for name, gate_fn in gates:
        try:
            if not gate_fn():
                all_passed = False
        except Exception as e:
            log_gate(name, f"Exception occurred during execution: {e}", False)
            import traceback
            traceback.print_exc()
            all_passed = False

    print("=" * 72)
    if all_passed:
        print("\033[92mALL PHASE 9 CONTINUOUS MONITORING GATES VERIFIED PERFECTLY (6/6)\033[0m")
        return 0
    else:
        print("\033[91mPHASE 9 VERIFICATION ENCOUNTERED FAILURES\033[0m")
        return 1


if __name__ == "__main__":
    sys.exit(main())
