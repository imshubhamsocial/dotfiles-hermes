"""Machine verification gate for Phase 24 Autonomous Offline LoGRA/NoRA Weight Evolution."""

import json
import os
import pathlib
import sys

testbed_root = pathlib.Path(__file__).resolve().parent
scenario_dir = testbed_root / "scenario"
sys.path.insert(0, str(scenario_dir))

from offline_adapter_engine import (
    LoGRAGradientSketcher,
    NoRAAdapterConsolidator,
    OfflineEvolutionOrchestrator,
    VRAMQuorumGuard,
)


def test_autonomous_logra_metrics():
    """Validates that autonomous_logra_metrics.json exists and satisfies Phase 24 invariants."""
    metrics_path = testbed_root / "autonomous_logra_metrics.json"
    assert metrics_path.exists(), f"Metrics file {metrics_path} must exist (run benchmark_autonomous_logra.py)"

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    # Invariant 1: Temporal Mutual Exclusion Verified
    assert metrics["temporal_mutual_exclusion_verified"] is True, (
        "Temporal Mutual Exclusion must be verified (llama-server suspended, VRAM quorum met)"
    )

    # Invariant 2: Peak Total VRAM <= 4,812.0 MiB Hardware Ceiling
    assert metrics["peak_total_vram_mib"] <= 4812.0, (
        f"Peak total VRAM must be <= 4812.0 MiB, got {metrics['peak_total_vram_mib']} MiB"
    )

    # Invariant 3: NoRA Frobenius Normalization ||A||_F == 1.0
    assert metrics["nora_frobenius_norm"] == 1.0, (
        f"NoRA Frobenius norm must be 1.0, got {metrics['nora_frobenius_norm']}"
    )

    # Invariant 4: KL Divergence <= 0.05
    assert metrics["kl_divergence"] <= 0.05, (
        f"KL divergence must be <= 0.05, got {metrics['kl_divergence']}"
    )

    # Invariant 5: Post-Resume MTP Speculative Throughput >= 42.4 tok/s
    assert metrics["post_resume_mtp_tok_per_sec"] >= 42.4, (
        f"Post-resume MTP throughput must be >= 42.4 tok/s, got {metrics['post_resume_mtp_tok_per_sec']} tok/s"
    )


def test_live_offline_logra_execution(tmp_path):
    """Live functional verification of OfflineEvolutionOrchestrator."""
    sample_file = tmp_path / "samples.jsonl"
    sample_file.write_text(
        '{"id": "t1", "reward": 0.95, "tokens": 128}\n'
        '{"id": "t2", "reward": 0.90, "tokens": 256}\n',
        encoding="utf-8",
    )

    orchestrator = OfflineEvolutionOrchestrator(
        str(sample_file),
        rank=64,
        d_model=2048,
        kl_budget=0.05,
    )

    metrics = orchestrator.run_offline_evolution_cycle()

    assert metrics["temporal_mutual_exclusion_verified"] is True
    assert metrics["peak_total_vram_mib"] <= 4812.0
    assert metrics["nora_frobenius_norm"] == 1.0
    assert metrics["kl_divergence"] <= 0.05
    assert metrics["post_resume_mtp_tok_per_sec"] >= 42.4
    assert metrics["samples_processed"] == 2
