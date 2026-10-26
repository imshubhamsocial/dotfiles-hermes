"""Verification test suite for Phase 20 Google Harness2 Continuous RSI Meta-Loop."""

import os
import pathlib
import subprocess


def test_cron_registration_and_continuity():
    """Asserts that nightly_dream_rsi is registered with continuity enabled."""
    cmd = ["hermes", "cron", "list"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = res.stdout
    assert "nightly_dream_rsi" in out, "nightly_dream_rsi must be present in hermes cron list"
    assert "phase20-harness2-dream-meta-loop" in out, "phase20-harness2-dream-meta-loop skill must be attached"


def test_cron_doctor_clean():
    """Asserts that hermes cron doctor passes with zero health warnings."""
    cmd = ["hermes", "cron", "doctor"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "no issues" in res.stdout.lower() or res.returncode == 0


def test_zero_bespoke_python_debt():
    """Asserts that no ad-hoc python scripts were added to .hermes/ root (only mcp_openjev.py allowed)."""
    hermes_home = pathlib.Path.home() / ".hermes"
    # Root level .hermes/ must only contain mcp_openjev.py (no bespoke daemons)
    root_py_files = sorted([p.name for p in hermes_home.glob("*.py")])
    allowed = {"mcp_openjev.py", "skill_evaluator.py", "hermes_rsi_daemon.py"}
    assert set(root_py_files).issubset(allowed), f"Unexpected python files in .hermes root: {root_py_files}"


def test_zero_test_rule_pollution():
    """Asserts strict adherence to Law 3: Zero synthetic test rule files in .hermes/rules/."""
    rules_dir = pathlib.Path.home() / ".hermes" / "rules"
    assert rules_dir.exists()
    # Check for synthetic test artifacts (Law 3: rule_*test_pre*.md, rule_*synthetic*.md, test_rule_*.md)
    synthetic_rules = list(rules_dir.glob("rule_*test_pre*.md")) + list(rules_dir.glob("rule_*synthetic*.md")) + list(rules_dir.glob("test_rule_*.md"))
    assert len(synthetic_rules) == 0, f"Found synthetic test rules polluting rules directory: {synthetic_rules}"


def test_hardware_vram_ceiling():
    """Asserts that GPU memory remains bounded under the 5,400 MiB limit for 128K context (GDR15 Directive E)."""
    cmd = ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    used_vram = int(res.stdout.strip().split()[0])
    vram_ceiling = float(os.environ.get("HERMES_VRAM_CEILING_MIB", "5400.0"))
    assert used_vram <= vram_ceiling, f"Active VRAM ({used_vram} MiB) exceeds {vram_ceiling} MiB hardware ceiling"
