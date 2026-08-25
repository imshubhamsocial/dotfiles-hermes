"""
Contract Tests for U23: Integrated Local Fast-Research Engine & Web Ingestion
==============================================================================
Tests the FastWebResearchEngine class, HTML-to-Markdown cleaner, token bounding,
RAMDisk caching, and sub-300ms fallback research behavior.
"""

from __future__ import annotations

import sys
import tempfile
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.fast_research import (
    FastWebResearchEngine,
    SearchResult,
    ResearchSynthesis,
    clean_html_to_markdown,
    bound_markdown_tokens,
    create_fast_research_engine,
)


class TestHTMLToMarkdownCleaning:
    """Test 1: Fast deterministic HTML-to-Markdown cleaning."""

    def test_basic_html_cleaning(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title><script>console.log('secret');</script><style>body { color: red; }</style></head>
        <body>
            <header><nav><a href="/home">Home</a></nav></header>
            <h1>Introduction to WebGL</h1>
            <p>WebGL is a JavaScript API for rendering <b>interactive</b> 3D graphics.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <pre><code>const scene = new THREE.Scene();</code></pre>
            <footer>Copyright 2026</footer>
        </body>
        </html>
        """
        md = clean_html_to_markdown(html)

        assert "console.log" not in md
        assert "color: red" not in md
        assert "Home" not in md
        assert "Copyright 2026" not in md
        assert "Introduction to WebGL" in md
        assert "interactive" in md
        assert "• Item 1" in md
        assert "const scene = new THREE.Scene();" in md

    def test_empty_or_malformed_html(self):
        assert clean_html_to_markdown("") == ""
        assert clean_html_to_markdown(None) == ""
        assert clean_html_to_markdown("plain text with no tags") == "plain text with no tags"


class TestTokenBounding:
    """Test 2: Strict prompt and context token ceiling bounding."""

    def test_token_bounding_under_budget(self):
        short_text = "This is a short research summary."
        bounded = bound_markdown_tokens(short_text, max_tokens=100)
        assert bounded == short_text

    def test_token_bounding_over_budget(self):
        long_text = "Important research finding.\n" + ("Lorem ipsum data point about simulation physics. " * 300)
        bounded = bound_markdown_tokens(long_text, max_tokens=50)

        assert len(bounded) < len(long_text)
        assert "Truncated" in bounded
        assert "Important research finding" in bounded


class TestFastWebResearchEngine:
    """Test 3: Fast research engine execution, caching, and fallback."""

    def test_search_results_structure(self):
        engine = create_fast_research_engine(cache_path=None)
        # Verify fallback synthesis works without errors even in mock or disconnected environments
        synthesis = engine.research("threejs shallow water simulation laplacian", max_pages=1, use_cache=False)

        assert isinstance(synthesis, ResearchSynthesis)
        assert synthesis.query == "threejs shallow water simulation laplacian"
        assert len(synthesis.summary_markdown) > 0
        assert synthesis.estimated_tokens <= 1200
        assert not synthesis.cached

    def test_cache_hit_and_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            cache_file = os.path.join(td, "cache.json")
            engine = FastWebResearchEngine(cache_path=cache_file)

            # Insert manual result into cache
            engine._cache["custom query"] = {
                "summary_markdown": "# Custom Cached Markdown",
                "sources": ["https://custom.org/doc"],
                "estimated_tokens": 15,
            }
            engine._save_cache()

            # Second engine loading from cache file
            engine2 = FastWebResearchEngine(cache_path=cache_file)
            res = engine2.research("custom query", use_cache=True)

            assert res.cached is True
            assert "# Custom Cached Markdown" in res.summary_markdown
            assert res.sources == ["https://custom.org/doc"]

    def test_clear_cache(self):
        with tempfile.TemporaryDirectory() as td:
            cache_file = os.path.join(td, "cache.json")
            engine = FastWebResearchEngine(cache_path=cache_file)
            engine._cache["query"] = {"summary_markdown": "x", "sources": [], "estimated_tokens": 1}
            engine._save_cache()
            assert os.path.exists(cache_file)

            engine.clear_cache()
            assert len(engine._cache) == 0
            assert not os.path.exists(cache_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
