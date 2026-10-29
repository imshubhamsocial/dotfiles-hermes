# Phase 52 Specification: Fresh-Session Verification Gate & Append-Only Decision Receipts

## 1. Intent & Architectural Rationale
In multi-turn autonomous reasoning and repair tasks (e.g., Tau-bench Retail and HumanEval repair), models often suffer from self-referential confirmation bias when verifying their own candidate actions within a contaminated conversational context.
Under Jake Van Clief's ICM and the Clief Notes engineering standard, verification must be conducted in an isolated **Fresh-Session Verification Gate** ("One Reader in Three Hats", Gabriel Azoulay & Andrew Carter):
1. **History Stripping**: Conversational chatter, intermediate rationalizations, and `HANDOFF.md` notes are completely excluded from the verification window.
2. **Three Hats Evaluation**:
   - **Hat 1 (Contract & Spec)**: Candidate output strictly fulfills canonical Layer 3 requirements.
   - **Hat 2 (Evidence & Grounding)**: All parameters, IDs, and claims are 100% grounded in observed Layer 4 read-tool outputs without fabrication.
   - **Hat 3 (Policy & Safety Boundaries)**: Action strictly respects 3-Tier boundaries (Always/Ask First/Never) and anti-sycophancy directives.
3. **Append-Only Decision Receipts**: All routing decisions, gate validations, and verification outcomes are cryptographically logged to `.hermes/decisions/decision_receipts.jsonl` with a candidate SHA-256 snapshot hash.

## 2. Technical Deliverables

### 2.1 Layer 2 Verification Contract (`stages/04-verify/CONTEXT.md`)
- Strict line-cap: $\le 80$ lines.
- 4-Column Selective Section Load Table: `Source | File | Section | Why`.
- Defines the isolated fresh-session evaluation protocol.

### 2.2 Fresh-Session Verifier (`scripts/hermes_fresh_session_verifier.py`)
- `FreshSessionVerifier`:
  - `strip_conversational_history(messages)`: Extracts only system contract, observed tool evidence, and proposed candidate output.
  - `evaluate_three_hats(spec_text, evidence_text, candidate)`: Computes deterministic Pass/Fail scores across all three hats.
  - `log_decision_receipt(...)`: Records append-only receipts into `.hermes/decisions/decision_receipts.jsonl` with `candidate_snapshot_hash`, gate outcomes, and timestamps.
- Integrates six System One decision gates: `Intent Guard`, `Rule Guard`, `Scope Guard`, `Done Gate`, `Claims Gate`, and `Commit Guard`.

### 2.3 Hardware & Performance Invariants
- Zero GPU VRAM consumption (0.0 MiB GPU VRAM).
- `query_live_nvml_vram()` MUST verify `used_mib <= 5400.0`.
- Cryptographic receipt sealed at `/tmp/hermes_verified_receipt.json` with `all_phases_verified: true`.
