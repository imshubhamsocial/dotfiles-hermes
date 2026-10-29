# Phase 52 Implementation Plan: Fresh-Session Verification Gate & Decision Receipts

## Target Symbols
- `stages/04-verify/CONTEXT.md` (ICM Layer 2 Stage Contract, <= 80 lines)
- `FreshSessionVerifier` (class in `scripts/hermes_fresh_session_verifier.py`)
- `DecisionLogger` (class in `scripts/hermes_fresh_session_verifier.py`)
- `SystemOneGateType` (Enum for 6 gates: Intent Guard, Rule Guard, Scope Guard, Done Gate, Claims Gate, Commit Guard)

## Causal Hypotheses
1. Stripping conversational history and scratchpad handoffs eliminates self-referential bias and sycophantic hallucination loops during output review.
2. The "One Reader in Three Hats" evaluation systematically validates specifications (Hat 1), evidence grounding (Hat 2), and negative constraints (Hat 3).
3. Append-only `.hermes/decisions/` receipts with SHA-256 snapshot hashes provide cryptographic provenance for all autonomous routing and verification actions.

## Implementation Steps
1. Create `stages/04-verify/CONTEXT.md` complying with ICM <= 80 lines and 4-column load table.
2. Implement `scripts/hermes_fresh_session_verifier.py` with `FreshSessionVerifier`, `DecisionLogger`, and System One gates.
3. Validate with `ruff check scripts/hermes_fresh_session_verifier.py`.
4. Update `.hermes/mcp_ephemeral_bridge.py` to record decisions upon tool completions.
5. Write and execute `03_verify/contract.sh`.
6. Seal `/tmp/hermes_verified_receipt.json` with `all_phases_verified: true`.
