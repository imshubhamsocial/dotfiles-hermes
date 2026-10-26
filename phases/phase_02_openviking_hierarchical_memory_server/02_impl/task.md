# Phase 02: OpenViking Hierarchical Memory Server — Implementation Checklist

> **Phase Directory**: `phase_02_openviking_hierarchical_memory_server`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `~/.config/systemd/user/hermes-openviking.service`: persistent daemon unit definition
  - `~/.openviking/ov.conf`: server and dense embedding configuration
  - `mcp.server.fastmcp` / `fastmcp`: package alignment in `.local/lib/python3.13/site-packages`
- Module Stems:
  - `openviking-server` (Port 1933)
  - `openviking.server.app.create_app`
- Required Skills:
  - `viking-retrieval`

---

## 2. Causal Hypotheses
1. `openviking-server` was failing on import because `mcp 2.x` deprecated `mcp.server.fastmcp` and altered constructor arguments for `MCPServer`. Realigning user environment to `fastmcp==3.4.7` and `mcp==1.30.0` satisfies `openviking`'s FastMCP endpoint imports while retaining 100% compatibility with `mcp_openjev.py`.
2. Provisioning `hermes-openviking.service` with `CUDA_VISIBLE_DEVICES=""` ensures 0.0 MiB GPU VRAM consumption while running `openviking-server` bound to `127.0.0.1:1933`.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Realign MCP package dependencies to `fastmcp==3.4.7` and `mcp==1.30.0`.
- [x] Step 4: Verify `openviking-server` starts and answers `GET /health` with `{"status":"ok","healthy":true}`.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
