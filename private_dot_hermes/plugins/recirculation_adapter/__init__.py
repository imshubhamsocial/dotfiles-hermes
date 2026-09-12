"""
Google DeepMind Recirculation System-2 Prefill Hook Plugin.
Hooks into `on_session_start` and `pre_llm_call` to execute dynamical prefill passes,
evaluating task specifications for Lyapunov energy convergence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from hermes_core.recirculation import RecirculationEngine, create_recirculation_engine

logger = logging.getLogger(__name__)
_engine = create_recirculation_engine(max_iterations=3)


def register(ctx: Any) -> None:
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_start", on_session_start)
        ctx.register_hook("pre_llm_call", pre_llm_call)
        logger.info("Recirculation System-2 Prefill Plugin registered successfully (on_session_start, pre_llm_call).")


def on_session_start(prompt: str = "", **kwargs: Any) -> Optional[Dict[str, Any]]:
    if not prompt:
        return None
    try:
        res = _engine.run_recirculation_cycle(prompt)
        final_energy = res.recirculation_state.energy_history[-1] if res.recirculation_state.energy_history else 0.0
        logger.debug(
            "Recirculation passes=%d, energy=%.6f, delta=%.6f, converged=%s, lift=%.2f%%",
            res.iterations_performed,
            final_energy,
            res.recirculation_state.convergence_delta,
            res.recirculation_state.converged,
            res.reasoning_lift_pct,
        )
        return {
            "recirculation_passes": res.iterations_performed,
            "recirculation_lift": res.reasoning_lift_pct / 100.0,
            "converged": res.recirculation_state.converged,
            "energy_delta": res.recirculation_state.convergence_delta,
        }
    except Exception as exc:
        logger.warning("Recirculation prefill skipped due to exception: %s", exc)
        return None


def pre_llm_call(prompt: str = "", **kwargs: Any) -> Optional[Dict[str, Any]]:
    """Recirculate latent state prior to LLM call to prune hallucinated plan branches."""
    if not prompt:
        return None
    try:
        res = _engine.run_recirculation_cycle(prompt)
        return {
            "turn_recirculation_passes": res.iterations_performed,
            "converged": res.recirculation_state.converged,
            "energy_delta": res.recirculation_state.convergence_delta,
        }
    except Exception as exc:
        logger.warning("Recirculation pre_llm_call skipped: %s", exc)
        return None
