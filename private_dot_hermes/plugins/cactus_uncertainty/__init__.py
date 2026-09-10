"""
Hermes Plugin: cactus_uncertainty
=================================
Cactus Hybrid Uncertainty Detection & Autonomous Clarification Gate.
Connects directly to llama-server's /completion endpoint to extract real token logprobs,
computes true Shannon entropy, and combines it with action blast radius and linguistic hedging.
Triggers autonomous human clarification before high-consequence mutations occur.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

DEFAULT_BASE_URL = os.environ.get("HERMES_MODEL_BASE_URL", "http://127.0.0.1:8138")

# High-uncertainty verbalized linguistic hedges
UNCERTAINTY_HEDGES: Set[str] = {
    "unsure",
    "not sure",
    "might break",
    "might not work",
    "probably",
    "perhaps",
    "speculative",
    "guess",
    "unclear",
    "ambiguous",
    "assume without verifying",
    "could fail",
    "untested hypothesis",
    "risky",
    "conflicted",
    "doubtful",
    "tentative",
    "hesitant",
    "unverified assumption",
}

# High-certainty affirmative anchors
CERTAINTY_ANCHORS: Set[str] = {
    "verified",
    "proven",
    "asserted",
    "deterministic",
    "confirmed",
    "guaranteed",
    "passed tests",
    "formally proved",
}

# Mutating & potentially destructive tools
MUTATING_TOOLS: Set[str] = {
    "write_file",
    "patch_file",
    "rm_file",
    "delete_file",
    "apply_diff",
    "modify_file",
}

DESTRUCTIVE_COMMAND_PATTERNS: List[str] = [
    r"\brm\s+-[rf]{1,2}\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[xfd]{1,3}\b",
    r"\bdrop\s+database\b",
    r"\bdrop\s+table\b",
    r"\btruncate\s+table\b",
    r"\bmkfs\b",
    r"\bkill\s+-9\b",
]


def extract_real_logprobs(
    prompt: str,
    n_probs: int = 5,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 3.0,
) -> Optional[List[Dict[str, Any]]]:
    """
    Queries local llama-server for true token logprob distribution.
    Returns list of {'token': str, 'logprob': float, 'prob': float}.
    """
    try:
        url = f"{base_url.rstrip('/')}/completion"
        payload = {
            "prompt": prompt,
            "n_predict": 1,
            "n_probs": n_probs,
            "temperature": 1.0,
        }
        resp = httpx.post(url, json=payload, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            comp_probs = data.get("completion_probabilities", [])
            if comp_probs and "top_logprobs" in comp_probs[0]:
                results = []
                for item in comp_probs[0]["top_logprobs"]:
                    lp = float(item.get("logprob", 0.0))
                    p = math.exp(lp)
                    results.append({
                        "token": item.get("token", ""),
                        "logprob": lp,
                        "prob": p,
                    })
                return results
    except Exception:
        pass
    return None


def compute_shannon_entropy(top_logprobs: List[Dict[str, Any]]) -> float:
    """
    Computes real Shannon entropy H = -sum(p * ln(p)) over normalized probabilities.
    """
    if not top_logprobs:
        return 0.0

    raw_probs = [item.get("prob", math.exp(item.get("logprob", -10.0))) for item in top_logprobs]
    total_p = sum(raw_probs)
    if total_p <= 0:
        return 0.0

    # Normalize to form valid probability distribution
    norm_probs = [p / total_p for p in raw_probs]

    entropy = 0.0
    for p in norm_probs:
        if p > 1e-12:
            entropy -= p * math.log(p)
    return round(entropy, 4)


def analyze_verbal_hedges(text: str) -> Dict[str, Any]:
    """Scans for linguistic hedging markers and certainty anchors."""
    lower = text.lower()
    hedges_found = [h for h in UNCERTAINTY_HEDGES if h in lower]
    anchors_found = [a for a in CERTAINTY_ANCHORS if a in lower]
    hedge_score = min(1.0, len(hedges_found) * 0.25)
    anchor_discount = min(0.5, len(anchors_found) * 0.2)
    final_verbal = max(0.0, hedge_score - anchor_discount)
    return {
        "score": round(final_verbal, 3),
        "hedges": hedges_found,
        "anchors": anchors_found,
    }


def compute_action_risk(tool_name: str = "", command: str = "") -> float:
    """Computes destructive blast radius for tool calls and shell commands."""
    risk = 0.0
    if tool_name.lower() in MUTATING_TOOLS:
        risk = max(risk, 0.4)

    if command:
        for pattern in DESTRUCTIVE_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                risk = max(risk, 0.85)
                break
    return risk


def evaluate_hybrid_uncertainty(
    prompt: str,
    verbal_text: str = "",
    tool_name: str = "",
    command: str = "",
    base_url: str = DEFAULT_BASE_URL,
) -> Dict[str, Any]:
    """
    Synthesizes real model logprob entropy, linguistic hedging, and action risk
    into a calibrated uncertainty metric [0.0, 1.0].
    """
    # 1. Logprob Shannon entropy
    real_probs = extract_real_logprobs(prompt, base_url=base_url)
    if real_probs:
        raw_entropy = compute_shannon_entropy(real_probs)
        # Max entropy for 5 tokens is ln(5) ~= 1.609
        normalized_entropy = min(1.0, raw_entropy / 1.609)
        entropy_source = "llama-server"
    else:
        # Fallback if server offline: assume baseline uncertainty
        raw_entropy = 0.0
        normalized_entropy = 0.2
        entropy_source = "offline-fallback"

    # 2. Verbal hedging
    verbal = analyze_verbal_hedges(verbal_text or prompt)

    # 3. Action blast radius
    action_risk = compute_action_risk(tool_name, command)

    # Hybrid blend: 40% model logprob entropy, 30% linguistic hedging, 30% action risk
    hybrid_score = round(
        0.4 * normalized_entropy + 0.3 * verbal["score"] + 0.3 * action_risk,
        3
    )

    threshold = 0.65
    should_clarify = hybrid_score >= threshold

    return {
        "hybrid_score": hybrid_score,
        "threshold": threshold,
        "should_clarify": should_clarify,
        "raw_entropy": raw_entropy,
        "normalized_entropy": round(normalized_entropy, 3),
        "entropy_source": entropy_source,
        "verbal": verbal,
        "action_risk": round(action_risk, 3),
        "top_tokens": [item["token"] for item in (real_probs or [])][:3],
    }


def register(ctx=None):
    """Registers cactus_uncertainty into Hermes runtime."""
    if not ctx:
        return True

    # 1. Native CLI command: hermes uncertainty <prompt>
    if hasattr(ctx, "register_cli_command"):
        def setup_uncertainty(parser):
            parser.description = "Evaluate Cactus hybrid uncertainty and clarification gate"
            parser.add_argument("prompt", help="Prompt or task plan to evaluate")
            parser.add_argument("--tool", default="", help="Pending tool name")
            parser.add_argument("--command", default="", help="Pending shell command")
            parser.add_argument("--json", action="store_true", help="Output as JSON")

        def handle_uncertainty(args):
            res = evaluate_hybrid_uncertainty(
                args.prompt,
                verbal_text=args.prompt,
                tool_name=args.tool,
                command=args.command,
            )
            if getattr(args, "json", False):
                print(json.dumps(res, indent=2))
            else:
                verdict = "CLARIFY BEFORE PROCEEDING" if res["should_clarify"] else "SAFE TO PROCEED"
                mark = "!" if res["should_clarify"] else "✓"
                print(f"Cactus Uncertainty Gate: [{mark}] {verdict}")
                print(f"  Hybrid Score:       {res['hybrid_score']} (Threshold: {res['threshold']})")
                print(f"  Logprob Entropy:    {res['raw_entropy']} (Source: {res['entropy_source']})")
                print(f"  Verbal Hedge Score: {res['verbal']['score']}")
                print(f"  Action Risk:        {res['action_risk']}")
                if res["top_tokens"]:
                    print(f"  Top Tokens:         {res['top_tokens']}")
            return 0 if not res["should_clarify"] else 1

        ctx.register_cli_command("uncertainty", "Evaluate Cactus hybrid uncertainty gate", setup_uncertainty, handle_uncertainty)

    # 2. Native Slash command: /uncertainty <prompt>
    if hasattr(ctx, "register_command"):
        def slash_uncertainty(raw_args: str) -> str:
            prompt = raw_args.strip()
            if not prompt:
                return "Usage: /uncertainty <prompt_or_action_plan>"
            res = evaluate_hybrid_uncertainty(prompt, verbal_text=prompt)
            verdict = "⚠️ CLARIFY BEFORE PROCEEDING" if res["should_clarify"] else "✓ SAFE TO PROCEED"
            return (
                f"**Cactus Uncertainty Gate**: {verdict}\n"
                f"- **Hybrid Score**: `{res['hybrid_score']}` / `{res['threshold']}`\n"
                f"- **Logprob Entropy**: `{res['raw_entropy']}` ({res['entropy_source']})\n"
                f"- **Verbal Hedging**: `{res['verbal']['score']}` ({len(res['verbal']['hedges'])} markers)\n"
                f"- **Action Blast Radius**: `{res['action_risk']}`"
            )

        ctx.register_command("uncertainty", slash_uncertainty, "Evaluate Cactus uncertainty on a plan", "<prompt>")

    # 3. Lifecycle hook: pre_tool_call
    if hasattr(ctx, "register_hook"):
        def pre_tool_call_hook(tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None, **kwargs):
            args = tool_args or {}
            cmd = args.get("command", "") or args.get("cmd", "")
            action_risk = compute_action_risk(tool_name, cmd)
            
            # Only gate high-risk actions
            if action_risk >= 0.7:
                res = evaluate_hybrid_uncertainty(
                    prompt=f"Execute high risk command: {cmd}",
                    verbal_text=cmd,
                    tool_name=tool_name,
                    command=cmd,
                )
                if res["should_clarify"]:
                    return {
                        "action": "block",
                        "message": f"[Cactus Gate] High destructive risk detected (score: {res['hybrid_score']}). Please request explicit user confirmation before executing: {cmd}"
                    }
            return {"action": "continue"}

        ctx.register_hook("pre_tool_call", pre_tool_call_hook)

    return True


__all__ = [
    "extract_real_logprobs",
    "compute_shannon_entropy",
    "analyze_verbal_hedges",
    "compute_action_risk",
    "evaluate_hybrid_uncertainty",
    "register",
]
