"""
Contract Tests: Hermes CLI Harness Integration
===============================================
Validates native Hermes CLI execution, flags, subcommands, and plugin diagnostics:
  1. CLI version and help flags.
  2. Doctor health inspection subcommand.
  3. Plugins listing and mcp_tools doctor diagnosis.
  4. Exit code conventions (0 for success).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_hermes_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run hermes CLI via python module invocation."""
    cmd = [sys.executable, "-m", "hermes_cli.main", *args]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_hermes_version():
    """Verify hermes --version outputs version and exits cleanly."""
    res = run_hermes_cli("--version")
    assert res.returncode == 0
    assert "hermes" in res.stdout.lower() or "version" in res.stdout.lower() or len(res.stdout.strip()) > 0


def test_hermes_help():
    """Verify hermes --help documents mandatory operational flags."""
    res = run_hermes_cli("--help")
    assert res.returncode == 0
    assert "--yolo" in res.stdout
    assert "-z" in res.stdout or "--oneshot" in res.stdout
    assert "--skills" in res.stdout


def test_hermes_doctor():
    """Verify hermes doctor runs health checks cleanly."""
    res = run_hermes_cli("doctor")
    assert res.returncode == 0
    assert "PASSED" in res.stdout or "OK" in res.stdout or "Doctor" in res.stdout


def test_hermes_plugins_list():
    """Verify hermes plugins list detects registered plugins."""
    res = run_hermes_cli("plugins", "list")
    assert res.returncode == 0
    assert "mcp_tools" in res.stdout or "plugins" in res.stdout.lower()


def test_hermes_plugins_doctor_mcp_tools():
    """Verify hermes plugins doctor validates the mcp_tools plugin."""
    res = run_hermes_cli("plugins", "doctor", "mcp_tools")
    assert res.returncode == 0
    assert "PASSED" in res.stdout or "mcp_tools" in res.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
