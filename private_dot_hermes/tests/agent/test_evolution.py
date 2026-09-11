"""
Contract Tests: Pillar VI — Spec-Kit Driven Self-Evolution
==========================================================
Validates:
  1. EvolutionEngine initializes hypotheses and baselines directories.
  2. Seeds default Era 6 frontier hypotheses (H-001, H-002, H-003).
  3. Failure mode analysis clusters performance gaps by frequency and priority.
  4. Dynamic hypothesis proposal from detected failure clusters.
  5. Proposed hypotheses follow the github/spec-kit schema contract.
  6. Dry-run hypothesis implementation validates spec without side-effects.
  7. Live hypothesis implementation enforces the Zero-Regression Invariant.
  8. Evolution status provides full visibility into verified vs proposed hypotheses.
  9. Spec-kit contract fields (inputs, expected_output, acceptance_metric) are present.
 10. Weekly evolution cron automation script is present and executable.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import pytest

from plugins.self_evolution import EvolutionEngine, get_evolution_engine


@pytest.fixture
def temp_evolution():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = EvolutionEngine(root_dir=Path(tmpdir))
        yield engine


def test_evolution_engine_initialization(temp_evolution):
    assert temp_evolution.hypotheses_dir.exists()
    assert temp_evolution.baselines_dir.exists()
    st = temp_evolution.status()
    assert st["total_hypotheses"] >= 3


def test_default_hypotheses_seeded(temp_evolution):
    h1 = temp_evolution.hypotheses_dir / "H-001.json"
    h2 = temp_evolution.hypotheses_dir / "H-002.json"
    h3 = temp_evolution.hypotheses_dir / "H-003.json"
    assert h1.exists()
    assert h2.exists()
    assert h3.exists()

    d1 = json.loads(h1.read_text())
    assert d1["title"] == "BPE Memory Workspace Anti-Drift"
    assert d1["status"] == "verified"


def test_analyze_failure_modes_clusters(temp_evolution):
    clusters = temp_evolution.analyze_failure_modes()
    assert len(clusters) >= 3
    ids = [c["cluster_id"] for c in clusters]
    assert "F-VRAM" in ids
    assert "F-TOOL-DRIFT" in ids


def test_propose_hypotheses_generation(temp_evolution):
    proposed = temp_evolution.propose_hypotheses(top_k=2)
    assert len(proposed) == 2
    assert all("Mitigation for" in p["title"] for p in proposed)
    assert all(p["status"] == "proposed" for p in proposed)


def test_propose_hypotheses_persisted_to_disk(temp_evolution):
    proposed = temp_evolution.propose_hypotheses(top_k=1)
    hid = proposed[0]["id"]
    file_path = temp_evolution.hypotheses_dir / f"{hid}.json"
    assert file_path.exists()
    data = json.loads(file_path.read_text())
    assert data["id"] == hid


def test_implement_hypothesis_dry_run(temp_evolution):
    res = temp_evolution.implement_hypothesis("H-001", dry_run=True)
    assert res["status"] == "DRY_RUN_PASSED"
    assert res["zero_regression_guard"] == "ACTIVE"


def test_implement_hypothesis_live_execution(temp_evolution):
    # Propose new hypothesis
    proposed = temp_evolution.propose_hypotheses(top_k=1)[0]
    hid = proposed["id"]

    res = temp_evolution.implement_hypothesis(hid, dry_run=False)
    assert res["status"] == "SUCCESS"
    assert res["zero_regression_verified"] is True

    # Verify status changed on disk
    file_path = temp_evolution.hypotheses_dir / f"{hid}.json"
    data = json.loads(file_path.read_text())
    assert data["status"] == "implemented"


def test_evolution_status_metrics(temp_evolution):
    st = temp_evolution.status()
    assert "total_hypotheses" in st
    assert "verified_hypotheses" in st
    assert st["verified_hypotheses"] >= 3


def test_spec_kit_contract_fields(temp_evolution):
    h1 = json.loads((temp_evolution.hypotheses_dir / "H-001.json").read_text())
    spec = h1.get("spec", {})
    assert "inputs" in spec
    assert "expected_output" in spec
    assert "acceptance_metric" in spec


def test_weekly_cron_script_executable():
    hermes_home = Path(__file__).resolve().parent.parent.parent
    cron_script = hermes_home / "cron" / "weekly_evolution.sh"
    assert cron_script.exists()
    assert os.access(cron_script, os.X_OK)


def test_implement_hypothesis_audit_logging(temp_evolution):
    res = temp_evolution.implement_hypothesis("H-001", dry_run=True)
    assert res["status"] == "DRY_RUN_PASSED"

    from plugins.agentshield import get_audit_trail
    trail = get_audit_trail()
    recent = trail.get_recent(limit=5)
    assert any("hypothesis:H-001" in e["target"] for e in recent)
