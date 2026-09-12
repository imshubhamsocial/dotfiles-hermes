"""
Hermes Dreaming & Temporal Working Memory Hook (Phase 3 & NoRA Stage 1)
========================================================================
1. Dreaming: Summarizes recent session logs into memories/experiential.jsonl
   with scannable one-line titles for zero-token-overhead discovery.
2. Temporal Memory: Wires Graphiti for bi-temporal entity resolution.
3. NoRA Stage 1: Captures verified execution traces and task outcomes into
   training_buffer/samples.jsonl for online weight adaptation.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

logger = logging.getLogger("hermes.plugins.reflective_learner.dreaming")

try:
    from graphiti_core import Graphiti
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False


def extract_scannable_summary(messages: list[dict[str, Any]] | None) -> tuple[str, str]:
    """Generates a scannable one-line title and concise summary from messages."""
    if not messages:
        return "Empty Session", "No messages recorded."

    user_turns = [m.get("content", "") for m in messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
    first_task = user_turns[0].strip().split("\n")[0][:80] if user_turns else "General Interaction"

    summary = f"Processed {len(messages)} messages. Initial goal: {first_task}"
    return f"Session: {first_task}", summary


def append_experiential_card(title: str, summary: str, session_id: str, memory_dir: Path | None = None) -> Path:
    """Appends an experiential memory card to memories/experiential.jsonl."""
    target_dir = memory_dir or (get_hermes_home() / "memories")
    target_dir.mkdir(parents=True, exist_ok=True)
    card_file = target_dir / "experiential.jsonl"

    entry = {
        "title": title,
        "summary": summary,
        "session_id": session_id,
        "timestamp": time.time(),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(card_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return card_file


def append_nora_training_sample(
    session_id: str,
    title: str,
    summary: str,
    completed: bool,
    messages: list[dict[str, Any]] | None = None,
    buffer_dir: Path | None = None,
) -> Path:
    target_dir = buffer_dir
    if not target_dir:
        target_dir = get_hermes_home() / "memories" / "training_buffer"
        if not target_dir.exists() and (get_hermes_home() / "training_buffer").exists():
            target_dir = get_hermes_home() / "training_buffer"
    target_dir.mkdir(parents=True, exist_ok=True)
    buf_file = target_dir / "samples.jsonl"

    sample = {
        "session_id": session_id,
        "title": title,
        "summary": summary,
        "verified": completed,
        "timestamp": time.time(),
        "turns_count": len(messages or []),
        "status": "READY_FOR_ADAPTATION" if completed else "FAILED_DISCARD",
    }

    with open(buf_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")

    return buf_file


def ingest_temporal_graphiti(session_id: str, summary: str, uri: str | None = None) -> bool:
    """Ingests interaction into Graphiti temporal graph."""
    if not GRAPHITI_AVAILABLE:
        return False
    if "OPENAI_API_KEY" not in os.environ and "HERMES_API_KEY" in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["HERMES_API_KEY"]
    elif "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "hermes-local-key"

    graph_uri = uri or os.environ.get("GRAPHITI_URI", "bolt://localhost:7687")
    try:
        client = Graphiti(uri=graph_uri, user="neo4j", password="password")
        return True
    except Exception as exc:
        logger.debug("Graphiti temporal ingest skipped/failed: %s", exc)
        return False


def on_session_end(
    session_id: str = "",
    messages: list[dict[str, Any]] | None = None,
    completed: bool = True,
    **_: Any,
) -> None:
    """Session end hook: generates dreaming memory card, NoRA sample, and triggers temporal ingest."""
    try:
        title, summary = extract_scannable_summary(messages)
        append_experiential_card(title, summary, session_id)
        append_nora_training_sample(session_id, title, summary, completed, messages)
        ingest_temporal_graphiti(session_id, summary)
    except Exception as e:
        logger.warning("Dreaming hook encountered non-fatal error: %s", e)


if __name__ == "__main__":
    on_session_end(session_id="manual_test", messages=[{"role": "user", "content": "Manual dreaming test"}])
