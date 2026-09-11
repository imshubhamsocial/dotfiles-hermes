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
    """Entry point for Hermes plugin loader."""
    print("Google Antigravity 2.0 Bridge Plugin registered successfully.")


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
