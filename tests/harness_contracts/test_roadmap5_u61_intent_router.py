"""
Harness Contract: Milestone U61 — Intent Router & Bot Class Selector
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.intent_router import IntentRouter, create_intent_router


class TestIntentRouterContract:
    @pytest.fixture
    def router(self) -> IntentRouter:
        return create_intent_router()

    def test_explicit_bot_routing_architect(self, router: IntentRouter):
        decision = router.route_intent("Hey @architect, please decompose this system")
        assert decision.target_bot.bot_class == "architect"
        assert decision.confidence == 1.0
        assert "plan" in decision.target_bot.skills_allowed

    def test_explicit_bot_routing_coder(self, router: IntentRouter):
        decision = router.route_intent("Please @coder, implement the helper functions")
        assert decision.target_bot.bot_class == "coder"
        assert decision.confidence == 1.0

    def test_explicit_bot_routing_tester(self, router: IntentRouter):
        decision = router.route_intent("@tester check why pytest is failing")
        assert decision.target_bot.bot_class == "tester"
        assert decision.confidence == 1.0

    def test_implicit_trigger_classification(self, router: IntentRouter):
        d_arch = router.route_intent("We need a formal architectural blueprint and specification")
        assert d_arch.target_bot.bot_class == "architect"
        assert d_arch.confidence > 0.5

        d_test = router.route_intent("Run the test assertions and verify dynamic invariants")
        assert d_test.target_bot.bot_class == "tester"

        d_sec = router.route_intent("Scan for CVE vulnerability and sanitize inputs")
        assert d_sec.target_bot.bot_class == "domain-security"

        d_rev = router.route_intent("Perform code review and check PR diff for maintainability")
        assert d_rev.target_bot.bot_class == "domain-code-review"

    def test_guardrails_injection(self, router: IntentRouter):
        decision = router.route_intent("Decompose the system architecture")
        assert "Never write or edit code files directly" in decision.injected_guardrails or "plan.json" in decision.injected_guardrails
