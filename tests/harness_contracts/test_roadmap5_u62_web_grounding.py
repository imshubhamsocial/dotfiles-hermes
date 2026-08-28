"""
Harness Contract: Milestone U62 & Invariant R5-1 — Web Grounding Layer
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.web_grounding import WebGroundingEngine, create_web_grounding_engine


class TestWebGroundingContract:
    @pytest.fixture
    def engine(self) -> WebGroundingEngine:
        return create_web_grounding_engine()

    def test_policy_filtering(self, engine: WebGroundingEngine):
        # Policy 'never' should not execute
        r_never = engine.ground("test query", policy="never")
        assert r_never.executed is False
        assert r_never.markdown_context == ""

        # Policy 'before_plan' with 'architect' context should execute
        r_plan = engine.ground("python dataclasses", policy="before_plan", trigger_context="architect")
        assert r_plan.executed is True

        # Policy 'before_plan' with 'coder' context should skip
        r_skip = engine.ground("python dataclasses", policy="before_plan", trigger_context="coder")
        assert r_skip.executed is False

    def test_token_budget_bound(self, engine: WebGroundingEngine):
        # Invariant R5-1: Bound tokens <= 400
        res = engine.ground("fastembed onnx cpu embedding", policy="always", max_tokens=150)
        assert res.executed is True
        assert res.token_estimate <= 160
        assert "Web Grounding Evidence" in res.markdown_context

    def test_cache_determinism(self, engine: WebGroundingEngine):
        q = "gemma 4 architecture deepmind"
        r1 = engine.ground(q, policy="always")
        r2 = engine.ground(q, policy="always")
        assert r2.cached is True
        assert r1.markdown_context == r2.markdown_context
