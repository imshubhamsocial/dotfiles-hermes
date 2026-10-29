# Stage 02 Contract: Architectural Planning & Reference Integrity (02-plan)

## Inputs

| Source | File/Location | Section/Scope | Why |
| :--- | :--- | :--- | :--- |
| Stage 01 Output | ../01-spec/output/spec_packet.md | Full file | Approved problem scope and invariants |
| Substrate Map | ../../_config/substrate_ports.md | ## Active Daemon Table | Verify native port & plugin endpoints |
| System One Gates | ../../rules/anti_rationalization_tables.md | ## Rule Guard | Verify compliance with ICM conventions |
| ICM Architect | ~/.hermes/skills/icm-architect/SKILL.md | ## Reference Integrity | Enumerate all inbound links before moving files |

## Process

> 1. Read ../01-spec/output/spec_packet.md and map every required change to declarative configs, Markdown contracts, or official plugins.
> 2. Perform reference integrity verification: before moving or archiving any file, enumerate all in-repo and systemd/cron references.
> 3. If modifying skills, run hermes jev-curator plan to check 8-way semantic relations (duplicate, a_subset_of_b, conflict).
> 4. Complete the Stage 02 Audit and write output/implementation_plan.md.

## Outputs

| Artifact | Location | Format |
| :--- | :--- | :--- |
| Implementation Plan | stages/02-plan/output/implementation_plan.md | Markdown with step-by-step diff specification |

## Checkpoint & Audit

* **Checkpoint**: Present output/implementation_plan.md for human gate review if modifying ~/.hermes/config.yaml or deleting files.
* **Audit**: [ ] One-way stage references preserved; [ ] All CONTEXT.md edits remain < 80 lines; [ ] Zero circular dependencies.
