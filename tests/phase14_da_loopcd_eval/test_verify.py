"""Pytest verification module for Phase 14 Declarative Attention & LoopCD Testbed."""

import json
from pathlib import Path
import subprocess
import pytest


def test_da_loopcd_benchmark_execution():
    testbed_dir = Path(__file__).resolve().parent
    benchmark_script = testbed_dir / "benchmark_da_loopcd.py"

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

    assert metrics["attended_token_reduction_pct"] >= 48.0, f"Attended token reduction {metrics['attended_token_reduction_pct']}% < 48.0%"
    assert metrics["loopcd_pass_at_1_gain"] > 0.0, "LoopCD gain must be positive"
    assert metrics["slot_cache_hit_rate_pct"] >= 90.0, f"Slot cache hit rate {metrics['slot_cache_hit_rate_pct']}% < 90.0%"
    assert metrics["phase14_certified"] is True, "Phase 14 certification flag is false"
