"""
Hermes Plugin: code_review
==========================
OpenAI Codex Autonomous AI Code Review & Superhuman Security Gate.
Provides:
  - Strict Author != Auditor persona isolation
  - PR-blocking and Turn-blocking security verification (OWASP, CWE, Portability, YAGNI)
  - Upstream Intent verification during Phase 0 / Phase 1 planning
  - Native Hermes CLI command: `hermes review <file_or_diff>`
  - Native in-session slash command: `/review <file_or_diff>`
  - Native lifecycle hook: `pre_verify`
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hermes.plugins.code_review")

_reviewer = None

def _get_reviewer():
    global _reviewer
    if _reviewer is None:
        try:
            from agent.core.code_review import AutonomousCodeReviewer
            _reviewer = AutonomousCodeReviewer()
        except ImportError:
            # Fallback path resolution
            hermes_dir = Path(__file__).resolve().parents[2]
            agent_core = hermes_dir / "hermes-agent"
            if str(agent_core) not in sys.path:
                sys.path.insert(0, str(agent_core))
            from agent.core.code_review import AutonomousCodeReviewer
            _reviewer = AutonomousCodeReviewer()
    return _reviewer


def register(ctx) -> bool:
    """Plugin lifecycle entrypoint."""

    # 1. Native CLI Commands
    if hasattr(ctx, "register_cli_command"):
        def setup_review(parser):
            parser.description = "Autonomous AI Code Review & Security Gate (OpenAI Codex paradigm)"
            parser.add_argument("target", help="File path or diff to review")
            parser.add_argument("--intent", "-i", default=None, help="Task intent to verify alignment")

        def handle_review(args):
            reviewer = _get_reviewer()
            target_p = Path(args.target)
            if target_p.exists():
                res = reviewer.review_file(target_p, intent_summary=args.intent)
            else:
                # Treat target as diff string or raw content
                res = reviewer.review_content(args.target, intent_summary=args.intent)

            print(res.to_markdown())
            return 0 if res.passed else 1

        ctx.register_cli_command(
            "review",
            "Autonomous AI code review and PR-blocking security audit",
            setup_review,
            handle_review,
        )

    # 2. Native In-Session Slash Command
    if hasattr(ctx, "register_command"):
        def slash_review(raw_args: str) -> str:
            target = raw_args.strip()
            if not target:
                return "Usage: /review <file_path_or_snippet>"
            reviewer = _get_reviewer()
            target_p = Path(target)
            if target_p.exists():
                res = reviewer.review_file(target_p)
            else:
                res = reviewer.review_content(target)
            return res.to_markdown()

        ctx.register_command("review", "Run autonomous code review and security audit", slash_review)

    # 3. Lifecycle Hook: pre_verify
    if hasattr(ctx, "register_hook"):
        def pre_verify_hook(changed_paths=None, **kwargs: Any) -> Dict[str, Any]:
            if not changed_paths:
                return {"action": "continue"}

            reviewer = _get_reviewer()
            blocking_issues = []

            for p in changed_paths:
                path = Path(p)
                if path.exists() and path.is_file():
                    res = reviewer.review_file(path)
                    if not res.passed:
                        for v in res.violations:
                            if v.severity.value in ("CRITICAL", "HIGH"):
                                blocking_issues.append(f"[{v.category.value}] {path.name}:{v.line or 1} - {v.message}")

            if blocking_issues:
                return {
                    "action": "continue",
                    "message": (
                        "OpenAI Superhuman Security Gate BLOCKED completion (STATUS: BLOCKED_BY_AUDITOR):\n"
                        + "\n".join(blocking_issues)
                        + "\nRemediate all security and portability violations before concluding."
                    ),
                }

            return {"action": "continue"}

        ctx.register_hook("pre_verify", pre_verify_hook)

    return True


__all__ = ["register", "_get_reviewer"]
