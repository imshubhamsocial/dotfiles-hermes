"""
Quorum Audit Pre-Tool-Call Hook: Enforces Author != Auditor Maker/Verifier Invariant.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def pre_tool_call(
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    session_id: str = "",
    task_id: str = "",
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """
    Enforces maker/verifier structural separation before tool dispatch.
    1. If invoking an audit check (quorum_audit_check), author and auditor MUST be distinct.
    2. If agent identity is 'tester', mutating file tools (write_file, patch) are strictly blocked.
    3. If agent identity is 'coder', self-audit signoff is blocked.
    """
    args = args or {}
    current_role = kwargs.get("role", "") or ""

    # Invariant 1: Quorum Audit check must have Author != Auditor
    if tool_name in ("quorum_audit_check", "audit_code", "verify_task"):
        author = args.get("author") or args.get("author_agent") or ""
        auditor = args.get("auditor") or args.get("auditor_agent") or current_role or ""
        if author and auditor and author.strip().lower() == auditor.strip().lower():
            return {
                "action": "block",
                "message": (
                    f"Quorum Violation: Author '{author}' cannot audit its own code. "
                    "Maker and Verifier must remain strictly distinct (Author != Auditor)."
                ),
            }

    # Invariant 2: @tester cannot mutate files
    if "tester" in current_role.lower() or kwargs.get("agent_profile") == "tester":
        if tool_name in ("write_file", "patch", "patch_file"):
            return {
                "action": "block",
                "message": (
                    f"Quorum Violation: Role '@tester' has read/exec capability only. "
                    f"Mutating tool '{tool_name}' is forbidden for verifiers."
                ),
            }

    return None
