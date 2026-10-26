"""Unit tests for Phase 24 Offline LoGRA/NoRA Adapter Engine."""

import json
import pathlib

import numpy as np
import pytest
from offline_adapter_engine import (
    LoGRAGradientSketcher,
    NoRAAdapterConsolidator,
    OfflineEvolutionOrchestrator,
    VRAMQuorumGuard,
)

testbed_root = pathlib.Path(__file__).resolve().parent.parent


def test_vram_quorum_guard():
    guard = VRAMQuorumGuard(max_quiescent_vram_mib=650.0)
    tme_verified, quiescent_vram, peak_total = guard.acquire_vram_quorum()

    assert tme_verified is True
    assert quiescent_vram <= 650.0
    assert peak_total <= 4812.0
    assert guard.llama_server_suspended is True

    # Test quorum breach detection
    guard.max_quiescent_vram_mib = 500.0
    with pytest.raises(RuntimeError, match="VRAM Quorum Violation"):
        guard.acquire_vram_quorum()


def test_logra_gradient_sketcher():
    sketcher = LoGRAGradientSketcher(rank=64, d_model=2048, seed=42)
    dense_grad = np.ones((2048, 64), dtype=np.float32)
    projected = sketcher.project_gradient(dense_grad)

    assert projected.shape == (2048, 64)

    # Bad dimension should raise ValueError
    bad_grad = np.ones((1024, 64), dtype=np.float32)
    with pytest.raises(ValueError, match="Gradient dimension"):
        sketcher.project_gradient(bad_grad)


def test_nora_adapter_consolidator():
    consolidator = NoRAAdapterConsolidator(rank=64, d_model=2048)
    matrix_a, f_norm = consolidator.initialize_normalized_a(seed=42)

    assert matrix_a.shape == (64, 2048)
    assert f_norm == 1.0

    matrix_b = consolidator.initialize_zero_b()
    assert matrix_b.shape == (2048, 64)
    assert np.all(matrix_b == 0.0)

    # Test KL divergence
    p1 = np.array([0.5, 0.5])
    p2 = np.array([0.5, 0.5])
    assert consolidator.compute_kl_divergence(p1, p2) == 0.0

    p3 = np.array([0.9, 0.1])
    p4 = np.array([0.1, 0.9])
    assert consolidator.compute_kl_divergence(p3, p4) > 0.0


def test_offline_evolution_orchestrator():
    buffer_path = testbed_root / "scenario" / "training_buffer" / "samples.jsonl"
    orchestrator = OfflineEvolutionOrchestrator(str(buffer_path), rank=64, d_model=2048)

    samples = orchestrator.load_training_trajectories()
    assert len(samples) >= 5

    metrics = orchestrator.run_offline_evolution_cycle()
    assert metrics["temporal_mutual_exclusion_verified"] is True
    assert metrics["peak_total_vram_mib"] <= 4812.0
    assert metrics["nora_frobenius_norm"] == 1.0
    assert metrics["kl_divergence"] <= 0.05
    assert metrics["post_resume_mtp_tok_per_sec"] >= 42.4
    assert metrics["samples_processed"] == len(samples)
