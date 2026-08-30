"""
Unified SQLite WAL Mode Database Connection Factory & Migration Engine (Issues #06 & #07)
========================================================================================
Provides thread-safe connection pooling, automatic schema migrations, and WAL mode
pragmas across all Hermes SQLite databases (~/.hermes/state.db, kanban.db, etc.).
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional


class DatabaseConnectionFactory:
    """Thread-safe SQLite connection factory with WAL mode and auto-migration."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(Path(db_path).resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_pragmas()

    def _init_pragmas(self):
        """Enable WAL mode, foreign keys, and synchronous NORMAL on initial creation."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=5000")
            # Create schema_version table for migrations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            conn.commit()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a thread-local SQLite connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA busy_timeout=5000")

        yield self._local.conn

    def apply_migration(self, version: int, description: str, migration_fn: Callable[[sqlite3.Connection], None]):
        """Run a transactional migration if it has not already been applied (Issue #07)."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM schema_versions WHERE version = ?", (version,))
                if cursor.fetchone() is not None:
                    return  # Migration already applied

                cursor.execute("BEGIN IMMEDIATE")
                try:
                    migration_fn(conn)
                    cursor.execute(
                        "INSERT INTO schema_versions (version, description) VALUES (?, ?)",
                        (version, description),
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

    def close(self):
        """Close thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None


_state_db_factory: Optional[DatabaseConnectionFactory] = None


def get_state_db_factory() -> DatabaseConnectionFactory:
    """Singleton getter for default ~/.hermes/state.db connection factory."""
    global _state_db_factory
    if _state_db_factory is None:
        db_path = Path.home() / ".hermes" / "state.db"
        _state_db_factory = DatabaseConnectionFactory(db_path)
    return _state_db_factory
