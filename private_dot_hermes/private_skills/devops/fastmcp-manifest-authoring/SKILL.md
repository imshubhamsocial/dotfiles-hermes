---
name: fastmcp-manifest-authoring
description: Use when authoring FastMCP tool servers and manifests.
version: 0.2.0
author: Hermes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [FastMCP, MCP, Tools, Manifest, Python]
    category: devops
---

# FastMCP Tool Server & Manifest Authoring Guide

This guide establishes the standard procedure for structuring, defining, and serving custom tools via the FastMCP framework for Hermes Agent OS.

## When to Use

- Exposing custom python scripts or libraries as Model Context Protocol (MCP) servers.
- Authoring tools with structured type validation via `@mcp.tool()`.
- Integrating local MCP tool endpoints into `~/.hermes/config.yaml`.

## Prerequisites

- Python virtual environment with `fastmcp>=4.0.0` installed.
- Hermes agent environment inside Distrobox container `ws-hermes`.

## How to Run

Test and run the FastMCP server via standard stdio transport:

```bash
# Direct stdio test run
python3 server.py

# Or via FastMCP CLI inspect
fastmcp inspect server.py
```

## Quick Reference

| Action | Canonical Invocation / Code |
|:---|:---|
| Import | `from fastmcp import FastMCP` |
| Instantiate | `mcp = FastMCP("service-name", instructions="...")` |
| Tool Decorator | `@mcp.tool()` on typed function with docstring |
| Resource Decorator | `@mcp.resource("uri://path")` |
| Serve (stdio) | `if __name__ == "__main__": mcp.run()` |
| Config Entry | Add under `mcp_servers:` in `~/.hermes/config.yaml` |

## Procedure

### 1. Author the Server (`server.py`)

Always use standard Python type annotations and docstrings. FastMCP automatically derives JSON Schema parameter specs from function signatures and docstrings.

```python
"""FastMCP Tool Server Implementation."""

from typing import Any, Dict
from fastmcp import FastMCP

# Initialize FastMCP application
mcp = FastMCP(
    "system-tools",
    instructions="Provides local diagnostic and inspection tools.",
)


@mcp.tool()
def search_vault(query: str, top_k: int = 3) -> Dict[str, Any]:
  """Performs a semantic search against the local knowledge vault.

  Args:
      query: The semantic search query string.
      top_k: Number of top matches to retrieve (default: 3).

  Returns:
      A dictionary containing retrieved items and status metadata.
  """
  if not query.strip():
    return {"success": False, "error": "Query string cannot be empty."}

  # Implementation logic here
  return {
      "success": True,
      "query": query,
      "results": [{"id": "doc_1", "score": 0.89}],
  }


if __name__ == "__main__":
  mcp.run(transport="stdio")
```

### 2. Contract Testing (`test_server.py`)

Verify tool registration and execution using pytest and FastMCP's built-in call handler:

```python
import pytest
from server import mcp


def test_tool_registration():
  tools = mcp.list_tools()
  tool_names = [t.name for t in tools]
  assert "search_vault" in tool_names


@pytest.mark.asyncio
async def test_search_vault_invocation():
  result = await mcp.call_tool("search_vault", {"query": "architecture"})
  assert result is not None
```

### 3. Registering with Hermes Agent

Register the MCP server in `~/.hermes/config.yaml` so the agent can discover and invoke the tools:

```yaml
mcp_servers:
  system-tools:
    command: "python3"
    args: ["/path/to/server.py"]
    env: {}
```

## Pitfalls

- **Avoid Hallucinated Wrapper Imports**: Never import non-existent modules such as `hermes_tools`. Use Python standard library (`subprocess`, `json`, `sys`) and official `fastmcp`.
- **Docstrings are Schemas**: FastMCP generates descriptions directly from Python docstrings. Missing docstrings result in empty tool descriptions in the LLM tool context.
- **Type Annotations Mandatory**: Every parameter must have an explicit Python type hint (`str`, `int`, `float`, `bool`, `List[str]`, `Dict[str, Any]`). Untyped parameters fall back to generic string representations.

## Verification

Validate tool discovery and execution:

```bash
python3 -m pytest test_server.py -q
```
All contract tests must pass with 0 errors.