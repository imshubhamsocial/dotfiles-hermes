# Phase 48 Specification: AST Canonizer v3 & 768-Token Ephemeral Tool Budget

* **ICM Layer**: Infrastructure (60% Allocation Tier)
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)
* **Input State**: 
  - Forensic audit of GDR26 identified 6 edge-case syntax traps in 4B SLM code synthesis within `AST Canonizer v2` (unclosed `<deliberation>` tags, multi-fence prefix collisions, stripped typing preamble imports, helper-only function hijacks, asymmetrical first-line body indentation, unrecovered tail-line truncations).
  - FastMCP Ephemeral Dynamic Tool Bridge on Port 1934 caps tool dialogue at 512 tokens, risking mid-JSON truncations during parallel tool calls and multi-argument database mutations.
* **Process**:
  1. Upgrade `scripts/hermes_ast_canonizer.py` to **AST Canonizer v3**:
     - Handle closed and unclosed `<deliberation>` / `<thought>` traces.
     - Extract markdown fences preferring the block defining the target entry point.
     - Merge preamble imports (`from typing import ...`) and upstream helpers from `prompt_stub`.
     - Verify target signature against helper-only `FunctionDef` hijacks while applying `CanonicalSignatureTransformer`.
     - Normalize asymmetrical first-line indentation in body completions.
     - Implement iterative tail-line truncation recovery on `SyntaxError`.
  2. Upgrade `private_dot_hermes/executable_mcp_ephemeral_bridge.py` and `.hermes/mcp_ephemeral_bridge.py`:
     - Raise tool-turn token budget from 512 to **768 tokens** with `req_timeout = 60.0s`.
     - Enforce `ROLE_CONDITIONING_DIRECTIVE` prompting deliberation strictly under 150 tokens.
     - Explicitly pass `inject_persona=bool(tools)` in `handle_chat_completions`.
  3. Deploy updated bridge to `~/.hermes/mcp_ephemeral_bridge.py` and restart `hermes-ephemeral-bridge.service`.
* **Output Artifacts**:
  - `scripts/hermes_ast_canonizer.py`
  - `.hermes/mcp_ephemeral_bridge.py`
  - `~/.hermes/mcp_ephemeral_bridge.py`
