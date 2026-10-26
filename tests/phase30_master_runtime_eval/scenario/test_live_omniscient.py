"""Unit tests for Omniscient Runtime Kernel Verifier."""

import pytest
from scenario.live_omniscient import OmniscientKernelVerifier


def test_live_nvml_vram_and_port_health():
    """Asserts that live NVML VRAM is within 5400.0 MiB ceiling and Port 8138 is healthy."""
    verifier = OmniscientKernelVerifier()
    report = verifier.verify_system_health()

    import os
    vram_ceiling = float(os.environ.get("HERMES_VRAM_CEILING_MIB", "5400.0"))
    assert report["live_nvml_vram_mib"] <= vram_ceiling, f"VRAM ceiling breached: {report['live_nvml_vram_mib']} MiB"
    assert report["port_8138_healthy"] is True, "Port 8138 llama-server is unreachable"
    assert report["vram_within_bounds"] is True


def test_statedb_and_constitutional_coverage():
    """Asserts that state.db has >= 100 sessions and SOUL.md covers Phase 25."""
    verifier = OmniscientKernelVerifier()
    report = verifier.verify_system_health()

    assert report["statedb_sessions"] >= 100, f"Expected >= 100 sessions, got {report['statedb_sessions']}"
    assert report["soul_covers_phase25"] is True, "SOUL.md constitutional coverage failed"


def test_nora_and_temporal_mutual_exclusion():
    """Asserts that NoRA Frobenius norm is 1.0 and TME is certified."""
    verifier = OmniscientKernelVerifier()
    report = verifier.verify_system_health()

    assert report["nora_frobenius_norm"] == 1.0, f"NoRA norm is {report['nora_frobenius_norm']}"
    assert report["kl_budget_respected"] is True
    assert report["temporal_mutual_exclusion_verified"] is True
    assert report["status"] == "certified_omniscient"
