"""compound_tools.py — CP-6 fold-in: E3 compressed toolkit + E4 cluster plan (Hermes middleware).

Canonical repo source. Installed (synced) into the lever profiles' plugins
dirs by bin/sync_lever_plugins.sh — live copies at
~/.hermes/profiles/{lever-thinking,frontier-stack}/plugins/compound_tools.py.

Wires the Batch-E / RESEARCH_PLAN E3+E4 prototypes (toolkit_compressor.py +
toolkit_clusterer.py) into the live request path as the "compound macro-tools"
lever (FRONTIER_COVERAGE_MATRIX F10 / HARNESS_SCALING_TO_FRONTIER §2 row 1):

- E3 (EASYTOOL): pre-compress every tool schema OFFLINE into a concise unified
  instruction (signature + distilled desc + use-for + avoid). The 4B model
  mis-parses verbose JSON-schema tool definitions (type/required drift,
  hallucinated arg keys) — the compressed block is what the model actually
  reads, with every REQUIRED arg + type preserved (info_preserved contract).
- E4 (Tool-Planner): cluster the toolkit, and tell the model to plan at the
  CLUSTER level first (announce INTENT:<cluster> before the first tool frame
  of that cluster) instead of picking from raw tools — the "toolkit first"
  pattern, adapted to 4B (deterministic rules, no LLM in the loop).

This is a llm_request middleware, fail-open, deterministic, and CACHE-SAFE:
it only APPENDS to the FIRST-request system message (part of the cached
prefix) and NEVER mutates historical turns (the exact-byte llama.cpp prefix
cache must survive). No LLM calls, no network, no tool execution — the
compressed registry is built lazily once per process from the canonical arena
tool bundle.

Env knobs (all default ON; off = fail-open no-op):
HILO_COMPOUND_TOOLS_ENABLED (default 1) · HILO_COMPOUND_TOOLS_SRC (default:
the harness arena bundle at fastmcp_tool_server.ARENA_TOOLS; a JSON path is
also accepted for custom bundles).
"""

import json
import os
import sys
from pathlib import Path

_INJECTED = False
_REGISTRY_CACHE = None  # (guide_block, cluster_header) computed once per process


def _env_flag(name, default=True):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


def _load_arena_tools():
    """Lift the harness's canonical arena tool bundle as compressor input."""
    src = os.environ.get("HILO_COMPOUND_TOOLS_SRC")
    if src and Path(src).exists():
        raw = json.load(open(src, encoding="utf-8"))
        tools = raw if isinstance(raw, list) else raw.get("tools", raw)
        # normalize {"name","description","params"} → compressor inputSchema shape
        from toolkit_compressor import tool_schemas_from_fastmcp  # noqa: E402
        funcs = {}
        for t in tools:
            params = t.get("params") or {}
            funcs[t["name"]] = {"description": t.get("description", t.get("desc", "")),
                                "params": params}
        return tool_schemas_from_fastmcp(funcs)
    # canonical: the arena bundle (same source fastmcp_tool_server serves)
    try:
        from fastmcp_tool_server import ARENA_TOOLS  # noqa: E402
    except Exception:
        return None
    return [
        {"name": t["name"], "description": t.get("desc", ""),
         "inputSchema": {"type": "object",
                         "properties": {a: {"type": p.get("type", "string"),
                                            **( {"default": p["default"]}
                                                if "default" in p else {})}
                                        for a, p in t.get("params", {}).items()},
                         "required": [a for a, p in t.get("params", {}).items()
                                      if p.get("required", True)]}}
        for t in ARENA_TOOLS
    ]


def _build_registry():
    """(guide_block, cluster_header) — E3-compressed + E4-clustered, once."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    # sibling modules: the canonical sources live next to this plugin in the
    # repo; the installed copy lives under <profile>/plugins/<name>/ — walk up
    # to the prototypes dir for the siblings, mirroring amd_memory's core
    # resolution (Entry 70 lesson: the installed copy must resolve its deps).
    here = Path(__file__).resolve().parent
    for cand in (here, here.parent, here.parent.parent):
        if (cand / "toolkit_compressor.py").exists():
            sys.path.insert(0, str(cand))
            break
    try:
        from toolkit_compressor import compress_bundle, render_unified  # noqa: E402
        from toolkit_clusterer import cluster_tools, render_plan_header  # noqa: E402
        tools = _load_arena_tools()
        if not tools:
            return None
        res = compress_bundle(tools)
        # E4 operates on the compressed shape (name + desc)
        cluster_input = [{"name": c["name"], "desc": c["desc"]}
                         for c in res["tools"]]
        clusters = cluster_tools(cluster_input)
        guide = res["block"]
        header = render_plan_header(clusters)
        _REGISTRY_CACHE = (guide, header)
        return _REGISTRY_CACHE
    except Exception:
        return None


def _append_text(content, suffix):
    """Append a text suffix to message content (str or parts-list), cache-safe."""
    if content is None:
        return suffix
    if isinstance(content, str):
        return content + suffix
    if isinstance(content, list):
        try:
            return list(content) + [{"type": "text", "text": suffix.lstrip("\n")}]
        except Exception:
            return content
    return content  # fail-open


def _on_request(request):
    global _INJECTED
    if _INJECTED:
        return None
    if not _env_flag("HILO_COMPOUND_TOOLS_ENABLED"):
        return None
    reg = _build_registry()
    if reg is None:
        return None  # fail-open: no registry → no injection
    guide, header = reg
    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    first = messages[0]
    if not isinstance(first, dict) or first.get("role") not in ("system", "developer"):
        return None
    block = (
        "\n\n[Toolkit guide — compressed tool instructions. Every required "
        "argument and its type is preserved; prose was distilled. Read the "
        "signatures, do NOT invent argument keys not listed.]\n"
        + header + "\n\n" + guide
    )
    first["content"] = _append_text(first.get("content"), block)
    _INJECTED = True
    return request


def register(ctx):
    """Register the llm_request middleware under the hermes.v1 contract.

    Return shape follows frontier_levers/adaptive_thinking: the middleware
    returns {"request", "source", "reason"} when it changed the request, or
    None when untouched (fail-open) — the wrapper below maps our internal
    _on_request (which returns the mutated request dict) onto that contract.
    """
    def _middleware(**kwargs):
        try:
            req = kwargs.get("request")
            if not isinstance(req, dict):
                return None
            request = dict(req)
            changed = _on_request(request)
            if changed is None:
                return None
            return {
                "request": changed,
                "source": "compound-tools",
                "reason": "E3 compressed toolkit + E4 cluster plan (request #1)",
            }
        except Exception:
            return None  # absolute fail-open: never break the request path

    ctx.register_middleware("llm_request", _middleware)
