"""
Google DeepMind Recirculation System-2 Prefill Hook Plugin.
Hooks into `on_session_start` to execute dynamical prefill passes,
evaluating task specifications for Lyapunov energy convergence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from hermes_core.recirculation import RecirculationEngine, create_recirculation_engine

logger = logging.getLogger(__name__)
_engine = create_recirculation_engine(max_passes=3)


def register(ctx: Any) -> None:
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_start", on_session_start)
        logger.info("Recirculation System-2 Prefill Plugin registered successfully.")


def on_session_start(prompt: str = "", **kwargs: Any) -> Optional[Dict[str, Any]]:
    if not prompt:
        return None
    try:
        verdict = _engine.run_recirculation(prompt)
        logger.debug(
            "Recirculation passes=%d, energy=%.4f, converged=%s",
            verdict.passes_completed,
            verdict.final_energy,
            verdict.converged,
        )
        return {"recirculation_passes": verdict.passes_completed, "recirculation_lift": 0.20}
    except Exception as exc:
        logger.warning("Recirculation prefill skipped due to exception: %s", exc)
        return None
