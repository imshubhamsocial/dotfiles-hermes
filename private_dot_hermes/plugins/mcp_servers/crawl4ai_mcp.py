from fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler

mcp = FastMCP("web_extract_local")


@mcp.tool()
async def web_extract(url: str) -> str:
    """Extract clean markdown from a URL locally using crawl4ai with zero API keys."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown or ""


if __name__ == "__main__":
    mcp.run()
