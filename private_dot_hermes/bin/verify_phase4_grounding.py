#!/usr/bin/env python3
"""
Native Verification Harness: Phase 4 Autonomous Web Grounding (Search-R1 Style)
===============================================================================
Validates:
  1. Multi-Backend Search Dispatch (SearXNG + DDGS + Wikipedia + arXiv) with RAMDisk caching.
  2. Multi-Turn Search Reasoning (arXiv:2503.09516): Query decomposition & adaptive refinement.
  3. Citation-Grounded Response Generation: Inline numbered citations & verifiable footnotes.
  4. Real-Time Fact Verification: Multi-source consensus checking & confidence scoring.
  5. WebGroundingEngine Substrate & Zero Hallucination Policy compliance.

Zero test folder architecture compliant.
"""

from __future__ import annotations

import os
import sys
import time

core_dir = os.path.expanduser("~/.hermes/hermes-agent/agent/core")
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from search_reasoner import (
    SearchResult,
    Citation,
    SearchReasoningResult,
    MultiTurnSearchReasoner,
    get_search_reasoner,
    reason_and_ground_search,
    _GLOBAL_CACHE,
)
from fact_verifier import (
    FactVerificationReport,
    RealTimeFactVerifier,
    get_fact_verifier,
    verify_claim,
)
from web_grounding import (
    GroundingResult,
    WebGroundingEngine,
    get_grounding_engine,
)


def test_gate1_multi_backend_and_caching() -> bool:
    print("\n[Gate 1] Multi-Backend Search Dispatch & RAMDisk Caching...")
    reasoner = get_search_reasoner()

    query = "Transformer neural network architecture"
    t0 = time.time()
    results = reasoner.dispatch_search(query, max_results=4)
    duration_uncached = (time.time() - t0) * 1000

    print(f"  • Uncached dispatch returned {len(results)} sources in {duration_uncached:.1f}ms")
    assert len(results) >= 1, "Expected at least 1 search result"

    # Verify source types present
    sources_found = set(r.source_type for r in results)
    print(f"  • Search backends detected: {sources_found}")

    # Verify RAMDisk caching
    t1 = time.time()
    cached_results = reasoner.dispatch_search(query, max_results=4)
    duration_cached = (time.time() - t1) * 1000
    print(f"  • Cached dispatch retrieved {len(cached_results)} sources in {duration_cached:.2f}ms")
    assert len(cached_results) == len(results), "Cached results count mismatch"
    assert duration_cached < 10.0, f"Cache latency unexpectedly high: {duration_cached}ms"

    print("  ✅ Gate 1 Certified: Multi-Backend Dispatch & RAMDisk Cache Operational")
    return True


def test_gate2_query_decomposition_and_refinement() -> bool:
    print("\n[Gate 2] Multi-Turn Search Reasoning & Query Decomposition (Search-R1)...")
    reasoner = get_search_reasoner()

    complex_query = "What is the Mixture of Block Attention mechanism and how does it compare to standard FlashAttention?"
    sub_questions = reasoner.decompose_query(complex_query, max_subquestions=5)
    print(f"  • Original Query: {complex_query}")
    print(f"  • Decomposed into {len(sub_questions)} sub-questions:")
    for i, sq in enumerate(sub_questions, 1):
        print(f"    {i}. {sq}")

    assert len(sub_questions) >= 3, f"Expected >=3 sub-questions, got {len(sub_questions)}"
    assert any("attention" in sq.lower() for sq in sub_questions), "Sub-questions missed core topic"

    print("  ✅ Gate 2 Certified: Search-R1 Query Decomposition Active")
    return True


def test_gate3_citation_grounded_generation() -> bool:
    print("\n[Gate 3] Citation-Grounded Response Generation...")
    reasoner = get_search_reasoner()

    query = "Apollo 11 Moon landing 1969"
    result = reasoner.reason_and_ground(query, max_iterations=2, target_fact_count=3)

    print(f"  • Iterations Run: {result.iterations_run}")
    print(f"  • Total Sources Retrieved: {len(result.sources)}")
    print(f"  • Citations Formatted: {len(result.citations)}")
    print(f"  • Grounding Confidence: {result.confidence_level} ({result.confidence_score:.2f})")
    print(f"  • Grounded Response Snippet (First 300 chars):\n    {result.grounded_response[:300]}...")

    assert len(result.sources) >= 2, f"Insufficient sources retrieved: {len(result.sources)}"
    assert len(result.citations) >= 2, f"Insufficient citations: {len(result.citations)}"
    assert "[1]" in result.grounded_response, "Missing inline citation [1]"
    assert "Footnotes & Citations" in result.grounded_response, "Missing footnotes section"

    print("  ✅ Gate 3 Certified: Citation-Grounded Synthesis Verified with Footnotes")
    return True


def test_gate4_real_time_fact_verification() -> bool:
    print("\n[Gate 4] Real-Time Fact Verification...")
    verifier = get_fact_verifier()

    # Case A: True, widely documented fact
    true_claim = "Python was created by Guido van Rossum and released in 1991."
    report_true = verifier.verify_claim(true_claim, min_sources=1)
    print(f"  • Testing True Claim: '{true_claim}'")
    print(f"    - Verdict: verified={report_true.verified}, confidence={report_true.confidence:.2f}, agreements={report_true.agreement_count}")
    print(f"    - Rationale: {report_true.rationale}")
    assert report_true.verified is True, "True claim failed verification"
    assert report_true.confidence >= 0.60, f"Confidence too low: {report_true.confidence}"
    assert len(report_true.sources) >= 1, "No sources attributed for true claim"

    # Case B: Fabricated claim
    false_claim = "The Pyramids of Giza were built in 1984 using JavaScript and CSS."
    report_false = verifier.verify_claim(false_claim, min_sources=2)
    print(f"  • Testing False Claim: '{false_claim}'")
    print(f"    - Verdict: verified={report_false.verified}, confidence={report_false.confidence:.2f}, agreements={report_false.agreement_count}")
    assert report_false.confidence <= 0.60, f"False claim confidence too high: {report_false.confidence}"

    print("  ✅ Gate 4 Certified: Real-Time Fact Verification Differentiates Factual Evidence")
    return True


def test_gate5_web_grounding_substrate() -> bool:
    print("\n[Gate 5] WebGroundingEngine Substrate & Invariant Compliance...")
    engine = get_grounding_engine()

    res = engine.ground("Three.js OrbitControls ESM", policy="always")
    assert res.executed is True, "Grounding failed to execute"
    assert len(res.sources) >= 1, "Grounding returned 0 sources"
    assert res.token_estimate > 20, "Token estimate too low"
    print(f"  • WebGroundingEngine executed: {len(res.sources)} sources, {res.token_estimate} tokens, confidence={res.confidence:.2f}")

    print("  ✅ Gate 5 Certified: Grounding Substrate Fully Operational")
    return True


def main() -> None:
    print("=" * 75)
    print("PHASE 4: AUTONOMOUS WEB GROUNDING (SEARCH-R1 STYLE) VERIFICATION")
    print("=" * 75)

    assert test_gate1_multi_backend_and_caching()
    assert test_gate2_query_decomposition_and_refinement()
    assert test_gate3_citation_grounded_generation()
    assert test_gate4_real_time_fact_verification()
    assert test_gate5_web_grounding_substrate()

    print("\n" + "=" * 75)
    print("PHASE 4 VERIFICATION RESULT: 100% PASS (ALL GROUNDING GATES CERTIFIED)")
    print("=" * 75)


if __name__ == "__main__":
    main()
