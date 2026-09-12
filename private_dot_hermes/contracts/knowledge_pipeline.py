#!/usr/bin/env python3
"""
Horizon 3 In-Process Verification Harness: Arkon MRP Knowledge Pipeline
& Traceable Graph Memory (Map -> Reduce -> Plan-Review -> Refine -> Verify -> Commit)
=====================================================================================
Verifies:
  1. Multi-Source Ingestion & Mapping (SearXNG, arXiv, Local Docs, AST)
  2. Proposition Distillation, Deduplication & Predicate Normalization (Reduce Phase)
  3. Structured Markdown Topology Blueprint Generation (Plan-Review Phase)
  4. Concept Page Refinement & Wikilink Injection without Clobbering (Refine Phase)
  5. Traceable Claims Cross-Referencing & Provenance Verification (Verify Phase)
  6. Persistence to SQLite semantic_triples.db & Concept Markdown (Commit Phase)
  7. Bidirectional Graph Traversal, Forward Links, Backlinks & Predicate Queries (WikiGraphNavigator)
"""

import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Resolve hermes-agent path dynamically
_hermes_dir = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parents[1]))
for p in [
    _hermes_dir / "hermes-agent",
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.mrp_planner import (
    ArkonMRPKnowledgeReport,
    ArkonKnowledgePipeline,
    WikiGraphNavigator,
    execute_arkon_mrp_pipeline,
)


def verify_map_and_reduce(pipeline: ArkonKnowledgePipeline, sample_sources: list) -> list:
    print("[1/6] Verifying Map & Reduce phases (Multi-source ingestion, deduplication)...")
    # 1. Map
    mapped = pipeline.map_sources(query="Hermes Autonomous Architecture", sources=sample_sources)
    assert len(mapped) >= 4, f"Expected >=4 mapped sentences, got {len(mapped)}"
    assert all("source_url" in m for m in mapped)
    print(f"  ✓ Ingested {len(mapped)} raw statements across {len(sample_sources)} diverse sources.")

    # 2. Reduce
    claims = pipeline.reduce_propositions(mapped)
    assert len(claims) >= 3, f"Expected >=3 reduced claims, got {len(claims)}"
    # Verify deduplication
    triples = [(c.subject.lower(), c.predicate, c.object.lower()) for c in claims]
    assert len(triples) == len(set(triples)), "Triples must be strictly deduplicated"
    assert any(c.predicate == "implements" for c in claims), "Expected 'implements' predicate"
    assert any(c.predicate == "depends_on" for c in claims), "Expected 'depends_on' predicate"
    print(f"  ✓ Reduced to {len(claims)} unique, normalized factual propositions.")
    return claims


def verify_plan_review_and_refine(pipeline: ArkonKnowledgePipeline, claims: list) -> tuple:
    print("[2/6] Verifying Plan-Review & Refine phases (Blueprint, concept merging)...")
    # 3. Plan-Review
    blueprint = pipeline.plan_review_blueprint(claims=claims, goal="Synthesize Hermes Knowledge Graph")
    assert "# Arkon MRP Plan-Review Blueprint" in blueprint
    assert "[[FaradayDirector]]" in blueprint or "[[PonytailLadder]]" in blueprint
    assert "Planned Concept Updates & Topology" in blueprint
    print("  ✓ Concise markdown blueprint generated with topological clusters.")

    # 4. Refine
    pages = pipeline.refine_concept_pages(claims=claims)
    assert len(pages) >= 2, f"Expected >=2 concept pages, got {len(pages)}"
    for slug, page in pages.items():
        assert page.title, "Concept title required"
        assert len(page.wikilinks) >= 1, "Expected wikilinks to be synthesized"
        md = page.render_markdown()
        assert "---" in md, "YAML frontmatter required"
        assert f'id: "{slug}"' in md
        assert "## Relational Graph & Wikilinks" in md
        assert "## Grounded Factual Claims & Provenance" in md
    print(f"  ✓ Refined {len(pages)} concept wiki pages with wikilinks and YAML frontmatter.")
    return blueprint, pages


def verify_claims_cross_referencing(pipeline: ArkonKnowledgePipeline, claims: list, sample_sources: list) -> list:
    print("[3/6] Verifying Verify phase (Traceable claims cross-referencing)...")
    verified_claims = pipeline.verify_claims(claims=claims, raw_sources=sample_sources)
    assert len(verified_claims) == len(claims)
    # The claims extracted from genuine source text must be verified
    verified_count = sum(1 for c in verified_claims if c.verified)
    assert verified_count >= 2, f"Expected >=2 verified claims, got {verified_count}"
    for c in verified_claims:
        if c.verified:
            assert c.confidence >= 0.85
    print(f"  ✓ Provenance audit complete: {verified_count}/{len(claims)} claims verified against primary sources.")
    return verified_claims


def verify_commit_phase(pipeline: ArkonKnowledgePipeline, pages: dict, verified_claims: list) -> None:
    print("[4/6] Verifying Commit phase (Persistence to SQLite semantic_triples.db and markdown)...")
    triples_count, saved_pages = pipeline.commit(pages=pages, claims=verified_claims)
    assert triples_count >= 2, f"Expected >=2 committed triples, got {triples_count}"
    assert len(saved_pages) == len(pages)

    # Verify SQLite persistence
    conn = sqlite3.connect(str(pipeline.db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM semantic_triples")
    count = cur.fetchone()[0]
    assert count >= triples_count, f"Expected database count >= {triples_count}, got {count}"

    # Verify markdown file exists on disk
    for path_str in saved_pages:
        p = Path(path_str)
        assert p.exists(), f"File {p} should exist on disk"
        content = p.read_text(encoding="utf-8")
        assert "Grounded Factual Claims & Provenance" in content
    conn.close()
    print(f"  ✓ Successfully committed {triples_count} triples to SQLite and wrote {len(saved_pages)} markdown files.")


def verify_bidirectional_traversal(knowledge_dir: Path, db_path: Path) -> None:
    print("[5/6] Verifying Bidirectional Graph Traversal (Forward links, Backlinks, Multi-hop)...")
    nav = WikiGraphNavigator(knowledge_dir=knowledge_dir, db_path=db_path)

    # 1. Forward links
    fwd_links = nav.find_forward_links("FaradayDirector")
    assert len(fwd_links) >= 1, f"Expected forward links from FaradayDirector, got {fwd_links}"
    print(f"  ✓ Forward links from 'FaradayDirector': {fwd_links}")

    # 2. Backlinks
    backlinks = nav.find_backlinks("PonytailLadder")
    assert len(backlinks) >= 1, f"Expected backlinks to PonytailLadder, got {backlinks}"
    print(f"  ✓ Backlinks pointing to 'PonytailLadder': {backlinks}")

    # 3. Multi-hop traversal
    traversal = nav.traverse(start_concept="FaradayDirector", max_depth=2)
    assert traversal["node_count"] >= 2, f"Expected >=2 visited nodes, got {traversal['node_count']}"
    assert len(traversal["edges"]) >= 1, "Expected traversal edges"
    print(f"  ✓ Multi-hop traversal explored {traversal['node_count']} nodes with {len(traversal['edges'])} relational edges.")

    # 4. Predicate queries
    dep_triples = nav.query_predicate(predicate="depends_on")
    assert len(dep_triples) >= 1, f"Expected at least 1 depends_on triple, got {dep_triples}"
    assert dep_triples[0]["predicate"] == "depends_on"
    print(f"  ✓ Predicate query for 'depends_on' returned {len(dep_triples)} match(es).")


def verify_end_to_end_pipeline(knowledge_dir: Path) -> None:
    print("[6/6] Verifying end-to-end execute_arkon_mrp_pipeline convenience interface...")
    test_sources = [
        {
            "title": "Astra Cognitive Architecture (OpenAI 2026)",
            "content": "Astra implements DualTierFusion to coordinate deep thinking models. DualTierFusion utilizes ObserverGate for pre-commit verification.",
            "url": "https://arxiv.org/abs/2609.99001",
            "kind": "arxiv",
        },
        {
            "title": "Hermes Technical Architecture Manual",
            "content": "DualTierFusion depends_on ProcessVerifier for mathematical bounds. ObserverGate verifies CodeAST safety.",
            "url": "file:///docs/hermes_arch.md",
            "kind": "local_doc",
        }
    ]

    report = execute_arkon_mrp_pipeline(
        goal="Ingest DualTierFusion specifications",
        query="DualTierFusion Astra",
        sources=test_sources,
        knowledge_dir=knowledge_dir,
    )

    assert isinstance(report, ArkonMRPKnowledgeReport)
    assert report.mapped_count >= 3
    assert report.reduced_propositions >= 2
    assert report.committed_triples >= 2
    assert len(report.committed_pages) >= 1
    assert "Astra" in report.refined_concepts or "dualtierfusion" in report.refined_concepts or "observergate" in report.refined_concepts
    print("  ✓ End-to-end Arkon MRP pipeline executed successfully:")
    print(f"    - Mapped: {report.mapped_count} | Reduced: {report.reduced_propositions} | Verified: {report.verified_claims} | Committed Triples: {report.committed_triples}")


def main():
    print("=" * 66)
    print("  HORIZON 3 IN-PROCESS VERIFICATION: ARKON MRP KNOWLEDGE PIPELINE ")
    print("  (Map -> Reduce -> Plan-Review -> Refine -> Verify -> Commit)   ")
    print("=" * 66)

    # Use a temporary clean knowledge environment for isolated testing
    temp_kdir = Path(tempfile.mkdtemp(prefix="arkon_test_"))
    try:
        pipeline = ArkonKnowledgePipeline(knowledge_dir=temp_kdir)

        sample_sources = [
            {
                "title": "Faraday Director Specification (Cognition Fusion 2026)",
                "content": "FaradayDirector implements CognitiveFusion for strategic 80/20 task assessment. FaradayDirector depends_on PonytailLadder for YAGNI pruning.",
                "url": "https://arxiv.org/abs/2609.12345",
                "kind": "arxiv",
            },
            {
                "title": "SpaceX Autonomous Build Loops Manual",
                "content": "PonytailLadder verifies DiffSimplicity to stop over-engineering. LoopOrchestrator manages ToolExecutionSubsystem in isolated sandboxes.",
                "url": "https://spacex.corp/ai/engineering.html",
                "kind": "web",
            },
            {
                "title": "Duplicate Ingestion Sample",
                "content": "FaradayDirector implements CognitiveFusion for strategic 80/20 task assessment.",
                "url": "https://arxiv.org/abs/2609.12345",
                "kind": "arxiv",
            }
        ]

        claims = verify_map_and_reduce(pipeline, sample_sources)
        blueprint, pages = verify_plan_review_and_refine(pipeline, claims)
        verified_claims = verify_claims_cross_referencing(pipeline, claims, sample_sources)
        verify_commit_phase(pipeline, pages, verified_claims)
        verify_bidirectional_traversal(knowledge_dir=temp_kdir, db_path=pipeline.db_path)
        verify_end_to_end_pipeline(knowledge_dir=temp_kdir)

    finally:
        shutil.rmtree(temp_kdir, ignore_errors=True)

    print("=" * 66)
    print("  ✅ HORIZON 3 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN   ")
    print("=" * 66)


if __name__ == "__main__":
    main()
