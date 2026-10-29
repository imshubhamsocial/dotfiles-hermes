#!/usr/bin/env python3
"""
GDR24 Phase 40: Upstream-Pure Ephemeral FastMCP Dynamic Tool Bridge (Port 1934)
Bridges Inspect AI request-level `tools` into Hermes Gateway (Port 8642) via MCP
and yields tool_calls back to Inspect AI's stateful evaluation loop.
Zero modifications to upstream .hermes/hermes-agent. 0.0 MiB GPU VRAM.
"""
import asyncio
import hashlib
import json
import os
import re
import sys
import time
import uuid

WORKSPACE_DIR = os.environ.get("WORKSPACE", "/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes")
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from aiohttp import ClientSession, ClientTimeout, web

from scripts.hermes_abductive_fastmcp import (
    decompose_and_sequentialize_tools,
    intercept_and_enforce_epistemic_gates,
    translate_tool_error_for_4b_cognition,
)
from scripts.hermes_ast_canonizer import sanitize_and_canonize_edit_surface

BRIDGE_HOST = os.environ.get("HERMES_BRIDGE_HOST", "127.0.0.1")
BRIDGE_PORT = int(os.environ.get("HERMES_BRIDGE_PORT", "1934"))
GATEWAY_URL = os.environ.get("HERMES_GATEWAY_URL", "http://127.0.0.1:8642/v1")
LLAMA_DIRECT_URL = os.environ.get("HERMES_LLAMA_URL", "http://127.0.0.1:8138/v1")
OPENVIKING_URL = os.environ.get("OPENVIKING_URL", "http://127.0.0.1:1933")

ROLE_CONDITIONING_DIRECTIVE = (
    "CRITICAL OPERATIONAL IDENTITY & EPISTEMIC PRECEDENCE CONTRACT:\n"
    "1. ROLE BINDING: You are the official, internal Customer Support Agent for this retail store. "
    "You have direct, authenticated read/write access to the store's customer, order, and product databases "
    "via the provided function tools.\n"
    "2. FORBIDDEN DISCLAIMERS: NEVER state 'As an AI assistant', 'I do not operate a physical online store', "
    "or 'I do not have access to private customer databases'. NEVER ask the customer which retailer, store, "
    "or website URL they purchased from (e.g., never mention Amazon, Target, Walmart, Zappos, or Home Depot).\n"
    "3. DOMAIN DB TOOL PRECEDENCE (OpenViking L1 Invariant): Before refusing any request or invoking "
    "transfer_to_human_agents, you MUST first execute read/lookup tools. If the customer does not remember "
    "their email address, immediately invoke find_user_id_by_name_zip(first_name, last_name, zip) and/or "
    "get_order_details(order_id) to inspect the actual database record and verify policy constraints.\n"
    "4. COMPACT DELIBERATION: Limit internal <deliberation> to at most 4 concise bullet points (< 120 tokens) "
    "mapping known attributes to tool signatures, then immediately emit the required tool call."
)

CODE_SYNTHESIS_DIRECTIVE = (
    "You are an expert Python software engineer. Implement the requested function directly, "
    "correctly, and efficiently according to its docstring and specifications. "
    "Keep deliberation concise, focused, and purposeful, then output the complete Python implementation inside a ```python ``` markdown block."
)

DELIB_REGEX = re.compile(r"<deliberation>.*?</deliberation>", re.DOTALL)

class EphemeralToolState:
    def __init__(self) -> None:
        self.active_tools: dict[str, dict] = {}
        self.tool_results_cache: dict[str, str] = {}
        self.intercepted_calls: list[dict] = []
        self.call_event: asyncio.Event = asyncio.Event()
        self.requests_bridged: int = 0
        self.tool_calls_yielded: int = 0
        self.session_state: dict = {"read_tools_called": []}

    def update_schemas(self, tools_list: list[dict]) -> None:
        for t in tools_list:
            fn = t.get("function", t)
            name = fn.get("name")
            if name:
                self.active_tools[name] = {
                    "name": name,
                    "description": fn.get("description", f"Domain tool {name}"),
                    "inputSchema": fn.get(
                        "parameters",
                        {"type": "object", "properties": {}},
                    ),
                }

    def harvest_tool_outputs(self, messages: list[dict]) -> None:
        """Index tool outputs sent by Inspect AI in role='tool' messages."""
        tc_id_to_sig: dict[str, str] = {}
        for m in messages:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    fn = tc.get("function", {})
                    sig = f"{fn.get('name')}:{fn.get('arguments', '{}')}"
                    tc_id_to_sig[tc.get("id", "")] = sig
            elif m.get("role") == "tool":
                tc_id = m.get("tool_call_id", "")
                content = m.get("content", "")
                if isinstance(content, list):
                    content = json.dumps(content)
                if tc_id in tc_id_to_sig:
                    sig = tc_id_to_sig[tc_id]
                    tool_name = sig.split(":", 1)[0]
                    try:
                        args = json.loads(sig.split(":", 1)[1])
                    except (json.JSONDecodeError, IndexError, ValueError):
                        args = {}
                    translated = translate_tool_error_for_4b_cognition(tool_name, args, str(content))
                    self.tool_results_cache[sig] = translated

STATE = EphemeralToolState()

def compact_messages(messages: list[dict], inject_persona: bool = True) -> list[dict]:
    """Enforce Sub-8K ICM Context Discipline and inject Role Binding Directive."""
    compacted: list[dict] = []
    has_system = False
    n_msgs = len(messages)

    for idx, msg in enumerate(messages):
        m = dict(msg)
        role = m.get("role", "user")
        content = m.get("content") or ""

        if role == "system":
            has_system = True
            if inject_persona and "CRITICAL OPERATIONAL IDENTITY" not in str(content):
                m["content"] = f"{ROLE_CONDITIONING_DIRECTIVE}\n\n{content}"
        elif role == "assistant" and isinstance(content, str):
            # Strip verbose <deliberation> from historical turns to prevent 200K token bloat
            if idx < n_msgs - 2:
                m["content"] = DELIB_REGEX.sub("", content).strip()
        elif role == "tool" and isinstance(content, str) and len(content) > 2048:
            # Cap single tool payload size while preserving JSON structure summary
            m["content"] = content[:2048] + "\n...[TRUNCATED_FOR_SUB_8K_DISCIPLINE]"

        compacted.append(m)

    if not has_system:
        directive = ROLE_CONDITIONING_DIRECTIVE if inject_persona else CODE_SYNTHESIS_DIRECTIVE
        compacted.insert(0, {"role": "system", "content": directive})

    return compacted

async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "service": "hermes-ephemeral-fastmcp-bridge",
        "port": BRIDGE_PORT,
        "registered_tools_count": len(STATE.active_tools),
        "registered_tools": list(STATE.active_tools.keys()),
        "requests_bridged": STATE.requests_bridged,
        "tool_calls_yielded": STATE.tool_calls_yielded,
        "cuda_vram_mib": 0.0,
    })

async def handle_mcp_jsonrpc(request: web.Request) -> web.Response:
    """
    FastMCP / Model Context Protocol Streamable HTTP JSON-RPC 2.0 Endpoint (/mcp).
    Mounted by Hermes Gateway (Port 8642) via ~/.hermes/config.yaml.
    """
    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError):
        return web.json_response({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status=400)

    method = body.get("method", "")
    req_id = body.get("id", 1)
    params = body.get("params", {})

    if method == "initialize":
        return web.json_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "ephemeral_eval_bridge", "version": "1.0.0"},
            },
        })

    if method == "notifications/initialized":
        return web.json_response({"jsonrpc": "2.0", "result": {}})

    if method == "tools/list":
        return web.json_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": list(STATE.active_tools.values())},
        })

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        args_json = json.dumps(tool_args, sort_keys=True)
        sig = f"{tool_name}:{args_json}"

        if sig in STATE.tool_results_cache:
            cached_out = STATE.tool_results_cache[sig]
            return web.json_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": cached_out}],
                    "isError": False,
                },
            })

        # Record tool call to yield back to Inspect AI's stateful RetailDB runner
        call_id = f"call_{hashlib.sha256(f'{sig}:{time.time()}'.encode()).hexdigest()[:16]}"
        STATE.intercepted_calls.append({
            "id": call_id,
            "type": "function",
            "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
        })
        STATE.tool_calls_yielded += 1
        STATE.call_event.set()

        return web.json_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{
                    "type": "text",
                    "text": f"[YIELD_TO_HARNESS:{call_id}] Tool {tool_name} queued for immediate execution.",
                }],
                "isError": False,
            },
        })

    return web.json_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {},
    })

async def handle_models(request: web.Request) -> web.Response:
    return web.json_response({
        "object": "list",
        "data": [
            {"id": "hermes-agent-bridged", "object": "model", "owned_by": "hermes"},
            {"id": "hermes-agent", "object": "model", "owned_by": "hermes"},
            {"id": "gemma-4-E4B-it-qat-q4_0", "object": "model", "owned_by": "local"},
        ],
    })

async def handle_chat_completions(request: web.Request) -> web.Response:
    """
    OpenAI-compatible /v1/chat/completions Ingress Endpoint on Port 1934.
    1. Registers caller `tools` into the FastMCP registry (/mcp).
    2. Compacts conversation context & injects Retail Role Conditioning.
    3. Coordinates execution with Port 8138 / Port 8642 and returns OpenAI tool_calls to Inspect AI.
    """
    payload = await request.json()
    STATE.requests_bridged += 1
    STATE.intercepted_calls.clear()
    STATE.call_event.clear()

    tools = payload.get("tools", [])
    if tools:
        STATE.update_schemas(tools)

    messages = payload.get("messages", [])
    STATE.harvest_tool_outputs(messages)
    compacted_msgs = compact_messages(messages, inject_persona=bool(tools))

    # Token budget & timeout policy:
    # 1. Multi-turn dialogue with tools (Tau-bench / BFCL): Enforce fast System-2 deliberation cap (512 tokens, < 10s per turn)
    # 2. Open-ended code synthesis / tasks without tools (HumanEval): Allow caller's requested budget (up to 3072 tokens)
    #    so Gemma-4's reasoning_content has plenty of headroom before emitting code.
    forward_payload = dict(payload)
    forward_payload["messages"] = compacted_msgs
    requested_max = int(payload.get("max_tokens") or 3072)
    if tools:
        forward_payload["max_tokens"] = min(requested_max, 512)
        req_timeout = 45.0
    else:
        forward_payload["max_tokens"] = min(max(requested_max, 2048), 3072)
        req_timeout = 180.0

    forward_payload["temperature"] = float(payload.get("temperature", 0.0))
    forward_payload["cache_prompt"] = True

    timeout = ClientTimeout(total=req_timeout)
    async with (
        ClientSession(timeout=timeout) as session,
        session.post(f"{LLAMA_DIRECT_URL}/chat/completions", json=forward_payload) as resp
    ):
        result = await resp.json()

    # If MCP calls were intercepted during bridged agent execution, synthesize standard tool_calls response
    if STATE.intercepted_calls:
        return web.json_response({
            "id": f"chatcmpl-bridge-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": payload.get("model", "hermes-agent-bridged"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": list(STATE.intercepted_calls),
                },
                "finish_reason": "tool_calls",
            }],
            "usage": result.get("usage", {"prompt_tokens": 512, "completion_tokens": 64, "total_tokens": 576}),
        })

    # Verify tool_calls formatting compliance for Inspect AI (-M responses_api=false)
    choices = result.get("choices", [])
    if choices and choices[0].get("message", {}).get("tool_calls"):
        raw_tcs = choices[0]["message"]["tool_calls"]
        # 1. Sequentialize and deduplicate parallel tool calls (Fixes BFCL parallel drop)
        ordered_tcs = decompose_and_sequentialize_tools(raw_tcs)

        # 2. In-flight Gate 2 check (Blocks premature transfer_to_human_agents)
        allowed_tcs = []
        gate2_blocked_msg = None
        for tc in ordered_tcs:
            fn = tc.get("function", {})
            gate_res = intercept_and_enforce_epistemic_gates(
                STATE.session_state,
                {"name": fn.get("name", ""), "arguments": fn.get("arguments", "{}")},
            )
            if gate_res["status"] == "BLOCKED_BY_EPISTEMIC_GATE_2":
                gate2_blocked_msg = gate_res["synthetic_observation"]
                break
            allowed_tcs.append(tc)

        if gate2_blocked_msg:
            choices[0]["message"]["tool_calls"] = None
            choices[0]["message"]["content"] = gate2_blocked_msg
            choices[0]["finish_reason"] = "stop"
        else:
            choices[0]["message"]["tool_calls"] = allowed_tcs
            STATE.tool_calls_yielded += len(allowed_tcs)

    # 3. Apply Phase 44 AST Canonizer to code synthesis completions
    elif choices:
        raw_text = choices[0].get("message", {}).get("content") or ""
        # If content is empty (e.g. reasoning block boundary), check reasoning_content fallback
        if not raw_text.strip() and choices[0].get("message", {}).get("reasoning_content"):
            r_text = choices[0]["message"]["reasoning_content"]
            if "```python" in r_text or "def " in r_text:
                raw_text = r_text

        if "def " in raw_text or "```" in raw_text:
            prompt_stub = ""
            for m in reversed(messages):
                if m.get("role") == "user" and m.get("content"):
                    prompt_stub = m.get("content")
                    break
            if "def " in prompt_stub:
                try:
                    canonized = sanitize_and_canonize_edit_surface(raw_text, prompt_stub)
                    choices[0]["message"]["content"] = canonized
                except Exception:
                    pass

    return web.json_response(result)

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_post("/mcp", handle_mcp_jsonrpc)
    app.router.add_get("/v1/models", handle_models)
    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host=BRIDGE_HOST, port=BRIDGE_PORT, print=None)
