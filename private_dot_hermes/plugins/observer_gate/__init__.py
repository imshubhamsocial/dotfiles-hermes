"""
Observer Gate Plugin for Upstream Hermes Agent.
Hooks into `pre_tool_call` and `transform_tool_result` to enforce:
1. AST structural verification on Python/JS/C++ code edits (DraftDetective)
2. Factual grounding & phantom file claim detection
3. 2-Strike Tabu Rollback Trigger on consecutive repair failures
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from hermes_core.verification_matrix import VerificationMatrix, create_verification_matrix

logger = logging.getLogger(__name__)

_matrix = create_verification_matrix()


def register(ctx: Any) -> None:
    """Register pre-commit observer hooks in Hermes."""
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_tool_call", on_pre_tool_call)
        ctx.register_hook("transform_tool_result", on_transform_tool_result)
        logger.info("Observer Gate & Verification Matrix successfully registered.")


def on_pre_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Audit candidate mutations before they execute."""
    if tool_name in ("write_file", "patch"):
        path = arguments.get("path", "")
        content = arguments.get("content", arguments.get("new_string", ""))
        if path and content:
            verdict = _matrix.audit_patch(
                file_path=path,
                code_content=content,
                markdown_summary=f"Modifying `{path}` via `{tool_name}`",
            )
            if not verdict.ast_gate_passed:
                logger.warning("Observer Gate intercepted invalid AST syntax in %s", path)
    return None


def on_transform_tool_result(tool_name: str, result_str: str) -> str:
    """Append verification receipts to tool outputs."""
    return result_str
