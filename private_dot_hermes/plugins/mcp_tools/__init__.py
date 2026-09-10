"""
Unified FastMCP Tool Server (Phase 1 Substrate)
==============================================
Exposes high-performance Crawl4AI web extraction and ast-grep polyglot AST search
directly to Hermes through FastMCP without custom wrappers.
"""

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

try:
    from ast_grep_py import SgRoot
except ImportError:
    SgRoot = None

if FastMCP is not None:
    mcp = FastMCP("hermes-tools")

    @mcp.tool
    async def web_extract(url: str, word_limit: int = 500) -> str:
        """Extract clean, LLM-ready markdown from any URL via Crawl4AI."""
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, word_count_threshold=word_limit)
                return result.markdown or ""
        except ImportError:
            return "Error: crawl4ai is not installed in the active environment."

    @mcp.tool
    def ast_search(pattern: str, code: str, lang: str = "python") -> list[dict]:
        """Search structural code patterns across code using ast-grep Tree-sitter."""
        if SgRoot is None:
            return [{"error": "ast-grep-py is not installed"}]
        root = SgRoot(code, lang)
        matches = root.root().find_all(pattern=pattern)
        return [
            {
                "text": node.text(),
                "range": str(node.range()),
            }
            for node in matches
        ]
else:
    mcp = None


def register(ctx=None):
    """Registers plugin mcp_tools into Hermes runtime."""
    pass

