"""
Contract Tests: Pillar I — BPE Memory Workspace (EvoHarness-RL Pattern)
========================================================================
Validates:
  1. BPE workspace directory and document initialization.
  2. Meta-Action 1: track updates belief.md with environmental truth.
  3. Meta-Action 2: commit_progress updates progress DAG checkboxes and ratios.
  4. Meta-Action 2: commit_progress appends new subgoals dynamically.
  5. Meta-Action 3: note inserts experience records with category tagging.
  6. Meta-Action 3: note increments frequency counter on duplicate insights.
  7. Meta-Action 3: note promotes recurring insights to invariants (frequency >= 3).
  8. Meta-Action 4: recall returns relevant results ordered by score.
  9. Meta-Action 4: recall filters by category taxonomy.
 10. Meta-Action 4: recall boosts promoted invariants in search ranking.
 11. BPE access log preserves immutable audit trail of all actions.
 12. Memory compaction leaves compact belief.md under threshold untouched.
 13. Memory compaction compresses bloated belief.md and archives entries.
 14. Annealing report computes routine call rates and internalization percentages.
 15. pre_turn hook formats compact context token budget under 150 tokens.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from plugins.bpe_workspace import BPEWorkspaceEngine, get_bpe_engine, register


@pytest.fixture
def temp_bpe():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = BPEWorkspaceEngine(root_dir=Path(tmpdir))
        yield engine


def test_bpe_engine_initialization(temp_bpe):
    assert temp_bpe.belief_file.exists()
    assert temp_bpe.progress_file.exists()
    assert temp_bpe.db_file.exists()
    st = temp_bpe.status()
    assert st["belief"]["exists"] is True
    assert st["progress"]["total_subgoals"] >= 5


def test_bpe_track_updates_belief(temp_bpe):
    res = temp_bpe.track({"vram": "3,400 MiB / 6,144 MiB", "git": "Clean master"})
    assert res["status"] == "success"
    content = temp_bpe.belief_file.read_text()
    assert "3,400 MiB" in content
    assert "Clean master" in content


def test_bpe_commit_progress_existing_subgoal(temp_bpe):
    res = temp_bpe.commit_progress("Pillar I: BPE Memory Workspace", "completed")
    assert res["status"] == "completed"
    assert res["completed_subgoals"] >= 1
    content = temp_bpe.progress_file.read_text()
    assert "- [x] Pillar I: BPE Memory Workspace" in content


def test_bpe_commit_progress_new_subgoal(temp_bpe):
    res = temp_bpe.commit_progress("New Feature XYZ Subgoal", "completed")
    assert res["subgoal"] == "New Feature XYZ Subgoal"
    content = temp_bpe.progress_file.read_text()
    assert "- [x] New Feature XYZ Subgoal" in content


def test_bpe_note_single_insight(temp_bpe):
    rec = temp_bpe.note("Never allocate more than 4,800 MiB VRAM", category="hardware")
    assert rec["frequency"] == 1
    assert rec["promoted"] is False
    st = temp_bpe.status()
    assert st["experience"]["total_entries"] == 1


def test_bpe_note_frequency_increment(temp_bpe):
    insight = "Always verify prefix-cache static byte parity."
    r1 = temp_bpe.note(insight, category="prompt")
    r2 = temp_bpe.note(insight, category="prompt")
    assert r1["frequency"] == 1
    assert r2["frequency"] == 2
    assert r2["promoted"] is False


def test_bpe_note_auto_promotion(temp_bpe):
    insight = "Keep AST queries scoped to active repository."
    temp_bpe.note(insight, category="ast")
    temp_bpe.note(insight, category="ast")
    r3 = temp_bpe.note(insight, category="ast")
    assert r3["frequency"] == 3
    assert r3["promoted"] is True
    st = temp_bpe.status()
    assert st["experience"]["promoted_entries"] == 1


def test_bpe_recall_exact_match(temp_bpe):
    temp_bpe.note("Use tree-sitter AST queries instead of fragile regex", category="ast")
    temp_bpe.note("Run pytest in ws-hermes container", category="docker")
    matches = temp_bpe.recall("tree-sitter regex", limit=2)
    assert len(matches) >= 1
    assert "tree-sitter" in matches[0]["insight"]


def test_bpe_recall_category_filter(temp_bpe):
    temp_bpe.note("VRAM guard strictly enforced", category="hardware")
    temp_bpe.note("Docker root isolation guard", category="security")
    matches = temp_bpe.recall("guard", category="security")
    assert len(matches) == 1
    assert matches[0]["category"] == "security"


def test_bpe_recall_promoted_boost(temp_bpe):
    # Ordinary match
    temp_bpe.note("Normal test runner guidelines", category="testing")
    # Recurring promoted match
    promoted = "Always check raw command output before claiming pass"
    temp_bpe.note(promoted, category="testing")
    temp_bpe.note(promoted, category="testing")
    temp_bpe.note(promoted, category="testing")

    matches = temp_bpe.recall("test guidelines", limit=2)
    assert len(matches) >= 1
    # The promoted insight with higher frequency should be ranked first
    assert matches[0]["promoted"] is True


def test_bpe_access_log_audit(temp_bpe):
    temp_bpe.track()
    temp_bpe.note("Audit trace insight", category="audit")
    temp_bpe.recall("trace")
    st = temp_bpe.status()
    # At least track + note + recall should be logged
    assert st["experience"]["access_log_entries"] >= 3


def test_bpe_compaction_under_threshold(temp_bpe):
    res = temp_bpe.compact_memory(threshold_chars=50000)
    assert res["compacted"] is False


def test_bpe_compaction_over_threshold(temp_bpe):
    # Artificially bloat belief file
    bloated = "# Header\n- **OS**: Linux\n" + ("Detailed log trace line here\n" * 200)
    temp_bpe.belief_file.write_text(bloated)
    res = temp_bpe.compact_memory(threshold_chars=500)
    assert res["compacted"] is True
    assert res["saved_chars"] > 0
    assert len(temp_bpe.belief_file.read_text()) < len(bloated)


def test_bpe_annealing_report_metrics(temp_bpe):
    temp_bpe.note("Frequent error workaround", category="compiler")
    temp_bpe.note("Frequent error workaround", category="compiler")
    temp_bpe.recall("error workaround")
    rep = temp_bpe.annealing_report()
    assert "categories" in rep
    assert any(c["category"] == "compiler" for c in rep["categories"])


def test_bpe_pre_turn_hook_injection(temp_bpe):
    class DummyContext:
        def __init__(self):
            self.hooks = {}
            self.cli_cmds = {}
            self.cmds = {}

        def register_hook(self, name, fn):
            self.hooks[name] = fn

        def register_cli_command(self, name, desc, setup, handler):
            self.cli_cmds[name] = handler

        def register_command(self, name, fn, desc, usage):
            self.cmds[name] = fn

    ctx = DummyContext()
    register(ctx)
    assert "pre_turn" in ctx.hooks
    hook_res = ctx.hooks["pre_turn"]()
    assert hook_res["action"] == "continue"
    assert "[BPE Memory Workspace]" in hook_res["injected_context"]
    assert len(hook_res["injected_context"]) < 500  # well within token budget


def test_bpe_compact_experiences(temp_bpe):
    # Add a recurring note (frequency >= 3)
    for _ in range(3):
        temp_bpe.note("Always use ast parsing for safe verification", category="syntax")

    # Add a one-off note (frequency 1)
    temp_bpe.note("Temporary scratch debug log", category="scratch")

    res = temp_bpe.compact_experiences(min_frequency_to_keep=2, promote_threshold=3)
    assert res["invariants_promoted_to_belief"] >= 1
    assert res["experiences_archived"] >= 1
    assert "syntax" in temp_bpe.belief_file.read_text()
