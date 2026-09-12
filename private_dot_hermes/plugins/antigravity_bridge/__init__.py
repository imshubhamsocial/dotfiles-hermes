"""
Hermes Plugin: antigravity_bridge
=================================
Google DeepMind Antigravity 2.0 (AGY) & Jules Cloud Agent Protocol Bridge.
Equips Hermes with:
1. AGY Artifacts Generator (GFM Alerts, Mermaid, Carousels, HTML Aux UI).
2. Gemini 3.8/4.0 Cryptographic Thought Signature Preserver.
3. Progressive Hierarchical Rule Walker (AGENTS.md / GEMINI.md).
4. Magentic-One Dual Ledgers & 2-Turn Stall Circuit Breaker.
5. A2A Agent Card Server & Jules Git Worktree Isolation Sandbox.
6. Shannon Entropy Execution Rails & Deterministic AST PRM.
"""

from __future__ import annotations

from .artifacts import AGYArtifactsManager, get_default_brain_dir
from .thought_signature import GeminiThoughtSignaturePreserver
from .rules_walker import HierarchicalRuleWalker, ProgressiveRule
from .dual_ledger import MagenticDualLedger, TaskMilestone
from .a2a_server import A2AAgentCardServer, JulesWorktreeSandbox
from .shannon_prm import ShannonEntropyRail, DeterministicCodePRM


def register(ctx=None):
    """Entry point for Hermes plugin loader: wires Antigravity 2.0 Bridge."""
    if not ctx:
        return True

    artifacts_mgr = AGYArtifactsManager()
    preserver = GeminiThoughtSignaturePreserver()

    # 1. Native CLI command: hermes agy [status | alert | mermaid]
    if hasattr(ctx, "register_cli_command"):
        def setup_agy(parser):
            parser.description = "Google DeepMind Antigravity 2.0 (AGY) Bridge & Artifacts"
            subparsers = parser.add_subparsers(dest="subcommand", help="AGY actions")
            subparsers.add_parser("status", help="Show Antigravity Bridge and brain directory status")
            alert_p = subparsers.add_parser("alert", help="Format a GitHub-style compliant alert block")
            alert_p.add_argument("level", choices=["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"], help="Alert level")
            alert_p.add_argument("text", help="Alert text content")
            mermaid_p = subparsers.add_parser("mermaid", help="Validate Mermaid diagram specification")
            mermaid_p.add_argument("chart_type", help="Chart type (e.g. 'flowchart TD', 'sequenceDiagram')")
            mermaid_p.add_argument("body", help="Chart body content")

        def handle_agy(args):
            subcmd = getattr(args, "subcommand", None) or "status"
            if subcmd == "status":
                print("Antigravity 2.0 (AGY) Bridge Status:")
                print(f"  Brain Directory: {artifacts_mgr.brain_dir}")
                print(f"  Scratch Directory: {artifacts_mgr.scratch_dir}")
                print(f"  Manifest Path: {artifacts_mgr.manifest_path}")
                print(f"  Active Thought Signatures: {len(preserver._active_signatures)}")
            elif subcmd == "alert":
                print(artifacts_mgr.format_alert(args.level, args.text))
            elif subcmd == "mermaid":
                try:
                    formatted = artifacts_mgr.format_mermaid(args.chart_type, args.body)
                    print("Mermaid diagram validated:")
                    print(formatted)
                except ValueError as e:
                    print(f"Mermaid validation error: {e}")

        ctx.register_cli_command("agy", setup_agy, handle_agy)

    # 2. Slash command: /agy
    if hasattr(ctx, "register_command"):
        def slash_agy(arg_str: str = ""):
            return (
                f"Antigravity 2.0 Bridge Active. Brain: {artifacts_mgr.brain_dir}.\n"
                f"Artifacts Manager and Gemini Thought Preserver operational."
            )

        ctx.register_command("agy", slash_agy, "Inspect Antigravity 2.0 Bridge status", "")

    return True


__all__ = [
    "AGYArtifactsManager",
    "get_default_brain_dir",
    "GeminiThoughtSignaturePreserver",
    "HierarchicalRuleWalker",
    "ProgressiveRule",
    "MagenticDualLedger",
    "TaskMilestone",
    "A2AAgentCardServer",
    "JulesWorktreeSandbox",
    "ShannonEntropyRail",
    "DeterministicCodePRM",
    "register",
]
