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


import selectors


def run_with_group_teardown(
    cmd,
    timeout_sec: float = 120,
    shell: str = "bash",
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
    inactivity_timeout_s: Optional[float] = None,
) -> Tuple[int, str, Dict[str, Any]]:
    """Run one command in its own process group; SIGKILL the whole group on
    timeout. Uses non-blocking selector streaming for zero-byte inactivity heartbeats.
    Returns (returncode, combined_output, meta).
    """
    meta: Dict[str, Any] = {
        "timed_out": False,
        "pgid": None,
        "teardown_ms": None,
        "survivors_after_kill": [],
        "killed_signal": None,
    }
    argv = cmd if isinstance(cmd, list) else [shell, "-c", cmd]
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
        env=env,
        cwd=cwd,
    )
    meta["pgid"] = proc.pid  # session leader => PGID == child PID

    sel = selectors.DefaultSelector()
    if proc.stdout:
        sel.register(proc.stdout, selectors.EVENT_READ)

    output_chunks = []
    start_time = time.perf_counter()
    last_activity = time.perf_counter()
    timed_out = False

    try:
        while proc.poll() is None:
            now = time.perf_counter()
            if now - start_time > timeout_sec:
                timed_out = True
                break

            if inactivity_timeout_s and (now - last_activity > inactivity_timeout_s):
                timed_out = True
                break

            events = sel.select(timeout=0.1)
            if events:
                for key, _ in events:
                    line = key.fileobj.readline()
                    if line:
                        output_chunks.append(line)
                        last_activity = time.perf_counter()

        # Drain remaining output
        if proc.stdout and not timed_out:
            output_chunks.extend(proc.stdout.readlines())

    finally:
        sel.close()

    if timed_out:
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

    combined = "".join(output_chunks).strip()
    return proc.returncode if proc.returncode is not None else 0, combined, meta
