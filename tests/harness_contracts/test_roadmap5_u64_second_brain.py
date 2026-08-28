"""
Harness Contract: Milestone U64 & Invariant R5-4 — Cross-Session Second Brain
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.second_brain import KnowledgeCard, SecondBrain, create_second_brain


class TestSecondBrainContract:
    @pytest.fixture
    def brain(self, tmp_path: Path) -> SecondBrain:
        return create_second_brain(root_dir=tmp_path / "knowledge")

    def test_save_and_retrieve_card(self, brain: SecondBrain):
        card = KnowledgeCard(
            id="gemma-4-hybrid-attention-arch",
            title="Gemma-4 Hybrid Attention Architecture",
            category="concepts",
            content="Gemma-4 E4B pairs sliding window local layers with global attention.",
            tags=["gemma4", "architecture", "attention"],
        )
        saved_path = brain.save(card)
        assert saved_path.exists()

        retrieved = brain.get("concepts", "gemma-4-hybrid-attention-arch")
        assert retrieved is not None
        assert retrieved.title == "Gemma-4 Hybrid Attention Architecture"
        assert "gemma4" in retrieved.tags

    def test_commit_gate_invariant_r5_4(self, brain: SecondBrain):
        # Unbalanced braces must be rejected by the gate
        invalid_card = KnowledgeCard(
            id="broken-syntax",
            title="Broken Syntax Note",
            category="concepts",
            content="This note has an unbalanced brace: { missing closing brace",
        )
        with pytest.raises(ValueError, match="Second Brain Commit Gate Rejected Card"):
            brain.save(invalid_card)

    def test_search_and_list(self, brain: SecondBrain):
        c1 = KnowledgeCard(
            id="c1",
            title="Lock-Free Queue",
            category="blueprints",
            content="Ringbuffer with atomic head/tail pointers in C++20.",
            tags=["cpp20", "concurrency"],
        )
        brain.save(c1)

        search_results = brain.search("atomic pointers concurrency")
        assert len(search_results) >= 1
        assert search_results[0].id == "c1"

        all_cards = brain.list_cards()
        assert len(all_cards) == 1
