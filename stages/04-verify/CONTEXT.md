# Stage 04-verify: Fresh-Session Adversarial Verification Contract

> **ICM Layer 2 Stage Gate**: Fresh-Session Verification ("One Reader in Three Hats")  
> **Precondition**: Candidate code synthesis or state mutation proposed in Layer 4.  
> **Postcondition**: Cryptographically sealed decision receipt in `.hermes/decisions/`.

## 1. Selective Section Loading Schema

| Source | File | Section | Why |
| :--- | :--- | :--- | :--- |
| Layer 0 | `AGENTS.md` | `## Stage Gate Machine` | Deterministic verification criteria and strike gates. |
| Layer 3 | `rules/anti_rationalization_tables.md` | `## Common Rationalisations` | Detects false-pass and lazy confirmation traps. |
| Layer 3 | `rules/anti_sycophancy_directives.md` | `## Directives` | Prevents sycophantic approval of ungrounded changes. |
| Layer 4 | Active Phase Contract | `contract.sh` | Deterministic execution suite and exit code verification. |

## 2. History Stripping Protocol
1. **Exclude Intermediate Context**: Completely block all conversational chatter, scratchpad notes, and `HANDOFF.md`.
2. **Isolate Verification Triad**:
   - Canonical Layer 3 Specification (`spec.md`).
   - Grounded Layer 4 Read Evidence (Prior verified tool outputs).
   - Candidate Mutation/Output (Under review).

## 3. "One Reader in Three Hats" Protocol
- **Hat 1 (Contract & Spec)**: Does the candidate strictly satisfy the specification and contract without scope creep?
- **Hat 2 (Evidence & Grounding)**: Are all IDs, parameters, and assertions present in Layer 4 read evidence?
- **Hat 3 (Policy & Safety Boundaries)**: Does the candidate preserve all 3-Tier permissions and negative invariants?

## 4. Decision Recording Invariant
Every evaluation MUST log an append-only receipt to `.hermes/decisions/decision_receipts.jsonl` containing:
- `timestamp`: ISO-8601 UTC timestamp.
- `candidate_snapshot_hash`: SHA-256 hash of the exact candidate output.
- `gate_name`: One of the 6 System One decision gates.
- `routing_probs`: Confidence scores across hats.
- `outcome`: `PASS`, `REJECT`, or `BLOCKED`.
