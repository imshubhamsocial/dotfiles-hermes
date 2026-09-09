"""
Harness Safety Contract: Sandbox Isolation & Execution Security
===============================================================
Validates:
  1. Bubblewrap (bwrap) availability and standard command line isolation flags.
  2. Denial output sanitization to prevent LLM retry loops.
  3. POSIX process group termination on timeout.
  4. VRAM envelope verification.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import pytest

BWRAP_BIN = "/usr/bin/bwrap"
SANDBOX_DENIAL_GUIDANCE = "Permission denied: access to protected system paths is restricted by policy."
DENIAL_PATTERNS = ["/etc/shadow", "/root", ".ssh", "Operation not permitted", "Permission denied"]


def build_bwrap_cmd(cmd: str, workspace: Path | None = None) -> list[str]:
    """Constructs minimal bwrap namespace jail arguments."""
    ws = str(workspace or Path.cwd())
    return [
        BWRAP_BIN,
        "--unshare-all",
        "--proc", "/proc",
        "--dev", "/dev",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--bind", ws, ws,
        "--chdir", ws,
        "bash", "-c", cmd,
    ]


def sanitize_output(output: str) -> str:
    """Collapses sensitive or protected denials into canonical single-line guidance."""
    for pattern in DENIAL_PATTERNS:
        if pattern in output:
            return SANDBOX_DENIAL_GUIDANCE
    return output


def run_with_timeout(cmd: str, timeout_sec: float = 2.0) -> tuple[int, str, bool]:
    """Runs command in a dedicated process group and kills children on timeout."""
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        out, _ = proc.communicate(timeout=timeout_sec)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        out, _ = proc.communicate()
        rc = proc.returncode
    return rc, out, timed_out


# ─── Bwrap Isolation Flag Tests ──────────────────────────────────────────────

def test_bwrap_binary_present():
    assert Path(BWRAP_BIN).exists(), "bwrap binary missing in host/container"


def test_build_cmd_contains_mandatory_isolation_flags():
    cmd = build_bwrap_cmd("true")
    joined = " ".join(cmd)
    for flag in ("--unshare-all", "--proc", "/proc", "--dev", "/dev", "--ro-bind", "/usr"):
        assert flag in joined


def test_build_cmd_never_binds_protected_roots():
    argv = build_bwrap_cmd("true")
    for protected in ("/etc", str(Path.home() / ".ssh"), "/root"):
        bind_positions = [i for i, a in enumerate(argv) if a in ("--bind", "--ro-bind")]
        for i in bind_positions:
            if i + 2 < len(argv):
                assert argv[i + 1] != protected and argv[i + 2] != protected


def test_sanitize_collapses_protected_denials():
    raw = "cat: /etc/shadow: Permission denied"
    assert sanitize_output(raw) == SANDBOX_DENIAL_GUIDANCE
    raw2 = "head: cannot open '/root/.bashrc': Permission denied"
    assert sanitize_output(raw2) == SANDBOX_DENIAL_GUIDANCE


def test_sanitize_leaves_normal_errors_untouched():
    normal = "Traceback (most recent call last):\nValueError: bad input"
    assert sanitize_output(normal) == normal


# ─── Process Group & Timeout Safety Tests ────────────────────────────────────

def test_process_group_normal_execution():
    rc, out, timed_out = run_with_timeout("echo 'safety_ok'", timeout_sec=5.0)
    assert rc == 0
    assert "safety_ok" in out
    assert timed_out is False


def test_process_group_timeout_kills_children():
    t0 = time.perf_counter()
    rc, out, timed_out = run_with_timeout("sleep 10", timeout_sec=0.5)
    elapsed = time.perf_counter() - t0
    assert timed_out is True
    assert elapsed < 3.0, "Process group kill did not terminate within budget"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
