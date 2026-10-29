# Implementation Task Checklist: Phase 45

## 1. Concrete Symbol Targets
- `intercept_and_enforce_epistemic_gates` in `scripts/hermes_abductive_fastmcp.py`
- `translate_tool_error_for_4b_cognition` in `scripts/hermes_abductive_fastmcp.py`
- `decompose_and_sequentialize_tools` in `scripts/hermes_abductive_fastmcp.py`
- In-flight hook integration in `.hermes/mcp_ephemeral_bridge.py`
- Verification contract in `phases/phase_45_fastmcp_gate2_abductive_error_sequential_dispatch/03_verify/contract.sh`

## 2. Causal Hypotheses
- **H1 (In-Flight Gate 2 Interception)**: Intercepting `transfer_to_human_agents` when `read_tools_called` is empty prevents premature surrender and directs the agent to query the customer database first.
- **H2 (Abductive Error Translation)**: Clarifying that a database miss (e.g., "Order not found") is a data-layer issue ($H_{\text{data}}$) rather than a syntax rejection ($H_{\text{schema}}$) prevents parameter renaming cascades and provides clear recovery paths.
- **H3 (Sequential Tool Decomposition)**: Splitting parallel multi-tool dispatches into sequential single-tool executions bypasses 4B attention cross-talk and aligns parallel accuracy with the 64.0% single-tool baseline.

## 3. Implementation Steps
- [x] Implement `scripts/hermes_abductive_fastmcp.py`.
- [x] Integrate epistemic interceptor and abductive translator into `.hermes/mcp_ephemeral_bridge.py`.
- [ ] Implement and execute `phases/phase_45_fastmcp_gate2_abductive_error_sequential_dispatch/03_verify/contract.sh`.
