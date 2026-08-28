#!/usr/bin/env python3
"""
POSIX Worker Pool — Gold Standard Scaffold
Subprocess pool with process group isolation and graceful teardown.
"""
import os
import signal
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List


def _worker_init():
    """Reset signal handlers in child processes."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_worker(cmd: str, timeout: float = 30.0) -> dict:
    """Execute a command in an isolated process group."""
    try:
        proc = subprocess.Popen(
            cmd, shell=True,
            preexec_fn=os.setsid,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": stdout.decode(errors="replace")[-500:],
            "stderr": stderr.decode(errors="replace")[-500:],
        }
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        return {"cmd": cmd, "returncode": -1, "error": "TIMEOUT"}
    except Exception as e:
        return {"cmd": cmd, "returncode": -1, "error": str(e)}


def worker_pool(commands: List[str], max_workers: int = 4,
                timeout: float = 30.0) -> List[dict]:
    """Run commands in parallel with process group isolation."""
    results = []
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_worker_init,
    ) as pool:
        futures = {pool.submit(run_worker, cmd, timeout): cmd for cmd in commands}
        for future in as_completed(futures):
            results.append(future.result())
    return results


if __name__ == "__main__":
    cmds = sys.argv[1:] or ["echo hello", "echo world", "sleep 0.1"]
    for r in worker_pool(cmds):
        status = "OK" if r["returncode"] == 0 else f"FAIL({r['returncode']})"
        print(f"  {status}: {r['cmd']}")
