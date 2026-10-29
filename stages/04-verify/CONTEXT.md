# Stage 04 Contract: Fresh-Session Verification & Decision Receipt (04-verify)

## Inputs

| Source | File/Location | Section/Scope | Why |
| :--- | :--- | :--- | :--- |
| Stage 01 Spec | ../01-spec/output/spec_packet.md | ## Acceptance Criteria | Original ground-truth requirements |
| Stage 03 Manifest | ../03-execute/output/execution_manifest.md | Full file | Artifacts and hashes to verify |
| System One Gates | ../../rules/anti_rationalization_tables.md | ## Claims & Commit Guards | Block unverified claims before Git commit |
| ICM Walk Test | ~/.hermes/skills/icm-architect/SKILL.md | ## The Walk Test | 8-point cold-agent verification checklist |

## Process

> 1. Invoke the native delegate_task tool to spawn a fresh, zero-history subagent ("Verifier Hat").
> 2. Instruct the subagent to cold-walk the workspace starting from AGENTS.md and independently verify every claim in execution_manifest.md.
> 3. Execute the 8-point ICM Walk Test (wc -l check on all CONTEXT.md < 80 lines and rules/*.md < 200 lines).
> 4. Write the signed verification report to output/verification_receipt.md and append a decision receipt to .hermes/decisions/.

## Outputs

| Artifact | Location | Format |
| :--- | :--- | :--- |
| Verification Receipt | stages/04-verify/output/verification_receipt.md | Markdown receipt signed by zero-history delegate_task |

## Checkpoint & Audit

* **Checkpoint**: Human review gate before git commit if any Walk Test item or Claims Guard check fails.
* **Audit**: [ ] Verified by zero-history delegate_task; [ ] All CONTEXT.md < 80 lines; [ ] hermes doctor passes with 0 warnings.
