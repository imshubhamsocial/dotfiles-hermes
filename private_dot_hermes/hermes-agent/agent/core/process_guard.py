"""
U10 Hardened POSIX Process Group Teardown (Phase 3.3)
=====================================================
Hanging test runners (Playwright, WebGL renderers, pytest fixtures) leave
orphaned child processes alive when only the direct child PID is killed on
timeout (roadmap §3.3 Trap-1: zombie node/browser accumulation).

Guarantee provided here:

  1. Every command spawns as its OWN session/process-group leader
     (`start_new_session=True` -> setsid).
  2. On timeout the ENTIRE group receives SIGKILL via
     `os.killpg(os.getpgid(pid), SIGKILL)` — no orphan survives.
  3. Teardown is verified: `/proc` is scanned for surviving group members
     and the elapsed teardown time is reported (spec target <= 100 ms).
"""

import os
import signal
import subprocess
import time
from typing import Any, Dict, Optional, Tuple

SURVIVOR_SCAN_DEADLINE_S = 1.0
TEARDOWN_BUDGET_MS = 100


def _group_members_alive(pgid: int) -> list:
    """Return PIDs whose /proc/<pid>/stat still belongs to the given PGID."""
    members = []
    try:
        entries = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return members
    for pid in entries:
        try:
            with open(f"/proc/{pid}/stat", "rb") as fh:
                stat = fh.read()
            # comm may contain spaces/parens; split after the closing paren.
            fields = stat[stat.rindex(b")") + 2:].split()
            if int(fields[2]) == pgid:  # field 5 in stat(5) after comm = pgrp
                members.append(int(pid))
        except (OSError, ValueError, IndexError):
            continue
    return members


def run_with_group_teardown(cmd, timeout_sec: float = 120,
                            shell: str = "bash",
                            env: Optional[Dict[str, str]] = None,
                            cwd: Optional[str] = None) -> Tuple[int, str, Dict[str, Any]]:
    """Run one command in its own process group; SIGKILL the whole group on
    timeout. `cmd` is a shell string or an argv list. Returns
    (returncode, combined_output, meta).

    meta keys: timed_out, pgid, teardown_ms (None if not torn down),
    survivors_after_kill, killed_signal.
    """
    meta: Dict[str, Any] = {"timed_out": False, "pgid": None,
                            "teardown_ms": None, "survivors_after_kill": [],
                            "killed_signal": None}
    argv = cmd if isinstance(cmd, list) else [shell, "-c", cmd]
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, start_new_session=True, env=env, cwd=cwd,
    )
    meta["pgid"] = proc.pid  # session leader => PGID == child PID
    try:
        out, _ = proc.communicate(timeout=timeout_sec)
        return proc.returncode, (out or "").strip(), meta
    except subprocess.TimeoutExpired:
        meta["timed_out"] = True
        t0 = time.perf_counter()
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            meta["killed_signal"] = "SIGKILL"
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        # Verify: scan /proc until no group member remains (or deadline).
        deadline = time.perf_counter() + SURVIVOR_SCAN_DEADLINE_S
        survivors = _group_members_alive(meta["pgid"])
        while survivors and time.perf_counter() < deadline:
            time.sleep(0.005)
            survivors = _group_members_alive(meta["pgid"])
        meta["teardown_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        meta["survivors_after_kill"] = survivors
        return 124, f"Error: Command timed out after {timeout_sec}s; process group {meta['pgid']} SIGKILLed.", meta
