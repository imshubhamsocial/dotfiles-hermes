# Implementation Task Checklist: Phase 48

## 1. Concrete Symbol Targets
- `sanitize_and_canonize_edit_surface` in `scripts/hermes_ast_canonizer.py` (AST Canonizer v3)
- `compact_messages` and `handle_chat_completions` in `.hermes/mcp_ephemeral_bridge.py`
- `ROLE_CONDITIONING_DIRECTIVE` in `.hermes/mcp_ephemeral_bridge.py`
- `03_verify/contract.sh` in `phases/phase_48_ast_canonizer_v3_and_768_token_tool_budget/03_verify/contract.sh`

## 2. Causal Hypotheses
- **H1 (AST Canonizer v3 Resilience)**: Resolving the six Small-Language-Model syntax traps (unclosed deliberation tags, multi-fence prefix collisions, stripped typing preamble imports, helper-only function hijacks, asymmetrical first-line body indentation, unrecovered tail-line truncations) eliminates 100% of non-algorithmic HumanEval failure modes.
- **H2 (768-Token Tool Headroom)**: Raising the tool dialogue ceiling from 512 to 768 tokens prevents mid-JSON truncation during parallel tool calls and multi-argument database mutations while bounding per-turn latency under 10 seconds.
- **H3 (Directive Calibrations)**: Constraining tool-turn deliberation under 150 tokens preserves token headroom for valid JSON schema emission.

## 3. Implementation Steps
- [x] Implement AST Canonizer v3 in `scripts/hermes_ast_canonizer.py`.
- [x] Update dynamic token budget (768 tokens, 60s timeout) and directive in `.hermes/mcp_ephemeral_bridge.py` and deploy to `~/.hermes/mcp_ephemeral_bridge.py`.
- [x] Restart `hermes-ephemeral-bridge.service`.
- [x] Lint modified files using `ruff` (zero errors).
- [ ] Create and execute `03_verify/contract.sh` testing all 6 edge-case traps and bridge parameters.
