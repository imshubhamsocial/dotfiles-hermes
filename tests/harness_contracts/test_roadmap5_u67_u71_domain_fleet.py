"""
Harness Contract: Milestones U67-U71 & Invariant R5-3 — Domain Bot Fleet
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.domain_fleet import DomainFleetManager, create_domain_fleet_manager


class TestDomainFleetContract:
    @pytest.fixture
    def fleet(self) -> DomainFleetManager:
        return create_domain_fleet_manager()

    def test_fleet_bot_registration(self, fleet: DomainFleetManager):
        # Verify core bots and domain specialists
        expected = ["architect", "coder", "tester", "researcher", "code-review", "design", "security", "devops"]
        for b in expected:
            bot = fleet.get_bot(b)
            assert bot is not None, f"Bot '{b}' should be registered."
            assert bot.display_name.startswith("@")
            assert len(bot.guardrails) > 0

    def test_clean_room_scratchpad_isolation_invariant_r5_3(self, fleet: DomainFleetManager, tmp_path: Path):
        fleet.scratchpad_root = tmp_path
        state_arch = fleet.prepare_bot_turn("architect", "Decompose the cache subsystem", session_id="test_sess")
        assert state_arch.scratchpad_dir.exists()
        assert "architect" in str(state_arch.scratchpad_dir)

        state_coder = fleet.prepare_bot_turn("coder", "Implement cache ringbuffer", session_id="test_sess")
        assert state_coder.scratchpad_dir.exists()
        assert "coder" in str(state_coder.scratchpad_dir)
        # Verify isolation: separate directories
        assert state_arch.scratchpad_dir != state_coder.scratchpad_dir

    def test_bot_isolation_purity(self, fleet: DomainFleetManager):
        state_coder = fleet.prepare_bot_turn("coder", "Implement feature")
        # Invariant R5-3: Coder must not inherit researcher or design rules
        assert "Never write or edit code files directly" not in state_coder.system_prompt
        assert "Adhere strictly to .hermes/plan.json" in state_coder.system_prompt
