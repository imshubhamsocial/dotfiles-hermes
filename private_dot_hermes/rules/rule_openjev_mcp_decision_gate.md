# OpenJev MCP Decision Gate Invariant

## Overview
The OpenJev MCP Server utilizes a standard Stdio JSON-RPC protocol to register specialized tools (e.g., `jev_decide`) within the Hermes runtime environment. This process allows the agent to leverage local, fast, and deterministic hypothesis evaluation.

## Key Mechanisms
1.  **MCP Registration:** The server must be correctly registered in `.hermes/config.yaml` under `mcp_servers: openjev:`. The command must point to the specific execution path (`python3.13 ${userHome}/.hermes/mcp_openjev.py`).
2.  **Interface Protocol:** Communication occurs exclusively via Stdio JSON-RPC. The exposed function signature must accurately reflect the required inputs (premise, hypothesis A, hypothesis B).
3.  **Performance Gate:** The core invariant is that the hypothesis discrimination logic, which evaluates log probabilities against the local LLM (llama-server), must execute with high reliability and critically, maintain an average execution time significantly under **50ms**.

## Verification Requirements
*   **Execution:** Must pass `test_openjev_mcp.py`.
*   **Config:** Must be listed in `mcp_servers` block of `.hermes/config.yaml`.
*   **Constraint:** Must use standard MCP protocols and avoid bespoke shell wrappers.