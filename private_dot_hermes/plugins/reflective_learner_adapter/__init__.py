"""
Reflective Learner Adapter Plugin for Upstream Hermes Agent.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from hermes_core.reflective_learner import ReflectiveLearner, create_reflective_learner

logger = logging.getLogger(__name__)
_learner = create_reflective_learner()


def register(ctx: Any) -> None:
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_start", on_session_start)
        ctx.register_hook("on_session_end", on_session_end)
        logger.info("Reflective Learner Plugin registered successfully.")


def on_session_start(**kwargs: Any) -> Optional[Dict[str, Any]]:
    rules = _learner.get_active_distilled_rules()
    return {"injected_learned_rules": rules}


def on_session_end(**kwargs: Any) -> None:
    pass
