"""
Contract Tests for Cactus Hybrid Uncertainty Plugin
===================================================
Validates:
  1. Shannon entropy calculation across token logprob distributions
  2. Verbal linguistic hedge analysis and certainty anchors
  3. Action risk and blast radius estimation
  4. Hybrid uncertainty score calculation and clarification threshold gating
"""

import math
import pytest
from plugins.cactus_uncertainty import (
    compute_shannon_entropy,
    analyze_verbal_hedges,
    compute_action_risk,
    evaluate_hybrid_uncertainty,
)


def test_shannon_entropy_deterministic_distribution():
    # A single token with probability 1.0 has 0 entropy
    logprobs = [
        {"token": "Paris", "logprob": 0.0, "prob": 1.0},
        {"token": "London", "logprob": -10.0, "prob": 0.0},
    ]
    h = compute_shannon_entropy(logprobs)
    assert h == pytest.approx(0.0, abs=1e-3)


def test_shannon_entropy_uniform_distribution():
    # 2 tokens with equal probability 0.5 each -> H = -2 * (0.5 * ln(0.5)) = ln(2) ~= 0.6931
    logprobs = [
        {"token": "A", "logprob": -0.6931, "prob": 0.5},
        {"token": "B", "logprob": -0.6931, "prob": 0.5},
    ]
    h = compute_shannon_entropy(logprobs)
    assert h == pytest.approx(0.6931, abs=1e-3)


def test_verbal_hedges_detection():
    hedged_text = "I am unsure and guessing this might break the system, perhaps we assume without verifying."
    res = analyze_verbal_hedges(hedged_text)
    assert res["score"] > 0.5
    assert "unsure" in res["hedges"]
    assert "guessing" in res["hedges"] or "guess" in res["hedges"]


def test_certainty_anchors_discount():
    anchored_text = "I am unsure, but this is verified, deterministic, and confirmed by tests."
    res = analyze_verbal_hedges(anchored_text)
    assert "verified" in res["anchors"]
    assert "deterministic" in res["anchors"]
    assert res["score"] < 0.3


def test_compute_action_risk_destructive_commands():
    risk_safe = compute_action_risk(tool_name="read_file", command="git status")
    assert risk_safe == 0.0

    risk_mutating = compute_action_risk(tool_name="write_file")
    assert risk_mutating >= 0.4

    risk_destructive = compute_action_risk(command="rm -rf /var/log")
    assert risk_destructive >= 0.85


def test_evaluate_hybrid_uncertainty():
    res = evaluate_hybrid_uncertainty(
        prompt="Safe read query",
        verbal_text="Confirmed and verified",
        tool_name="read_file",
        command="git status",
    )
    assert res["should_clarify"] is False
    assert res["hybrid_score"] < res["threshold"]
