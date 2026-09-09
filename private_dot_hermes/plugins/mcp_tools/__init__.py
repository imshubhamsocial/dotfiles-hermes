"""
Unified FastMCP Tool Server (Phase 1 Substrate)
==============================================
Exposes high-performance Crawl4AI web extraction and ast-grep polyglot AST search
directly to Hermes through FastMCP without custom wrappers.
"""

from fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler
from ast_grep_py import SgRoot

mcp = FastMCP("hermes-tools")


@mcp.tool
async def web_extract(url: str, word_limit: int = 500) -> str:
    """Extract clean, LLM-ready markdown from any URL via Crawl4AI."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, word_count_threshold=word_limit)
        return result.markdown or ""


@mcp.tool
def ast_search(pattern: str, code: str, lang: str = "python") -> list[dict]:
    """Search structural code patterns across code using ast-grep Tree-sitter."""
    root = SgRoot(code, lang)
    matches = root.root().find_all(pattern=pattern)
    return [
        {
            "text": node.text(),
            "range": str(node.range()),
        }
        for node in matches
    ]


def register(ctx=None):
    """Registers plugin mcp_tools into Hermes runtime."""
    pass
