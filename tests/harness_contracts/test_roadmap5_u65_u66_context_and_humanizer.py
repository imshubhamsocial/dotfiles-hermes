"""
Harness Contract: Milestones U65 & U66 — Context Window Guard & Humanizer
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.context_window_guard import ContextWindowGuard, create_context_window_guard
from hermes_core.humanizer import Humanizer, create_humanizer


class TestContextWindowGuardContract:
    @pytest.fixture
    def guard(self) -> ContextWindowGuard:
        return create_context_window_guard()

    def test_vram_estimation_and_invariant_r5_5(self, guard: ContextWindowGuard):
        # 65536 context evaluation
        assess_65k = guard.estimate_vram(65536, slots=2)
        assert assess_65k.safe is True
        assert assess_65k.estimated_total_vram_mib < guard.ceiling

        # Best safe context selection
        best_safe = guard.select_best_safe_context(slots=2)
        assert best_safe in (131072, 98304, 65536)

    def test_config_update(self, guard: ContextWindowGuard, tmp_path: Path):
        cfg = tmp_path / "config.yaml"
        cfg.write_text("context_length: 65536\nauxiliary:\n  compression:\n    context_length: 65536\n")
        guard.update_config_context_length(cfg, 131072)
        content = cfg.read_text()
        assert "context_length: 131072" in content


class TestHumanizerContract:
    @pytest.fixture
    def humanizer(self) -> Humanizer:
        return create_humanizer(enabled=True)

    def test_strips_robotic_throat_clearing(self, humanizer: Humanizer):
        fluff = "Certainly! I'd be happy to help with that! Here is the code you requested:\n```python\nprint('hello')\n```\nLet me know if you have any other questions!"
        res = humanizer.humanize(fluff)
        assert "Certainly!" not in res.humanized_text
        assert "Let me know if you have any other questions!" not in res.humanized_text
        assert "```python\nprint('hello')\n```" in res.humanized_text
        assert res.tokens_saved > 0

    def test_preserves_factual_and_clean_code(self, humanizer: Humanizer):
        factual = "Executed observer gate on `bin/observer_gate.py`. 6/6 gates passed.\n```json\n{\"status\": \"APPROVED\"}\n```"
        res = humanizer.humanize(factual)
        assert "Executed observer gate" in res.humanized_text
        assert "{\"status\": \"APPROVED\"}" in res.humanized_text
