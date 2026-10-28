# Phase 40 Specification: Ephemeral FastMCP Dynamic Tool Bridge (Port 1934)

* **ICM Layer**: Infrastructure (60% Allocation Tier)  
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)  
* **Input State**: Inspect AI `POST /v1/chat/completions` payloads containing caller tools arrays dropped by `gateway/platforms/api_server_openai_routes.py`.  
* **Process**:  
  1. Deploy `~/.hermes/mcp_ephemeral_bridge.py` on Port 1934 exposing `/mcp` (FastMCP JSON-RPC 2.0) and `/v1/chat/completions` (OpenAI tool-bridging ingress).  
  2. Configure `~/.hermes/profiles/eval_retail_config_overlay.yaml` mounting `ephemeral_eval_bridge` in `platform_toolsets.api_server` and removing `web_search` from closed-world evaluation toolsets.  
* **Output Artifact**: Live daemon on `http://127.0.0.1:1934/health` and `/mcp` with 0.0 MiB GPU VRAM footprint.
