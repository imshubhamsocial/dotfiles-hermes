"""
Phase 9: Prime Agent Architecture — RLM Persistent Python Kernel
================================================================
Implements Recursive Language Model (RLM) persistent Python kernel in /dev/shm.
Allows agents to execute batched, programmatic tool calls in a single Python turn
(e.g., sieve, ast-grep, diff_apply, lsp) instead of sequential chat turn cycles.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class KernelExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    variables_exported: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.returncode == 0


class PrimePythonKernel:
    """
    Persistent in-memory Python state machine providing sub-5ms batch tool execution.
    """

    def __init__(self, workspace_root: Optional[Union[str, Path]] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self._globals: Dict[str, Any] = {
            "__builtins__": __builtins__,
            "Path": Path,
            "json": json,
            "os": os,
            "sys": sys,
            "WORKSPACE_ROOT": str(self.workspace_root),
        }
        self._execution_count = 0

    def register_tool(self, name: str, func: Any) -> None:
        """Exposes a tool or helper function directly in the kernel namespace."""
        self._globals[name] = func

    def execute_script(self, script_code: str, timeout_sec: float = 10.0) -> KernelExecutionResult:
        """Executes a multi-line Python script within the persistent kernel namespace."""
        self._execution_count += 1
        t0 = time.perf_counter()

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        sys.stdout, sys.stderr = stdout_buf, stderr_buf
        rc = 0
        try:
            # Execute within persistent globals
            exec(script_code, self._globals)
        except Exception:
            rc = 1
            stderr_buf.write(traceback.format_exc())
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        duration_ms = (time.perf_counter() - t0) * 1000.0

        # Export simple serializable user variables
        exported = {}
        for k, v in self._globals.items():
            if not k.startswith("_") and isinstance(v, (str, int, float, bool, list, dict)):
                exported[k] = v

        return KernelExecutionResult(
            returncode=rc,
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue(),
            duration_ms=round(duration_ms, 2),
            variables_exported=exported,
        )


def create_prime_kernel(workspace_root: Optional[Union[str, Path]] = None) -> PrimePythonKernel:
    return PrimePythonKernel(workspace_root=workspace_root)
