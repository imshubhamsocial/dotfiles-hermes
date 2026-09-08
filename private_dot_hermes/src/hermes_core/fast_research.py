"""
Fast Web Research Engine & Documentation Ingestion (Milestone U23 & D7-09)
==========================================================================
High-speed web search, modern crawl4ai / trafilatura web scraping, and
token-bounded synthesis for 4B SLMs and autonomous Agent OS sub-agents.

Features:
  1. Sub-300ms Search Provider Routing (DDGS / DuckDuckGo Lite with fallback)
  2. Async LLM-friendly Web Scraping via crawl4ai with trafilatura / regex fallbacks
  3. Concurrent multi-page batch crawling in a single browser session
  4. Token Bounding (<1,200 tokens) with ContextEngine integration
  5. RAMDisk query cache (/dev/shm/hermes_research_cache.json or :memory:)
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

# Graceful optional imports for upstream scraping engines
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, DefaultMarkdownGenerator
    CRAWL4AI_AVAILABLE = True
except (ImportError, Exception):
    CRAWL4AI_AVAILABLE = False

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except (ImportError, Exception):
    TRAFILATURA_AVAILABLE = False

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False

# Token estimation factor (~3.5 chars per token for typical tech prose)
CHAR_PER_TOKEN = 3.5
DEFAULT_RESEARCH_TOKEN_BUDGET = 1200


def _run_async_safely(coro_fn, *args, **kwargs):
    """
    Executes an async coroutine synchronously, whether or not an event loop
    is already running on the current thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro_fn(*args, **kwargs)).result()
    else:
        return asyncio.run(coro_fn(*args, **kwargs))


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    score: float = 1.0


@dataclass
class ResearchSynthesis:
    query: str
    summary_markdown: str
    sources: List[str]
    estimated_tokens: int
    duration_sec: float
    cached: bool = False


def clean_html_to_markdown(html_content: str, backend: str = "regex") -> str:
    """
    Deterministic converter from HTML to readable Markdown.
    Supports 'regex' (default lightweight cleaner stripping noise, boilerplate, scripts, styles,
    navigations, headers, and footers), 'crawl4ai', or 'trafilatura'.
    """
    if not html_content or not isinstance(html_content, str):
        return ""

    if backend == "crawl4ai" and CRAWL4AI_AVAILABLE:
        try:
            gen = DefaultMarkdownGenerator()
            res = gen.generate_markdown(html_content)
            if res and res.raw_markdown:
                return res.raw_markdown.strip()
        except Exception:
            pass

    if backend == "trafilatura" and TRAFILATURA_AVAILABLE:
        try:
            extracted = trafilatura.extract(html_content, output_format="markdown")
            if extracted:
                return extracted.strip()
        except Exception:
            pass

    # Standard deterministic regex cleaner
    # Remove script, style, head, nav, footer, header, aside, form tags
    cleaned = re.sub(
        r"<(script|style|head|nav|footer|header|aside|form|noscript|svg)[^>]*>.*?</\1>",
        "",
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Convert headings
    cleaned = re.sub(r"<h[1-3][^>]*>(.*?)</h[1-3]>", r"\n### \1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<h[4-6][^>]*>(.*?)</h[4-6]>", r"\n#### \1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Convert paragraphs and breaks
    cleaned = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    # Convert list items
    cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"• \1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Convert code blocks
    cleaned = re.sub(
        r"<pre[^>]*><code[^>]*>(.*?)</code></pre>",
        r"\n```\n\1\n```\n",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Strip remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Decode common HTML entities
    cleaned = (
        cleaned.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    # Compress whitespaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def bound_markdown_tokens(text: str, max_tokens: int = DEFAULT_RESEARCH_TOKEN_BUDGET) -> str:
    """
    Enforces a strict token ceiling on markdown outputs to avoid saturating 4B SLM contexts.
    """
    estimated = int(len(text) / CHAR_PER_TOKEN)
    if estimated <= max_tokens:
        return text

    allowed_chars = int(max_tokens * CHAR_PER_TOKEN)
    keep_head = int(allowed_chars * 0.7)
    keep_tail = int(allowed_chars * 0.25)

    truncated = (
        text[:keep_head].rstrip()
        + f"\n\n... [Research Engine: Truncated {estimated - max_tokens} tokens for token economy] ...\n\n"
        + text[-keep_tail:].lstrip()
    )
    return truncated


class FastWebResearchEngine:
    """
    Sub-300ms Web Research Engine with crawl4ai LLM-friendly scraping,
    provider fallbacks, token budget clamping, and RAMDisk result caching.
    """

    def __init__(self, cache_path: Optional[str] = "/dev/shm/hermes_research_cache.json"):
        self.cache_path = cache_path
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self):
        if self.cache_path and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self):
        if self.cache_path:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.cache_path)), exist_ok=True)
                with open(self.cache_path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=2)
            except Exception:
                pass

    def search_duckduckgo_lite(self, query: str, max_results: int = 3, timeout: float = 3.0) -> List[SearchResult]:
        """Search via DDGS if available, falling back to DuckDuckGo Lite HTML parse."""
        if DDGS_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    raw_res = list(ddgs.text(query, max_results=max_results))
                    if raw_res:
                        results = []
                        for r in raw_res:
                            results.append(
                                SearchResult(
                                    title=r.get("title", ""),
                                    url=r.get("href", ""),
                                    snippet=r.get("body", ""),
                                )
                            )
                        if results:
                            return results
            except Exception:
                pass

        try:
            search_url = "https://lite.duckduckgo.com/lite/"
            data = urllib.parse.urlencode({"q": query}).encode("utf-8")
            req = urllib.request.Request(
                search_url,
                data=data,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            matches = re.findall(
                r'<a[^>]+class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<td class="result-snippet">(.*?)</td>',
                html,
                re.DOTALL,
            )
            results = []
            for href, title, snippet in matches[:max_results]:
                clean_title = re.sub(r"<[^>]+>", "", title).strip()
                clean_snip = re.sub(r"<[^>]+>", "", snippet).strip()
                if "duckduckgo.com/l/?uddg=" in href:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if "uddg" in parsed:
                        href = parsed["uddg"][0]
                results.append(SearchResult(title=clean_title, url=href, snippet=clean_snip))
            return results
        except Exception:
            return []

    async def scrape_url_async(self, url: str, timeout: float = 5.0) -> str:
        """
        Fetch URL content and convert directly to clean Markdown using crawl4ai
        with trafilatura and deterministic regex fallbacks.
        """
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return f"[Failed to scrape {url}: Invalid URL scheme]"

        # Method 1: crawl4ai AsyncWebCrawler (Primary LLM-friendly crawler)
        if CRAWL4AI_AVAILABLE:
            try:
                b_conf = BrowserConfig(headless=True, verbose=False)
                r_conf = CrawlerRunConfig(page_timeout=int(timeout * 1000), verbose=False)
                async with AsyncWebCrawler(config=b_conf) as crawler:
                    res = await crawler.arun(url=url, config=r_conf)
                    if res and getattr(res, "success", False) and getattr(res, "markdown", None):
                        md_text = res.markdown.strip()
                        if md_text:
                            return md_text
            except Exception:
                pass

        # Method 2: trafilatura (High-speed reader extraction fallback)
        if TRAFILATURA_AVAILABLE:
            try:
                def _traf_fetch():
                    downloaded = trafilatura.fetch_url(url)
                    if downloaded:
                        return trafilatura.extract(downloaded, output_format="markdown")
                    return None

                loop = asyncio.get_running_loop()
                md = await loop.run_in_executor(None, _traf_fetch)
                if md and len(md.strip()) > 0:
                    return md.strip()
            except Exception:
                pass

        # Method 3: Python urllib + clean_html_to_markdown regex fallback
        try:
            def _http_fetch():
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw_html = resp.read().decode("utf-8", errors="replace")
                    return clean_html_to_markdown(raw_html)

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _http_fetch)
        except Exception as e:
            return f"[Failed to scrape {url}: {e}]"

    def scrape_url(self, url: str, timeout: float = 5.0) -> str:
        """Fetch URL content and convert directly to clean Markdown."""
        return _run_async_safely(self.scrape_url_async, url, timeout=timeout)

    async def scrape_urls_batch_async(self, urls: List[str], timeout: float = 5.0) -> Dict[str, str]:
        """
        Concurrently scrape multiple URLs using a single crawl4ai browser session
        for optimal speed and minimal memory overhead.
        """
        results: Dict[str, str] = {}
        valid_urls = [u for u in urls if u and (u.startswith("http://") or u.startswith("https://"))]
        if not valid_urls:
            return results

        remaining_urls = list(valid_urls)
        if CRAWL4AI_AVAILABLE:
            try:
                b_conf = BrowserConfig(headless=True, verbose=False)
                r_conf = CrawlerRunConfig(page_timeout=int(timeout * 1000), verbose=False)
                async with AsyncWebCrawler(config=b_conf) as crawler:
                    c_tasks = [crawler.arun(url=u, config=r_conf) for u in valid_urls]
                    c_results = await asyncio.gather(*c_tasks, return_exceptions=True)
                    for u, r in zip(valid_urls, c_results):
                        if (
                            not isinstance(r, Exception)
                            and getattr(r, "success", False)
                            and getattr(r, "markdown", None)
                        ):
                            md_str = r.markdown.strip()
                            if md_str:
                                results[u] = md_str
                                remaining_urls.remove(u)
            except Exception:
                pass

        if remaining_urls:
            fallback_tasks = [self.scrape_url_async(u, timeout=timeout) for u in remaining_urls]
            fallback_results = await asyncio.gather(*fallback_tasks, return_exceptions=True)
            for u, r in zip(remaining_urls, fallback_results):
                if isinstance(r, Exception):
                    results[u] = f"[Failed to scrape {u}: {r}]"
                else:
                    results[u] = r

        return results

    async def research_async(
        self,
        query: str,
        max_pages: int = 2,
        max_tokens: int = DEFAULT_RESEARCH_TOKEN_BUDGET,
        use_cache: bool = True,
    ) -> ResearchSynthesis:
        """
        Executes end-to-end fast web research with async scraping, bounding, and caching.
        """
        start_time = time.perf_counter()
        normalized_key = query.strip().lower()

        if use_cache and normalized_key in self._cache:
            entry = self._cache[normalized_key]
            dur = time.perf_counter() - start_time
            return ResearchSynthesis(
                query=query,
                summary_markdown=entry["summary_markdown"],
                sources=entry["sources"],
                estimated_tokens=entry["estimated_tokens"],
                duration_sec=dur,
                cached=True,
            )

        # 1. Search
        loop = asyncio.get_running_loop()
        search_results = await loop.run_in_executor(None, self.search_duckduckgo_lite, query, max_pages + 1)

        if not search_results:
            summary = (
                f"# Research Query: {query}\n\n"
                "No live search results returned. Proceeding with parametric baseline knowledge."
            )
            dur = time.perf_counter() - start_time
            return ResearchSynthesis(
                query=query,
                summary_markdown=summary,
                sources=[],
                estimated_tokens=int(len(summary) / CHAR_PER_TOKEN),
                duration_sec=dur,
                cached=False,
            )

        # 2. Scrape & Format concurrently
        blocks = [f"# Research Synthesis: {query}\n"]
        sources = []
        target_results = search_results[:max_pages]
        urls_to_scrape = [
            item.url for item in target_results if item.url and (item.url.startswith("http://") or item.url.startswith("https://"))
        ]

        scraped_content = await self.scrape_urls_batch_async(urls_to_scrape)

        for idx, item in enumerate(target_results):
            title = item.title or f"Result {idx+1}"
            url = item.url
            snippet = item.snippet
            sources.append(url)

            blocks.append(f"## {idx+1}. {title}\n**Source**: `{url}`\n**Summary**: {snippet}\n")

            page_md = scraped_content.get(url, "")
            if page_md and len(page_md) > 80 and not page_md.startswith("[Failed"):
                clean_slice = page_md[:1000].strip()
                blocks.append(f"**Key Content**:\n```markdown\n{clean_slice}\n```\n")

        dur = time.perf_counter() - start_time
        blocks.append(f"\n*(Research completed in {dur:.2f}s | Bounded to <={max_tokens} tokens)*")

        raw_md = "\n".join(blocks)
        bounded_md = bound_markdown_tokens(raw_md, max_tokens=max_tokens)
        token_count = int(len(bounded_md) / CHAR_PER_TOKEN)

        synthesis = ResearchSynthesis(
            query=query,
            summary_markdown=bounded_md,
            sources=sources,
            estimated_tokens=token_count,
            duration_sec=dur,
            cached=False,
        )

        if use_cache:
            self._cache[normalized_key] = {
                "summary_markdown": bounded_md,
                "sources": sources,
                "estimated_tokens": token_count,
            }
            self._save_cache()

        return synthesis

    def research(
        self,
        query: str,
        max_pages: int = 2,
        max_tokens: int = DEFAULT_RESEARCH_TOKEN_BUDGET,
        use_cache: bool = True,
    ) -> ResearchSynthesis:
        """
        Executes end-to-end fast web research with scraping, bounding, and caching.
        """
        return _run_async_safely(
            self.research_async,
            query,
            max_pages=max_pages,
            max_tokens=max_tokens,
            use_cache=use_cache,
        )

    def clear_cache(self):
        """Clears the search/scrape cache."""
        self._cache.clear()
        if self.cache_path and os.path.exists(self.cache_path):
            try:
                os.remove(self.cache_path)
            except Exception:
                pass


def create_fast_research_engine(cache_path: Optional[str] = "/dev/shm/hermes_research_cache.json") -> FastWebResearchEngine:
    """Factory helper creating a FastWebResearchEngine instance."""
    return FastWebResearchEngine(cache_path=cache_path)


__all__ = [
    "SearchResult",
    "ResearchSynthesis",
    "FastWebResearchEngine",
    "clean_html_to_markdown",
    "bound_markdown_tokens",
    "create_fast_research_engine",
    "CRAWL4AI_AVAILABLE",
    "TRAFILATURA_AVAILABLE",
]
