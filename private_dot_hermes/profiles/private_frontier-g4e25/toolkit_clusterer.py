#!/usr/bin/env python3
"""E4 — Tool-Planner-style toolkit clustering + tool masking (offline, deterministic).

Paper alignment: Tool-Planner (ICLR'25) — semantic tool clustering; plan at
toolkit level FIRST instead of picking from 50 raw tools. GDR-r2 E7 MERGE:
"10–15K schema tokens → top-3 tools via a 1.5B zero-shot classifier" (tool
masking). Plan row: E4 (Batch-E §5 / RESEARCH_PLAN E4).

Design decisions (4B-friendly, per Batch-E §5 + GDR E7):
    1. RULE-BASED clustering (keyword → cluster, first-match-wins, deterministic)
       — no LLM in the loop; MCP servers already group this way, so the rules
       are mostly name/verb prefixes (write_*, *search, *test …).
    2. The model sees CLUSTERS with an intent line each — it announces the
       cluster before emitting a TOOL: frame (Tool-Planner "toolkit first").
    3. ToolMasker is an INTERFACE with a deterministic keyword-overlap stub now;
       the GDR E7 1.5B classifier is a wave-2 hardware probe (interface ready,
       no harness change needed to swap the scorer).

Invariants (offline-test contract):
    1. Every tool lands in exactly one cluster; clusters ordered by definition,
       members alpha-sorted — deterministic.
    2. A tool matching no rule goes to the "General" cluster (never dropped).
    3. Masker is a pure function of (task_text, top_k) — deterministic.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

# ── cluster rules: ordered, first-match-wins ────────────────────────────────
# name/verb prefixes + description keywords, lowercased. Order matters.
CLUSTER_RULES: List[Dict[str, Any]] = [
    {"name": "Inspect", "intent": "locate & read code/data without changing it",
     "keywords": ["read", "search", "find", "grep", "query", "seek", "symbol",
                  "lookup", "inspect", "memory", "view", "list"]},
    {"name": "Verify", "intent": "run checks/tests and judge the result",
     "keywords": ["test", "verify", "check", "validate", "lint", "pytest"]},
    {"name": "Modify", "intent": "create/edit files or execute shell commands",
     "keywords": ["write", "edit", "create", "patch", "bash", "shell", "exec",
                  "run", "index", "apply", "save"]},
]

_GENERAL = {"name": "General", "intent": "anything not covered above"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


def assign_cluster(name: str, description: str) -> str:
    """First-match-wins keyword routing → cluster name (deterministic)."""
    hay = _norm(f"{name} {description}")
    for rule in CLUSTER_RULES:
        for kw in rule["keywords"]:
            # Prefix-anchored on the tool name (write_file → write_) is the
            # strongest signal; bare keyword match on description otherwise.
            if name.lower().startswith(kw) or f" {kw} " in f" {hay} ":
                return rule["name"]
    return _GENERAL["name"]


def cluster_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Cluster compressed tools (E3 output shape: name/desc) into plan blocks.

    Input tools: [{"name": str, "desc": str, ...}] (order-insensitive).
    Returns: [{"name", "intent", "members": [tool-name...]}] — members sorted,
    clusters in CLUSTER_RULES order + General last.
    """
    buckets: Dict[str, List[str]] = {}
    for t in tools:
        cluster = assign_cluster(t["name"], t.get("desc") or "")
        buckets.setdefault(cluster, []).append(t["name"])
    out: List[Dict[str, Any]] = []
    for rule in CLUSTER_RULES:
        names = buckets.pop(rule["name"], None)
        if names:
            out.append({"name": rule["name"], "intent": rule["intent"],
                        "members": sorted(names)})
    general = buckets.pop(_GENERAL["name"], None)
    if general:
        out.append({"name": _GENERAL["name"], "intent": _GENERAL["intent"],
                    "members": sorted(general)})
    # Safety: any bucket not covered by the rules still surfaces (never drops).
    for leftover, names in sorted(buckets.items()):
        out.append({"name": leftover, "intent": "unclassified",
                    "members": sorted(names)})
    return out


def render_plan_header(clusters: List[Dict[str, Any]]) -> str:
    """The Tool-Planner "plan at toolkit level" block for the system prompt."""
    lines = [
        "Plan at the TOOLKIT level first: choose a cluster, then pick a tool",
        "inside it. Announce the cluster with INTENT:<cluster> on its own line",
        "before the first tool frame of that cluster.",
    ]
    for c in clusters:
        lines.append(f"- {c['name']}: {c['intent']} — "
                     f"tools: {', '.join(c['members'])}")
    return "\n".join(lines)


# ── Tool masking (GDR E7 merge) ─────────────────────────────────────────────

Scorer = Callable[[str, str], float]  # (tool_name, task_text) → relevance


class ToolMasker:
    """Top-k tool masking.

    `scorer` defaults to deterministic keyword-overlap (stub for offline use);
    the wave-2 GDR E7 arm swaps in a 1.5B zero-shot classifier implementing the
    same callable signature — no caller change.
    """

    def __init__(self, tools: List[Dict[str, Any]], scorer: Scorer | None = None):
        self.tools = list(tools)
        self._scorer = scorer or _overlap_scorer

    def mask(self, task_text: str, top_k: int = 3) -> List[str]:
        """Return the top-k tool names for `task_text` (deterministic tie-break:
        name alpha ascending)."""
        scored = [(self._scorer(t["name"], task_text), t["name"])
                  for t in self.tools]
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [name for _, name in scored[: max(0, top_k)]]


def _overlap_scorer(name: str, task_text: str) -> float:
    """Deterministic stub: token overlap between tool name and task text.

    Tokenizes on word boundaries; scores whole-name hits + shared stems. A pure
    function of its inputs — offline-test determinism guaranteed.
    """
    name_toks = set(_norm(name).split())
    task_toks = set(_norm(task_text).split())
    if not name_toks:
        return 0.0
    hits = name_toks & task_toks
    score = float(len(hits))
    # Prefix stems (write↔writing, search↔searched) add half a point.
    for n in name_toks:
        for t in task_toks:
            if len(n) >= 4 and len(t) >= 4 and (t.startswith(n) or n.startswith(t)):
                score += 0.5
    return score
