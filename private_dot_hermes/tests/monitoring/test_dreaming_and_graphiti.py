"""
Contract Tests: Dreaming Memory Cards & Graphiti Temporal Resolution (Phase 3)
=============================================================================
Validates:
  1. on_session_end dreaming hook creates scannable memory cards in experiential.jsonl.
  2. extract_scannable_summary generates concise, zero-overhead retrieval titles.
  3. Graphiti temporal graph integration executes cleanly.
  4. OpenLIT telemetry initialization.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import pytest

HERMES_DIR = Path(__file__).resolve().parents[2]
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))
if str(HERMES_DIR / "src") not in sys.path:
    sys.path.insert(0, str(HERMES_DIR / "src"))

from plugins.reflective_learner_adapter.hooks.on_session_end import (
    extract_scannable_summary,
    append_experiential_card,
    ingest_temporal_graphiti,
    on_session_end,
    GRAPHITI_AVAILABLE,
)
from hermes_core.trajectory import init_observability, OPENLIT_AVAILABLE


def test_dreaming_scannable_summary_extraction():
    messages = [
        {"role": "user", "content": "Refactor database migrations to use SQLModel"},
        {"role": "assistant", "content": "Created models and migration scripts."},
    ]
    title, summary = extract_scannable_summary(messages)
    assert title.startswith("Session: Refactor database migrations")
    assert len(title) <= 100
    assert "Processed 2 messages" in summary


def test_dreaming_experiential_card_persistence():
    with tempfile.TemporaryDirectory() as td:
        mem_dir = Path(td) / "memories"
        card_file = append_experiential_card(
            title="Session: Build FastMCP Server",
            summary="Processed 10 messages. FastMCP server deployed.",
            session_id="test_sess_001",
            memory_dir=mem_dir,
        )
        assert card_file.exists()
        lines = card_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["title"] == "Session: Build FastMCP Server"
        assert entry["session_id"] == "test_sess_001"
        assert "timestamp" in entry


def test_graphiti_temporal_memory_integration():
    assert GRAPHITI_AVAILABLE is True
    ok = ingest_temporal_graphiti(
        session_id="sess_temporal_test",
        summary="User updated memory retention settings",
    )
    assert ok is True


def test_openlit_telemetry_integration(monkeypatch):
    assert OPENLIT_AVAILABLE is True
    import hermes_core.trajectory as traj_mod
    monkeypatch.setattr("openlit.init", lambda **kwargs: None)
    monkeypatch.setattr(traj_mod, "_OBSERVABILITY_INITIALIZED", False)
    res = init_observability(otlp_endpoint="http://localhost:4318", application_name="hermes-test")
    assert res is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
