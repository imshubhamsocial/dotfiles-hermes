"""Temporal knowledge graph context plugin.

Calls upstream graphiti-core / DuckDB in pre_tool_call to track and surface
the most temporally relevant codebase entity contexts.
"""
from __future__ import annotations

import duckdb
from pathlib import Path
from typing import Any, Dict, Optional


def _get_db_path() -> Path:
    hermes_home = Path.home() / ".hermes"
    return hermes_home / "knowledge.duckdb"


def _init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_context (
                entity_id VARCHAR PRIMARY KEY,
                entity_type VARCHAR,
                name VARCHAR,
                path VARCHAR,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        """)


def _on_pre_tool_call(tool_name: str = "", args: Optional[Dict[str, Any]] = None, **_: Any) -> Optional[Dict[str, Any]]:
    """Upstream 3-line hook adapter querying the temporal entity graph."""
    db_path = _get_db_path()
    if not db_path.exists():
        _init_db(db_path)

    target_path = (args or {}).get("path") or (args or {}).get("file_path")
    if target_path:
        with duckdb.connect(str(db_path)) as conn:
            conn.execute(
                "INSERT INTO entity_context (entity_id, entity_type, name, path) "
                "VALUES (?, 'file', ?, ?) "
                "ON CONFLICT (entity_id) DO UPDATE SET updated_at = now(), access_count = entity_context.access_count + 1",
                [str(target_path), Path(str(target_path)).name, str(target_path)],
            )
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
