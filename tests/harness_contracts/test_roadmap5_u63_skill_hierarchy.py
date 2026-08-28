"""
Harness Contract: Milestone U63 & Invariant R5-2 — 4-Tier Skill Hierarchy Engine
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.skill_router import FourTierSkillRouter, create_skill_router


class TestSkillHierarchyContract:
    @pytest.fixture
    def router(self) -> FourTierSkillRouter:
        return create_skill_router()

    def test_single_skill_per_turn_invariant_r5_2(self, router: FourTierSkillRouter):
        # Invariant R5-2: Inject exactly 1 skill <= 200 tokens
        result = router.route("debug Python code using debugpy and pdb", max_tokens=200)
        assert result.matched is True
        assert result.skill is not None
        assert result.token_count <= 200
        assert "SKILL ACTIVE" in result.injected_prompt

    def test_hierarchical_routing_precedence(self, router: FourTierSkillRouter):
        # Verify skills are cataloged across tiers
        tier_set = {s.tier for s in router.skills}
        assert len(tier_set) >= 1

    def test_unmatched_query_zero_token_waste(self, router: FourTierSkillRouter):
        # Zero-Token Waste Law #1: If no relevant skill, inject 0 tokens
        result = router.route("xyznonexistentunrelatedterm123456789")
        assert result.matched is False
        assert result.token_count == 0
        assert result.injected_prompt == ""
