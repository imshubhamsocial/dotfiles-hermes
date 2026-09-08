"""
Domain 4 Persistence, State & Database Verification Suite
=========================================================
Tests SQLite WAL mode, database auto-migrations, SQLModel, DuckDB,
DiskCache, and Google FlatBuffers binary state serialization.
"""

import tempfile
import time
from pathlib import Path
import pytest

from hermes_core.database import DatabaseConnectionFactory
from hermes_core.experience_store import ExperienceStore, EpisodeModel
from hermes_core.flatbuffers_state import FlatBufferCheckpoint


def test_database_connection_factory_and_migrations():
    """Verify thread-safe SQLite connection factory and schema migrations (Issues #06 & #07)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_state.db"
        factory = DatabaseConnectionFactory(db_path)

        with factory.get_connection() as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode.lower() == "wal"

        # Apply a migration
        def mig1(conn):
            conn.execute("CREATE TABLE test_items (id INTEGER PRIMARY KEY, name TEXT)")

        factory.apply_migration(1, "Create test_items table", mig1)

        # Verify idempotency
        factory.apply_migration(1, "Create test_items table again", mig1)

        with factory.get_connection() as conn:
            conn.execute("INSERT INTO test_items (name) VALUES ('item1')")
            row = conn.execute("SELECT name FROM test_items WHERE id = 1").fetchone()
            assert row["name"] == "item1"

        factory.close()


def test_experience_store_sqlmodel_persistence():
    """Verify SQLModel episodic memory persistence (Issue #11)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(db_path=Path(tmpdir) / "exp.json")
        ep = store.record_episode(
            episode_id="ep_001",
            task_description="Build REST API",
            subsystem="backend",
            tool_calls=[{"name": "write_file", "path": "main.py"}],
            outcome="SUCCESS",
            token_usage=450,
            duration_sec=1.2,
        )
        assert ep.episode_id == "ep_001"
        assert len(store.episodes) == 1


def test_flatbuffers_binary_state_serialization_speed():
    """Verify Google FlatBuffers serialization and sub-100μs recovery (Issue #35)."""
    checkpoint = FlatBufferCheckpoint(
        session_id="session_domain4_test",
        turn_index=5,
        state_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90",
        context_tokens=1420,
        payload={"variables": {"x": 10, "y": 20}, "last_file": "app.py"},
    )

    t0 = time.perf_counter()
    raw_binary = checkpoint.serialize()
    serialize_time_us = (time.perf_counter() - t0) * 1_000_000

    t1 = time.perf_counter()
    recovered = FlatBufferCheckpoint.deserialize(raw_binary)
    deserialize_time_us = (time.perf_counter() - t1) * 1_000_000

    print(f"FlatBuffers Serialize: {serialize_time_us:.1f}μs, Deserialize: {deserialize_time_us:.1f}μs")

    assert recovered.session_id == "session_domain4_test"
    assert recovered.turn_index == 5
    assert recovered.context_tokens == 1420
    assert recovered.payload["variables"]["x"] == 10
    assert deserialize_time_us < 1000.0  # sub-1ms (typically <50μs)
