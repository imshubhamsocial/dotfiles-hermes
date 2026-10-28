# Phase 37 Specification: Port 8642 Gateway Dynamic Tool Passthrough & FastMCP Bridging

## 1. Objective
Resolve the control-loop collision by configuring the Hermes Gateway on Port 8642 with Passthrough-First Routing: when caller tools are supplied, forward the exact tool schema to `llama-server` on Port 8138 while injecting retrieved procedural skills into context. In bridged mode, expose environment tools via FastMCP on Port 1934.

## 2. Invariants
- `POST http://127.0.0.1:8642/v1/chat/completions` with a `tools` payload must return structured `tool_calls` in `choices[0].message`.
- Gateway must not strip tool calls or serialize content-only responses when tools are declared.
- Port 1934 FastMCP bridge must respond to MCP JSON-RPC protocol requests.
- Single-slot concurrency lock on Slot 0 (`/tmp/jev_harness2_slot0.lock`) must be enforced.
