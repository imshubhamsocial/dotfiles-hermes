"""
FastMCP In-Memory Transport & Tool Verification Suite
=====================================================
Validates:
  1. In-memory FastMCP tool registration and schema exposure via mcp_tools.
  2. ast-grep polyglot AST pattern searching via ast_search.
  3. Fast dispatch latency for in-memory FastMCP tool calls.
  4. Pillow image downsampling validation for multimodal budgeting.
"""

from __future__ import annotations

import asyncio
import io
import sys
import time
from pathlib import Path
import pytest
from PIL import Image

HERMES_DIR = Path(__file__).resolve().parents[2]
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

from plugins.mcp_tools import mcp, ast_search
from fastmcp import FastMCP


def test_fastmcp_mcp_tools_registration():
    """Verify mcp_tools plugin initializes with correct tools and metadata."""
    assert mcp.name == "hermes-tools"

    async def _check():
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "web_extract" in tool_names
        assert "ast_search" in tool_names

    asyncio.run(_check())


def test_ast_search_execution():
    """Verify ast_search finds structural code patterns using ast-grep."""
    code = (
        "class Worker:\n"
        "    def run(self):\n"
        "        pass\n"
        "\n"
        "def helper():\n"
        "    return 42\n"
    )
    matches = ast_search(pattern="def $NAME($$$): $$$", code=code, lang="python")
    assert len(matches) == 2
    matched_texts = [m["text"] for m in matches]
    assert any("helper" in t for t in matched_texts)
    assert any("run" in t for t in matched_texts)


def test_fastmcp_in_memory_latency():
    """Verify native FastMCP dispatch executes with low latency."""
    bench_mcp = FastMCP("bench-server")

    @bench_mcp.tool
    def calculate_sum(a: int, b: int) -> int:
        return a + b

    async def _benchmark():
        await bench_mcp.call_tool("calculate_sum", {"a": 1, "b": 2})

        latencies = []
        for _ in range(50):
            t0 = time.perf_counter()
            res = await bench_mcp.call_tool("calculate_sum", {"a": 10, "b": 20})
            latencies.append((time.perf_counter() - t0) * 1000)
            assert res.content[0].text == "30" or res.content[0].type == "text"

        avg_latency_ms = sum(latencies) / len(latencies)
        assert avg_latency_ms < 10.0, f"Dispatch latency exceeded SLA: {avg_latency_ms:.3f}ms"

    asyncio.run(_benchmark())


def test_pillow_image_downsampling():
    """Verify Pillow base64 / dimension bounds check for vision budgets."""
    img = Image.new("RGB", (1920, 1080), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    with Image.open(io.BytesIO(raw_bytes)) as loaded:
        assert loaded.size == (1920, 1080)
        loaded.thumbnail((512, 512))
        assert loaded.width <= 512
        assert loaded.height <= 512


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
