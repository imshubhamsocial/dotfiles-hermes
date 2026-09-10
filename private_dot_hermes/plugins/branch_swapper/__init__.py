"""
Hermes Plugin: branch_swapper
=============================
Autonomous Hypothesis Tree Branch Swapper & Tabu Pruner (Two-Strike Tabu MCTS).
Detects fixations and repair loops in execution, triggers branch swaps, and accumulates negative boundary constraints.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .branch_swapper import (
    BranchSwapper,
    NegativeConstraint,
    RepairTurn,
    SwapTrigger,
    TabuPattern,
    create_branch_swapper,
)
from .hypothesis_tree import (
    HypothesisNode,
    HypothesisTree,
    get_hypothesis_tree,
)


def register(ctx=None):
    """Registers plugin branch_swapper into Hermes runtime."""
    if not ctx:
        return True

    # 1. Native CLI command: hermes hypothesis [status | branch | backtrack]
    if hasattr(ctx, "register_cli_command"):
        def setup_hypothesis(parser):
            parser.description = "Inspect and manage MCTS hypothesis tree and Tabu constraints"
            subparsers = parser.add_subparsers(dest="subcommand", help="Hypothesis actions")

            subparsers.add_parser("status", help="Show current active branch and accumulated constraints")

            branch_p = subparsers.add_parser("branch", help="Add a new exploratory branch")
            branch_p.add_argument("title", help="Branch title")
            branch_p.add_argument("hypothesis", help="Hypothesis description")

            backtrack_p = subparsers.add_parser("backtrack", help="Backtrack from active branch on failure")
            backtrack_p.add_argument("reason", help="Failure reason / trace")
            backtrack_p.add_argument("--constraint", default="Learned negative boundary constraint", help="Boundary constraint")

        def handle_hypothesis(args):
            subcmd = getattr(args, "subcommand", None) or "status"
            tree = get_hypothesis_tree()

            if subcmd == "status":
                active_id = tree.active_node_id or "None (Root)"
                active_node = tree.nodes.get(tree.active_node_id) if tree.active_node_id else None
                constraints = tree.get_accumulated_negative_constraints()
                print(f"Hypothesis Tree Status:")
                print(f"  Total Nodes: {len(tree.nodes)}")
                print(f"  Active Branch: [{active_id}] {active_node.title if active_node else 'N/A'}")
                if active_node:
                    print(f"  Hypothesis: {active_node.hypothesis}")
                    print(f"  Status: {active_node.status}")
                print(f"  Accumulated Boundary Constraints ({len(constraints)}):")
                for c in constraints:
                    print(f"    - {c}")
                return 0

            elif subcmd == "branch":
                node = tree.add_branch(args.title, args.hypothesis)
                tree.save_state()
                print(f"✓ Created branch [{node.id}]: {node.title}")
                return 0

            elif subcmd == "backtrack":
                node = tree.record_failure_and_backtrack(args.reason, args.constraint)
                tree.save_state()
                new_id = node.id if node else "Root"
                print(f"✓ Backtracked to branch: [{new_id}]")
                return 0

            return 0

        ctx.register_cli_command("hypothesis", "Inspect and control hypothesis tree search", setup_hypothesis, handle_hypothesis)

    # 2. Native Slash command: /hypothesis
    if hasattr(ctx, "register_command"):
        def slash_hypothesis(raw_args: str) -> str:
            tree = get_hypothesis_tree()
            active_node = tree.nodes.get(tree.active_node_id) if tree.active_node_id else None
            constraints = tree.get_accumulated_negative_constraints()
            lines = [
                "**Hypothesis Tree & Tabu Search**",
                f"- **Active Branch**: `{tree.active_node_id or 'None'}` ({active_node.title if active_node else 'Root'})",
                f"- **Total Nodes**: {len(tree.nodes)}",
                f"- **Negative Boundary Constraints** ({len(constraints)}):",
            ]
            for c in constraints:
                lines.append(f"  - `{c}`")
            return "\n".join(lines)

        ctx.register_command("hypothesis", slash_hypothesis, "Show active hypothesis branch and Tabu constraints", "")

    # 3. Lifecycle Hook: pre_verify
    if hasattr(ctx, "register_hook"):
        swapper = create_branch_swapper()

        def pre_verify_hook(task_id: str = "current_task", hypothesis_id: Optional[str] = None, **kwargs):
            tree = get_hypothesis_tree()
            hyp_id = hypothesis_id or tree.active_node_id or "default_hyp"
            history = swapper.get_repair_history(task_id, hyp_id, limit=2)
            consecutive_fails = sum(1 for h in history if h.is_failure)
            if consecutive_fails >= 2:
                # Two consecutive failures detected → trigger automatic backtrack
                constraints = swapper.get_negative_constraints(task_id)
                top_constraint = constraints[-1].description if constraints else "Two consecutive repair failures"
                tree.record_failure_and_backtrack("Pre-verify consecutive repair failures", top_constraint)
                tree.save_state()
                return {
                    "action": "continue",
                    "message": f"Fixation detected on branch [{hyp_id}]: Two consecutive failures. Backtracked to parent. Apply learned constraint: {top_constraint}"
                }
            return {"action": "continue"}

        ctx.register_hook("pre_verify", pre_verify_hook)

    return True


__all__ = [
    "SwapTrigger",
    "RepairTurn",
    "TabuPattern",
    "NegativeConstraint",
    "BranchSwapper",
    "create_branch_swapper",
    "HypothesisNode",
    "HypothesisTree",
    "get_hypothesis_tree",
    "register",
]
