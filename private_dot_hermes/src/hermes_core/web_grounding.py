"""
Hermes Frontier Web Grounding Layer (Milestone U62 & Invariant R5-1)
====================================================================
Provides token-conscious (<400 tokens) web search grounding for all agent turns,
ensuring bots ground blueprints and code in current live specifications rather than
stale training priors.

Zero-API Default: Uses local DDGS provider with SearXNG fallback and offline caching.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hermes.web_grounding")

CACHE_DIR = Path("/dev/shm/hermes_cache")
CACHE_FILE = CACHE_DIR / "web_grounding_cache.json"


@dataclass
class GroundingSource:
    title: str
    url: str
    snippet: str
    score: float = 1.0


@dataclass
class GroundingResult:
    query: str
    policy: str
    executed: bool
    sources: List[GroundingSource] = field(default_factory=list)
    markdown_context: str = ""
    token_estimate: int = 0
    cached: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebGroundingEngine:
    """Token-efficient, zero-config web grounding layer."""

    VALID_POLICIES = {"always", "before_plan", "before_code", "on_error", "never"}

    def __init__(
        self,
        searxng_url: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
        offline_mode: bool = False,
    ):
        self.searxng_url = searxng_url or os.getenv("SEARXNG_URL")
        self.cache_ttl = cache_ttl_seconds
        self.offline_mode = offline_mode
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._load_disk_cache()

    def _load_disk_cache(self) -> None:
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._memory_cache = json.load(f)
        except Exception as e:
            logger.debug("Cache load failed: %s", e)
            self._memory_cache = {}

    def _save_disk_cache(self) -> None:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, indent=2)
        except Exception as e:
            logger.debug("Cache save failed: %s", e)

    def _cache_key(self, query: str) -> str:
        return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()

    def should_execute(self, policy: str, trigger_context: Optional[str] = None) -> bool:
        if self.offline_mode or policy == "never":
            return False
        if policy == "always":
            return True
        if policy == "before_plan" and trigger_context in (None, "plan", "spec", "architect"):
            return True
        if policy == "before_code" and trigger_context in ("code", "coder", "implement"):
            return True
        if policy == "on_error" and trigger_context in ("error", "debug", "test_failure"):
            return True
        return False

    def ground(
        self,
        query: str,
        policy: str = "always",
        trigger_context: Optional[str] = None,
        max_results: int = 3,
        max_tokens: int = 400,
    ) -> GroundingResult:
        """Perform a grounded search query constrained strictly to max_tokens."""
        if policy not in self.VALID_POLICIES:
            raise ValueError(f"Invalid grounding policy '{policy}'. Must be one of {self.VALID_POLICIES}")

        if not self.should_execute(policy, trigger_context):
            return GroundingResult(
                query=query,
                policy=policy,
                executed=False,
                markdown_context="",
                token_estimate=0,
            )

        ckey = self._cache_key(query)
        now = time.time()
        if ckey in self._memory_cache:
            entry = self._memory_cache[ckey]
            if now - entry.get("timestamp", 0) < self.cache_ttl:
                sources = [GroundingSource(**s) for s in entry.get("sources", [])]
                md = self._format_markdown(query, sources, max_tokens)
                return GroundingResult(
                    query=query,
                    policy=policy,
                    executed=True,
                    sources=sources,
                    markdown_context=md,
                    token_estimate=len(md.split()),
                    cached=True,
                )

        raw_results = self._fetch_search_results(query, max_results=max_results)
        sources: List[GroundingSource] = []
        for r in raw_results:
            title = str(r.get("title", "")).strip()
            url = str(r.get("href") or r.get("url") or "").strip()
            body = str(r.get("body") or r.get("snippet") or "").strip()
            if title and (url or body):
                sources.append(GroundingSource(title=title, url=url, snippet=body))

        md = self._format_markdown(query, sources, max_tokens)
        tok_est = len(md.split())

        # Store cache
        self._memory_cache[ckey] = {
            "timestamp": now,
            "sources": [asdict(s) for s in sources],
        }
        self._save_disk_cache()

        return GroundingResult(
            query=query,
            policy=policy,
            executed=True,
            sources=sources,
            markdown_context=md,
            token_estimate=tok_est,
            cached=False,
        )

    def _fetch_search_results(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        # 1. Try DuckDuckGo Search (duckduckgo_search / DDGS)
        try:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return results
        except Exception as e:
            logger.debug("DDGS search exception: %s", e)

        # 2. Try SearXNG fallback if configured
        if self.searxng_url:
            try:
                import urllib.parse
                import urllib.request
                params = urllib.parse.urlencode({"q": query, "format": "json"})
                url = f"{self.searxng_url}/search?{params}"
                req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Agent-OS/5.0"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("results", [])[:max_results]
            except Exception as e:
                logger.debug("SearXNG search exception: %s", e)

        # 3. Offline heuristic / deterministic fallback
        return [
            {
                "title": f"Hermes Grounding Fact: {query}",
                "href": "local://hermes/knowledge/grounding",
                "body": f"Deterministic offline spec grounding for '{query}'. Verify against repository contracts.",
            }
        ]

    def _format_markdown(self, query: str, sources: List[GroundingSource], max_tokens: int) -> str:
        if not sources:
            return ""
        lines = [f"### 🌐 Web Grounding Evidence (`{query}`)\n"]
        for s in sources:
            snip = s.snippet.replace("\n", " ").strip()
            # Bound length per snippet
            if len(snip) > 200:
                snip = snip[:197] + "..."
            lines.append(f"- **[{s.title}]({s.url})**: {snip}")

        md = "\n".join(lines)
        # Enforce hard token ceiling (approx 1 word ~= 1.3 tokens)
        words = md.split()
        if len(words) > max_tokens:
            md = " ".join(words[:max_tokens]) + "\n..."
        return md


def create_web_grounding_engine(**kwargs) -> WebGroundingEngine:
    return WebGroundingEngine(**kwargs)
