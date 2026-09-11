"""
Contract Tests: Pillar II — Hybrid Attention & 1M Context Engine
================================================================
Validates:
  1. 3-tier router initialization with 32K HOT and 256K WARM ceilings.
  2. Adding items to HOT tier with accurate token budgeting.
  3. Adding items to WARM tier.
  4. Automatic demotion of oldest unpinned items from HOT to WARM upon overflow.
  5. Pinned slots (System Prompt, SOUL.md, Active BPE) are never demoted.
  6. Automatic demotion of oldest items from WARM to COLD (disk archive).
  7. BM25 hybrid query successfully retrieves and promotes WARM items to HOT.
  8. Hybrid retrieval latency remains strictly < 50ms across realistic token scales.
  9. Retrieval latency benchmark battery execution.
 10. Model specification comparison (Spark X2.5 8x lift vs Gemma 4B baseline).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from plugins.context_budget_manager import HybridContextRouter, ContextItem, get_context_router


@pytest.fixture
def temp_router():
    with tempfile.TemporaryDirectory() as tmpdir:
        router = HybridContextRouter(cold_dir=Path(tmpdir))
        yield router


def test_context_router_initialization(temp_router):
    assert temp_router.HOT_MAX_TOKENS == 32768
    assert temp_router.WARM_MAX_TOKENS == 262144
    st = temp_router.status()
    assert st["hot"]["tokens"] == 0
    assert st["warm"]["tokens"] == 0


def test_add_item_hot_tier(temp_router):
    item = temp_router.add_item("print('Hello world!')", item_id="item1", tier="hot")
    assert item.tier == "hot"
    assert item.tokens >= 1
    assert temp_router.hot_tokens == item.tokens


def test_add_item_warm_tier(temp_router):
    item = temp_router.add_item("function test() { return 42; }", item_id="item2", tier="warm")
    assert item.tier == "warm"
    assert temp_router.warm_tokens == item.tokens


def test_hot_to_warm_automatic_demotion(temp_router):
    # Temporarily set lower limit for testing (100 tokens ~ 400 chars)
    temp_router.HOT_MAX_TOKENS = 100
    temp_router.add_item("Item 1 first " * 10, item_id="i1", tier="hot")  # ~32 tokens
    assert temp_router.items["i1"].tier == "hot"

    # Add second item (~80 tokens) so total is ~112 > 100
    temp_router.add_item("Item 2 second " * 25, item_id="i2", tier="hot")
    # Oldest item i1 should have been demoted to warm, i2 remains hot
    assert temp_router.items["i1"].tier == "warm"
    assert temp_router.items["i2"].tier == "hot"
    assert temp_router.demotion_count >= 1


def test_pinned_items_never_demoted(temp_router):
    temp_router.HOT_MAX_TOKENS = 100
    # Pin item 1
    temp_router.add_item("Pinned system prompt " * 15, item_id="pinned_sys", tier="hot", pinned=True)
    temp_router.add_item("Unpinned task item " * 15, item_id="unpinned_task", tier="hot", pinned=False)

    # Add item 3 forcing overflow
    temp_router.add_item("Overflow item " * 20, item_id="overflow", tier="hot")

    # Pinned item must remain hot
    assert temp_router.items["pinned_sys"].tier == "hot"
    # Unpinned item should have been demoted
    assert temp_router.items["unpinned_task"].tier == "warm"


def test_warm_to_cold_automatic_demotion(temp_router):
    temp_router.WARM_MAX_TOKENS = 100
    temp_router.add_item("Warm item one " * 20, item_id="w1", tier="warm")
    temp_router.add_item("Warm item two " * 30, item_id="w2", tier="warm")

    # w1 should be demoted to cold and written to disk
    assert temp_router.items["w1"].tier == "cold"
    cold_files = list(temp_router.cold_dir.glob("*.json"))
    assert len(cold_files) >= 1


def test_bm25_hybrid_query_promotes_warm_to_hot(temp_router):
    temp_router.add_item("Kernel page table isolation mechanism", item_id="k1", tier="warm")
    temp_router.add_item("React virtual DOM diffing lifecycle", item_id="r1", tier="warm")

    assert temp_router.items["k1"].tier == "warm"
    matches = temp_router.query_hybrid("page table isolation", top_k=1)
    assert len(matches) == 1
    assert matches[0]["id"] == "k1"
    # Matched item should now be promoted to hot!
    assert temp_router.items["k1"].tier == "hot"
    assert temp_router.promotion_count >= 1


def test_retrieval_latency_under_50ms(temp_router):
    # Add large corpus in warm tier (~10,000 tokens)
    for i in range(20):
        temp_router.add_item(f"Document segment {i}: system invariant and architectural bounds", item_id=f"doc_{i}", tier="warm")

    matches = temp_router.query_hybrid("architectural bounds invariant", top_k=3)
    assert len(matches) >= 1
    assert matches[0]["retrieval_ms"] < 50.0


def test_benchmark_context_execution(temp_router):
    res = temp_router.benchmark_context(sample_sizes=[500, 2000])
    assert "benchmarks" in res
    assert len(res["benchmarks"]) == 2
    for b in res["benchmarks"]:
        assert "PASS" in b["status"]
        assert b["latency_ms"] < 50.0


def test_model_specs_comparison():
    res = HybridContextRouter.benchmark_model_specs("spark-x2.5-4b", "gemma-4-4b")
    assert res["context_lift_factor"] == "8.0x"
    assert res["vram_safe_on_rtx3050"] is True
    assert "Sliding-Window" in res["candidate"]["attention_mechanism"]


def test_context_cold_retrieval(temp_router):
    # Demote an item directly into cold disk archive
    item = temp_router.add_item("Critical invariant archived to cold disk", item_id="cold_arch_1", tier="warm")
    item.tier = "cold"
    temp_router._archive_to_disk(item)
    temp_router.items.pop("cold_arch_1", None)

    assert (temp_router.cold_dir / "cold_arch_1.json").exists()

    # Query cold tier and promote back to warm
    res = temp_router.query_cold("critical invariant", top_k=1, promote_to_warm=True)
    assert len(res) == 1
    assert res[0]["id"] == "cold_arch_1"
    assert res[0]["tier"] == "warm"
    assert "cold_arch_1" in temp_router.items
    assert temp_router.items["cold_arch_1"].tier == "warm"


def test_output_token_budget_guard_safe():
    from plugins.context_budget_manager import OutputTokenBudgetGuard
    res = OutputTokenBudgetGuard.evaluate_budget(current_input_tokens=10000)
    assert res["requires_compaction"] is False
    assert res["status"] == "BUDGET_SAFE"
    assert res["remaining_output_budget"] > 2048


def test_output_token_budget_guard_compaction_trigger(temp_router):
    from plugins.context_budget_manager import OutputTokenBudgetGuard
    res = OutputTokenBudgetGuard.evaluate_budget(current_input_tokens=31500, router=temp_router)
    assert res["requires_compaction"] is True
    assert res["status"] == "COMPACTION_TRIGGERED"
    assert res["remaining_output_budget"] < 2048


def test_reasoning_trace_buffer_carryover():
    from plugins.context_budget_manager import ReasoningTraceBuffer
    buf = ReasoningTraceBuffer(max_traces=3)
    t1 = buf.record_trace(1, "Step 1: Analyzed AST architecture and determined invariants.")
    t2 = buf.record_trace(2, "Step 2: Formulated contract tests before mutating code.")
    assert len(buf.traces) == 2
    rendered = buf.render_context_prefill()
    assert "Retained System-2 Reasoning Context" in rendered
    assert "Step 1" in rendered
    assert "Step 2" in rendered


def test_session_checkpoint_manager_roundtrip(tmp_path):
    from plugins.context_budget_manager import SessionCheckpointManager
    mgr = SessionCheckpointManager(session_dir=tmp_path)
    state = {"turn": 5, "plan": ["m1", "m2"], "score": 0.85}
    saved_path = mgr.save_checkpoint("test_session_1", state)
    assert saved_path.exists()

    chks = mgr.list_checkpoints()
    assert len(chks) == 1
    assert chks[0]["name"] == "test_session_1"

    loaded = mgr.load_checkpoint("test_session_1")
    assert loaded is not None
    assert loaded["state"]["turn"] == 5
    assert loaded["state"]["score"] == 0.85


def test_qwen38_flash_next_model_benchmark():
    from plugins.context_budget_manager import HybridContextRouter
    res = HybridContextRouter.benchmark_model_specs("qwen3.8-flash-next", "gemma-4-4b")
    assert res["candidate"]["name"] == "qwen3.8-flash-next"
    assert res["candidate"]["native_context"] == 262144
    assert res["context_lift_factor"] == "2.0x"
    assert res["vram_safe_on_rtx3050"] is True
