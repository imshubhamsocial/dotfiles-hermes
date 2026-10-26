"""Unit tests for Live state.db Dream-RSI 2.0 Ingestion and Replay Simulator."""

import pytest
from scenario.live_sync import LiveDreamSyncEngine


def test_live_dream_sync_execution():
    """Asserts that LiveDreamSyncEngine successfully ingests real state.db sessions."""
    engine = LiveDreamSyncEngine()
    report = engine.sync()

    assert report["sessions_ingested"] >= 100, f"Expected >= 100 sessions, got {report['sessions_ingested']}"
    assert report["messages_processed"] >= 3000, f"Expected >= 3000 messages, got {report['messages_processed']}"
    assert report["replay_trees_persisted"] >= 1, f"Expected >= 1 replay trees, got {report['replay_trees_persisted']}"
    assert report["status"] == "synchronized"


def test_doubly_robust_and_rrsi_gate():
    """Asserts that Doubly Robust evaluation passes the RRSI variance stability gate."""
    engine = LiveDreamSyncEngine()
    report = engine.sync()

    assert report["rrsi_gate_passed"] is True, "RRSI variance stability gate failed"
    assert report["performance_lift"] > report["rrsi_stability_margin"]
    assert report["call_reduction_ratio"] >= 2.0, f"Expected >= 2.0x call reduction, got {report['call_reduction_ratio']}"


def test_zero_cuda_delta():
    """Asserts that trajectory ingestion and replay trees execute at 0 MiB CUDA VRAM delta."""
    engine = LiveDreamSyncEngine()
    report = engine.sync()

    assert report["cuda_delta_mib"] == 0.0, f"Expected 0.0 CUDA delta, got {report['cuda_delta_mib']}"
