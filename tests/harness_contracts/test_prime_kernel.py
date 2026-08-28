"""
Contract Spike: Phase 9 Prime Agent Persistent Python Kernel
============================================================
Tests persistent variable retention, programmatic batch tool execution,
and captured stdout/stderr telemetry.
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.prime_kernel import (
    KernelExecutionResult,
    PrimePythonKernel,
    create_prime_kernel,
)


def test_prime_kernel_batch_execution_and_persistence():
    with tempfile.TemporaryDirectory() as td:
        kernel = create_prime_kernel(workspace_root=td)
        
        # Turn 1: define variables and mock tool
        script_1 = (
            "x = 10\n"
            "y = 20\n"
            "def custom_tool(val):\n"
            "    return val * 2\n"
            "print(f'Sum: {x + y}')\n"
        )
        res_1 = kernel.execute_script(script_1)
        assert res_1.is_success
        assert "Sum: 30" in res_1.stdout
        assert res_1.variables_exported["x"] == 10
        assert res_1.variables_exported["y"] == 20
        
        # Turn 2: use state from Turn 1
        script_2 = (
            "z = custom_tool(x) + y\n"
            "print(f'Computed z: {z}')\n"
        )
        res_2 = kernel.execute_script(script_2)
        assert res_2.is_success
        assert "Computed z: 40" in res_2.stdout
        assert res_2.variables_exported["z"] == 40
        assert res_2.duration_ms < 50.0  # Sub-50ms execution check


def test_prime_kernel_error_isolation():
    kernel = create_prime_kernel()
    res = kernel.execute_script("1 / 0")
    assert not res.is_success
    assert res.returncode == 1
    assert "ZeroDivisionError" in res.stderr
