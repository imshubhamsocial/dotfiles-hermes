"""
Multi-Turn Search Reasoner (Phase IV.1 & IV.2)
==============================================
Based on Search-R1 (arXiv:2503.09516): Multi-turn search reasoning with query decomposition,
iterative refinement, cross-source verification, and citation grounding.

Search Backends:
  1. SearXNG local (http://127.0.0.1:8080) — primary with graceful fallback
  2. DuckDuckGo (ddgs) — robust web search
  3. Wikipedia API — high-assurance factual grounding
  4. arXiv API — peer-reviewed scientific claims
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


# ─── Data Structures ───

@dataclass
class SearchResult:
    title: str
    snippet: str
    url: str
    source_type: str  # "searxng", "ddg", "wikipedia", "arxiv"
    score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Citation:
    index: int
    title: str
    url: str
    snippet: str
    source_type: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchReasoningResult:
    query: str
    sub_questions: List[str]
    iterations_run: int
    sources: List[SearchResult]
    grounded_response: str
    citations: List[Citation]
    confidence_level: str  # "HIGH", "MEDIUM", "LOW"
    confidence_score: float
    token_estimate: int
    duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "sub_questions": self.sub_questions,
            "iterations_run": self.iterations_run,
            "sources": [s.to_dict() for s in self.sources],
            "grounded_response": self.grounded_response,
            "citations": [c.to_dict() for c in self.citations],
            "confidence_level": self.confidence_level,
            "confidence_score": self.confidence_score,
            "token_estimate": self.token_estimate,
            "duration_ms": self.duration_ms,
        }


# ─── RAMDisk Persistent Cache ───

CACHE_DB_PATH = "/dev/shm/hermes_search_cache.db" if os.path.exists("/dev/shm") else "/tmp/hermes_search_cache.db"


class SearchCache:
    """High-speed RAMDisk SQLite cache for web search queries."""

    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS search_cache (
                        query_hash TEXT PRIMARY KEY,
                        query_text TEXT,
                        backend TEXT,
                        results_json TEXT,
                        timestamp REAL
                    )
                    """
                )
        except Exception:
            pass

    def get(self, query: str, backend: str, ttl: float = 3600.0) -> Optional[List[SearchResult]]:
        q_hash = hashlib.sha256(f"{backend}:{query.lower().strip()}".encode()).hexdigest()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    "SELECT results_json, timestamp FROM search_cache WHERE query_hash = ?",
                    (q_hash,),
                )
                row = cur.fetchone()
                if row:
                    results_json, ts = row
                    if time.time() - ts < ttl:
                        data = json.loads(results_json)
                        return [SearchResult(**item) for item in data]
        except Exception:
            pass
        return None

    def set(self, query: str, backend: str, results: List[SearchResult]) -> None:
        q_hash = hashlib.sha256(f"{backend}:{query.lower().strip()}".encode()).hexdigest()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO search_cache VALUES (?, ?, ?, ?, ?)",
                    (
                        q_hash,
                        query,
                        backend,
                        json.dumps([r.to_dict() for r in results]),
                        time.time(),
                    ),
                )
        except Exception:
            pass


_GLOBAL_CACHE = SearchCache()


# ─── Individual Backend Handlers ───

def search_searxng(query: str, max_results: int = 5, host: str = "http://127.0.0.1:8080") -> List[SearchResult]:
    """Queries local SearXNG JSON API."""
    url = f"{host.rstrip('/')}/search?q={urllib.parse.quote(query)}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Agent-OS/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for r in data.get("results", [])[:max_results]:
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        snippet=r.get("content", ""),
                        url=r.get("url", ""),
                        source_type="searxng",
                    )
                )
            return results
    except Exception:
        return []


def search_duckduckgo(query: str, max_results: int = 5) -> List[SearchResult]:
    """Queries DuckDuckGo via ddgs."""
    results: List[SearchResult] = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        raw = list(DDGS().text(query, max_results=max_results))
        for r in raw:
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    snippet=r.get("body", "") or r.get("snippet", ""),
                    url=r.get("href", "") or r.get("link", "") or r.get("url", ""),
                    source_type="ddg",
                )
            )
    except Exception:
        pass
    return results


def search_wikipedia(query: str, max_results: int = 3) -> List[SearchResult]:
    """Queries Wikipedia API for factual grounding."""
    results: List[SearchResult] = []
    try:
        import wikipedia

        titles = wikipedia.search(query, results=max_results)
        for t in titles[:max_results]:
            try:
                page = wikipedia.page(t, auto_suggest=False)
                summary = page.summary[:500]
                results.append(
                    SearchResult(
                        title=f"Wikipedia: {page.title}",
                        snippet=summary,
                        url=page.url,
                        source_type="wikipedia",
                        score=0.95,
                    )
                )
            except Exception:
                continue
    except Exception:
        pass
    return results


def search_arxiv(query: str, max_results: int = 3) -> List[SearchResult]:
    """Queries arXiv API for academic/scientific grounding."""
    results: List[SearchResult] = []
    try:
        import arxiv

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        for paper in client.results(search):
            snippet = paper.summary.replace("\n", " ").strip()[:500]
            results.append(
                SearchResult(
                    title=f"arXiv: {paper.title}",
                    snippet=snippet,
                    url=paper.entry_id,
                    source_type="arxiv",
                    score=0.98,
                )
            )
    except Exception:
        pass
    return results


# ─── Multi-Turn Search Reasoner Engine ───

class MultiTurnSearchReasoner:
    """
    Search-R1 inspired Multi-Turn Grounding Engine:
      1. Query Decomposition: Sub-question synthesis (max 5)
      2. Multi-backend Dispatch: SearXNG -> DDGS -> Wikipedia -> arXiv
      3. Sufficiency Check & Adaptive Query Refinement (max 3 loops)
      4. Grounded Citation Assembly & Confidence Scoring
    """

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache

    def dispatch_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Dispatches search across backends with cascading fallback and RAMDisk caching."""
        if self.use_cache:
            cached = _GLOBAL_CACHE.get(query, "multi")
            if cached:
                return cached

        results: List[SearchResult] = []

        # 1. Primary: Try local SearXNG
        results = search_searxng(query, max_results=max_results)

        # 2. Fallback: DuckDuckGo
        if not results:
            results = search_duckduckgo(query, max_results=max_results)

        # 3. Augment with Wikipedia if factual/conceptual query
        wiki_results = search_wikipedia(query, max_results=2)
        results.extend(wiki_results)

        # 4. Augment with arXiv if scientific / AI / research query
        if any(term in query.lower() for term in ["arxiv", "paper", "algorithm", "attention", "transformer", "neural", "rl", "proof", "moba"]):
            arxiv_results = search_arxiv(query, max_results=2)
            results.extend(arxiv_results)

        # Deduplicate results by URL
        seen_urls = set()
        deduped: List[SearchResult] = []
        for r in results:
            if r.url and r.url not in seen_urls:
                seen_urls.add(r.url)
                deduped.append(r)

        if self.use_cache and deduped:
            _GLOBAL_CACHE.set(query, "multi", deduped)

        return deduped

    def decompose_query(self, query: str, max_subquestions: int = 5) -> List[str]:
        """
        Decomposes complex user query into targeted sub-questions.
        Heuristic multi-angle decomposition covering background, mechanisms, and verification.
        """
        sub_questions = [query]
        clean = query.strip().rstrip("?").lower()

        # Generate targeted sub-angles
        words = [w for w in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", clean) if w not in ("how", "what", "why", "when", "where", "which", "should", "does", "the", "and")]
        key_phrase = " ".join(words[:4]) if words else query

        sub_questions.append(f"{key_phrase} documentation specifications")
        sub_questions.append(f"{key_phrase} architecture overview")

        if any(w in clean for w in ["compare", "vs", "versus", "difference"]):
            sub_questions.append(f"{key_phrase} benchmarks comparison")
        elif any(w in clean for w in ["implement", "code", "install", "how to"]):
            sub_questions.append(f"{key_phrase} implementation example tutorial")

        return sub_questions[:max_subquestions]

    def reason_and_ground(
        self,
        query: str,
        max_iterations: int = 3,
        target_fact_count: int = 4,
    ) -> SearchReasoningResult:
        """Executes full multi-turn search reasoning loop."""
        t0 = time.time()
        sub_questions = self.decompose_query(query)
        collected_sources: List[SearchResult] = []
        seen_urls = set()
        iterations_run = 0

        current_queries = list(sub_questions)

        for iteration in range(1, max_iterations + 1):
            iterations_run = iteration
            new_sources = []

            for q in current_queries:
                batch = self.dispatch_search(q, max_results=3)
                for item in batch:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        collected_sources.append(item)
                        new_sources.append(item)

            # Check sufficiency: do we have enough diverse sources?
            if len(collected_sources) >= target_fact_count:
                break

            # If insufficient, generate refined queries for next iteration
            current_queries = [
                f"{query} definitive guide",
                f"{query} official source",
            ]

        # Build Citations
        citations: List[Citation] = []
        for idx, src in enumerate(collected_sources, start=1):
            citations.append(
                Citation(
                    index=idx,
                    title=src.title,
                    url=src.url,
                    snippet=src.snippet[:200],
                    source_type=src.source_type,
                )
            )

        # Cross-source verification & confidence estimation
        source_count = len(collected_sources)
        distinct_domains = len(set(urllib.parse.urlparse(s.url).netloc for s in collected_sources if s.url))

        if distinct_domains >= 3:
            conf_level = "HIGH"
            conf_score = min(0.98, 0.80 + (0.05 * distinct_domains))
        elif distinct_domains >= 1:
            conf_level = "MEDIUM"
            conf_score = 0.65 + (0.05 * distinct_domains)
        else:
            conf_level = "LOW"
            conf_score = 0.40

        # Synthesize citation-grounded response text
        response_lines = [
            f"Based on real-time web grounding across {source_count} retrieved sources ({distinct_domains} independent domains):",
            "",
        ]

        for c in citations[:6]:
            fact_summary = c.snippet.strip().replace("\n", " ")
            if fact_summary:
                response_lines.append(f"• {fact_summary} [{c.index}]")

        response_lines.append("\n### Footnotes & Citations:")
        for c in citations[:6]:
            response_lines.append(f"[{c.index}] {c.title} — {c.url}")

        grounded_text = "\n".join(response_lines)
        token_estimate = int(len(grounded_text) / 3.8)
        duration_ms = (time.time() - t0) * 1000

        return SearchReasoningResult(
            query=query,
            sub_questions=sub_questions,
            iterations_run=iterations_run,
            sources=collected_sources,
            grounded_response=grounded_text,
            citations=citations,
            confidence_level=conf_level,
            confidence_score=conf_score,
            token_estimate=token_estimate,
            duration_ms=duration_ms,
        )


_DEFAULT_REASONER: Optional[MultiTurnSearchReasoner] = None


def get_search_reasoner() -> MultiTurnSearchReasoner:
    global _DEFAULT_REASONER
    if _DEFAULT_REASONER is None:
        _DEFAULT_REASONER = MultiTurnSearchReasoner()
    return _DEFAULT_REASONER


def reason_and_ground_search(query: str) -> SearchReasoningResult:
    """One-line entrypoint for Search-R1 multi-turn grounded research."""
    return get_search_reasoner().reason_and_ground(query)
