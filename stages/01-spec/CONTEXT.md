# Stage 01 Contract: Specification & Intent Scoping (01-spec)

## Inputs

| Source | File/Location | Section/Scope | Why |
| :--- | :--- | :--- | :--- |
| User Task | Active Prompt / Issue | Full description | Primary problem statement |
| Hardware Rules | ../../rules/hardware_vram_invariants.md | ## Envelope Limits | Enforce hardware VRAM & zero-code bounds per rules/hardware_vram_invariants.md |
| System One Gates | ../../rules/anti_rationalization_tables.md | ## Intent & Scope Guards | Prevent scope creep and unrequested code |
| Epistemic Rules | ../../rules/anti_sycophancy_directives.md | ## Premise Validation | Reject flawed user assumptions early |

## Process

> 1. Parse the user request and inspect referenced files using native file_tools or openviking memory search.
> 2. Validate the request against Intent Guard and Scope Guard: confirm zero custom orchestration scripts are requested.
> 3. Define explicit acceptance criteria, touched file boundaries, and hardware invariants.
> 4. Run the Stage 01 Audit below and write output/spec_packet.md.

## Outputs

| Artifact | Location | Format |
| :--- | :--- | :--- |
| Specification Packet | stages/01-spec/output/spec_packet.md | Markdown with YAML frontmatter (status, scope_hash) |

## Checkpoint & Audit

* **Checkpoint**: Pause if user requirements conflict with the Zero-Custom-Code Imperative or rules/hardware_vram_invariants.md ceiling.
* **Audit**: [ ] Exact target files listed; [ ] No custom .py wrappers proposed; [ ] Hardware ceiling explicitly cited.
