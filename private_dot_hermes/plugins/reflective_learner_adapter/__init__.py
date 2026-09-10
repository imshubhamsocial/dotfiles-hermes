"""Hermes Plugin: reflective_learner_adapter"""

from .experience_store import (
    EpisodeRecord,
    ExperienceStore,
    create_experience_store,
)
from .trajectory import (
    TrajectoryRecorder,
    init_observability,
    get_trajectory_tracer,
    active_path,
    load_events,
    verify_chain,
    events_to_otel_spans,
    flush_to_milestone_disk,
)
from .hooks.on_session_end import on_session_end

def register(ctx=None):
    """Registers plugin reflective_learner_adapter into Hermes runtime."""
    if ctx and hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_end", on_session_end)

__all__ = [
    "EpisodeRecord",
    "ExperienceStore",
    "create_experience_store",
    "TrajectoryRecorder",
    "init_observability",
    "get_trajectory_tracer",
    "active_path",
    "load_events",
    "verify_chain",
    "events_to_otel_spans",
    "flush_to_milestone_disk",
    "on_session_end",
    "register",
]
