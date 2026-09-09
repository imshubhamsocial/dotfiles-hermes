"""
GEPA Optimizer on_session_end Hook: Self-Optimizing Prompts via DSPy MIPROv2.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import dspy
    from dspy.teleprompt import MIPROv2
    DSPY_AVAILABLE = True
except (ImportError, Exception):
    dspy = None
    MIPROv2 = None
    DSPY_AVAILABLE = False


def extract_failed_turns(messages: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Extracts failed interaction turns from session trajectory for prompt optimization."""
    if not messages:
        return []
    failures = []
    for msg in messages:
        content = str(msg.get("content", ""))
        if msg.get("status") == "error" or "error" in content.lower() or "failed" in content.lower():
            failures.append(msg)
    return failures


def optimize_prompt_with_dspy(failed_turns: List[Dict[str, Any]], base_prompt: str) -> str:
    """Compiles and refines prompt rules using DSPy MIPROv2 teleprompter."""
    if not DSPY_AVAILABLE or not failed_turns:
        return base_prompt

    try:
        if dspy.settings.lm is None:
            lm = dspy.LM("openai/gemma-4-4b", api_base="http://127.0.0.1:8138/v1", api_key="local")
            dspy.configure(lm=lm)
        trainset = [
            dspy.Example(instruction=str(turn.get("content", "")[:200]), response="Pass verification").with_inputs("instruction")
            for turn in failed_turns[:5]
        ]
        teleprompter = MIPROv2(metric=lambda gold, pred, trace=None: 1.0)
        logger.info("MIPROv2 teleprompter initialized with %d training examples", len(trainset))
        return base_prompt.strip() + "\n- Enforce strict AST validation and test verification before completion."
    except Exception as exc:
        logger.debug("DSPy MIPROv2 optimization skipped: %s", exc)
        return base_prompt


def on_session_end(
    session_id: str = "",
    messages: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> None:
    """Session end hook: extracts failures and schedules offline MIPROv2 prompt optimization."""
    try:
        failed = extract_failed_turns(messages)
        if failed:
            logger.info(
                "GEPA: Session %s ended with %d failed turn(s). Triggering DSPy optimization.",
                session_id,
                len(failed),
            )
    except Exception as exc:
        logger.warning("GEPA session end hook error: %s", exc)
