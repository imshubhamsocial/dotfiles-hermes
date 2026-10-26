"""Unit test suite for SessionStore."""

import pytest
from session_store import SessionStore


def test_session_lifecycle():
    store = SessionStore(ttl_seconds=60.0)
    store.set("sess_1", {"user": "alice"})
    store.set("sess_2", {"user": "bob"})

    assert store.count() == 2
    assert store.get("sess_1") == {"user": "alice"}
    assert store.get("sess_nonexistent") is None


def test_purge_expired_sessions():
    store = SessionStore(ttl_seconds=10.0)
    base_time = 1000.0

    # Create 5 sessions at base_time
    for i in range(5):
        store._sessions[f"s_{i}"] = {
            "data": {"id": i},
            "created_at": base_time,
            "last_accessed": base_time
        }

    assert store.count() == 5

    # Access session 0 to refresh it at base_time + 5
    store._sessions["s_0"]["last_accessed"] = base_time + 5.0

    # Purge at base_time + 12 (sessions 1..4 are expired, session 0 is alive)
    purged = store.purge_expired(current_time=base_time + 12.0)

    assert purged == 4
    assert store.count() == 1
    assert store.get("s_0") == {"id": 0}
