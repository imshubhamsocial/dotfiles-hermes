"""Pytest verification module for Phase 12 SoL-Pi Evaluation Testbed."""

import json
from pathlib import Path
import subprocess
import pytest


def test_sol_pi_benchmark_execution():
    testbed_dir = Path(__file__).resolve().parent
    benchmark_script = testbed_dir / "benchmark_sol_pi.py"

    # Execute benchmark runner
    res = subprocess.run(
        ["python3", str(benchmark_script)],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0, f"Benchmark execution failed: {res.stderr}"

    # Read and assert generated metrics.json
    metrics_path = testbed_dir / "metrics.json"
    assert metrics_path.exists(), "metrics.json was not created"

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["token_reduction_pct"] >= 44.0, f"Token reduction {metrics['token_reduction_pct']}% < 44.0%"
    assert metrics["tabu_halt_triggered"] is True, "Two-Strike Tabu halt was not triggered"
    assert metrics["verifier_preserved_tracebacks"] is True, "Verifier failed to preserve Python tracebacks"
    assert metrics["exit_code_masked"] is False, "Exit code was masked"
    assert metrics["phase12_certified"] is True, "Phase 12 certification flag is false"
