"""Pytest verification module for Phase 13 STAIR Evaluation Testbed."""

import json
from pathlib import Path
import subprocess
import pytest


def test_stair_benchmark_execution():
    testbed_dir = Path(__file__).resolve().parent
    benchmark_script = testbed_dir / "benchmark_stair.py"

    res = subprocess.run(
        ["python3", str(benchmark_script)],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0, f"Benchmark execution failed: {res.stderr}\nOutput: {res.stdout}"

    metrics_path = testbed_dir / "metrics.json"
    assert metrics_path.exists(), "metrics.json was not created"

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["recall_at_1"] >= 0.826, f"Recall@1 {metrics['recall_at_1']} < 0.826"
    assert metrics["chunk_boundary_errors"] == 0, "Chunk boundary errors detected"
    assert metrics["phase13_certified"] is True, "Phase 13 certification flag is false"
