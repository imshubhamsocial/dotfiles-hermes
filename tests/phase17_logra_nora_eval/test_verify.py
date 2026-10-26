"""Verification test suite for Phase 17 metrics and gate criteria."""

import json
import pathlib
import pytest
from logra_aligner import LoGRAAligner

testbed_root = pathlib.Path(__file__).resolve().parent


def test_aligner_nora_initialization():
    """Asserts that LoGRAAligner satisfies Frobenius normalization."""
    aligner = LoGRAAligner(rank=64, d_model=2048)
    a_matrix, f_norm = aligner.initialize_nora_down_proj(rank=64, d_model=2048, seed=42)
    assert a_matrix.shape == (64, 2048)
    assert round(f_norm, 5) == 1.0


def test_training_telemetry_metrics():
    """Asserts that training telemetry meets all Phase 17 criteria."""
    report_file = testbed_root / "training_telemetry.json"
    assert report_file.exists(), "training_telemetry.json must be generated prior to verification"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report.get("peak_total_vram_mib", 9999.0) <= 4812.0
    assert report.get("nora_frobenius_norm_init") == 1.0
    assert report.get("kl_budget_respected") is True
    assert report.get("post_resume_mtp_tok_per_sec", 0.0) >= 39.7
