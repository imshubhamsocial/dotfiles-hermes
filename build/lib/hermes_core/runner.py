"""
Hermes Canonical Runner SDK (Issue #28)
=======================================
Provides a typed, resilient Python SDK interface to execute Hermes agent tasks.
Features:
- Encapsulates mandatory flags: --in <DIR>, --yolo, -z (oneshot), -v (verbose)
- Auto-resolves workspace directory to current working directory or explicit Path
- Implements non-blocking I/O stream byte activity heartbeats (Issue #03)
- Returns structured ExecutionResult with status, timings, and outputs
"""

from __future__ import annotations

import os
import sys
import time
import shutil
import select
import selectors
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionResult:
    """Structured result from a HermesRunner execution turn."""
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    workspace: Path
    goal: str
    telemetry: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class HermesRunner:
    """Canonical programmatic SDK client for Hermes Agent OS."""

    def __init__(
        self,
        workspace: Optional[Path | str] = None,
        profile: str = "auto",
        max_turns: int = 25,
        yolo: bool = True,
        verbose: bool = False,
        inactivity_timeout_s: float = 60.0,
        binary_path: Optional[str] = None,
    ):
        self.workspace = Path(workspace or os.environ.get("HERMES_WORKSPACE", Path.cwd())).resolve()
        self.profile = profile
        self.max_turns = max_turns
        self.yolo = yolo
        self.verbose = verbose
        self.inactivity_timeout_s = inactivity_timeout_s
        self.binary_path = binary_path or shutil.which("hermes") or sys.executable

    def run(
        self,
        prompt: str,
        workspace: Optional[Path | str] = None,
        extra_flags: Optional[List[str]] = None,
    ) -> ExecutionResult:
        """Execute a prompt turn through Hermes with stream heartbeats."""
        ws = Path(workspace).resolve() if workspace else self.workspace
        ws.mkdir(parents=True, exist_ok=True)

        cmd = []
        if self.binary_path.endswith("python") or self.binary_path.endswith("python3") or self.binary_path.endswith("python3.13"):
            cmd.extend([self.binary_path, "-m", "hermes_core.cli"])
        else:
            cmd.append(self.binary_path)

        cmd.extend([
            "-z",
            "-w", str(ws),
            "-p", self.profile,
            "--max-turns", str(self.max_turns),
        ])
        if self.yolo:
            cmd.append("--yolo")
        if self.verbose:
            cmd.append("-v")
        if extra_flags:
            cmd.extend(extra_flags)

        cmd.append(prompt)

        env = os.environ.copy()
        env["HERMES_WORKSPACE"] = str(ws)

        start_time = time.perf_counter()
        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []

        proc = subprocess.Popen(
            cmd,
            cwd=str(ws),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            start_new_session=True,
        )

        sel = selectors.DefaultSelector()
        if proc.stdout:
            sel.register(proc.stdout, selectors.EVENT_READ, data="stdout")
        if proc.stderr:
            sel.register(proc.stderr, selectors.EVENT_READ, data="stderr")

        last_activity = time.perf_counter()

        while proc.poll() is None:
            events = sel.select(timeout=1.0)
            if events:
                for key, mask in events:
                    line = key.fileobj.readline()
                    if line:
                        last_activity = time.perf_counter()
                        if key.data == "stdout":
                            stdout_chunks.append(line)
                            if self.verbose:
                                sys.stdout.write(line)
                                sys.stdout.flush()
                        else:
                            stderr_chunks.append(line)
                            if self.verbose:
                                sys.stderr.write(line)
                                sys.stderr.flush()
            else:
                # Check for zero-byte inactivity deadlock
                if time.perf_counter() - last_activity > self.inactivity_timeout_s:
                    try:
                        import signal
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                        time.sleep(1.0)
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        proc.kill()
                    stderr_chunks.append(f"\n[HermesRunner] Terminated due to inactivity (> {self.inactivity_timeout_s}s silence)")
                    break

        # Drain remaining output
        if proc.stdout:
            stdout_chunks.extend(proc.stdout.readlines())
        if proc.stderr:
            stderr_chunks.extend(proc.stderr.readlines())

        sel.close()
        duration = time.perf_counter() - start_time
        exit_code = proc.returncode if proc.returncode is not None else 1

        return ExecutionResult(
            exit_code=exit_code,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            duration_s=duration,
            workspace=ws,
            goal=prompt,
        )
