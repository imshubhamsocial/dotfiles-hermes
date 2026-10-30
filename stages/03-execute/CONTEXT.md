# Stage 03 Contract: Native Execution & LSP Diagnostics (03-execute)

## Inputs

| Source | File/Location | Section/Scope | Why |
| :--- | :--- | :--- | :--- |
| Stage 02 Output | ../02-plan/output/implementation_plan.md | Full file | Approved step-by-step execution blueprint |
| Hardware Rules | ../../rules/hardware_vram_invariants.md | ## Live NVML Verification | Verify GPU VRAM against rules/hardware_vram_invariants.md |
| System One Gates | ../../rules/anti_rationalization_tables.md | ## Done Gate | Prevent premature completion or stubbing |

## Process

> 1. Execute the exact file edits and CLI operations specified in ../02-plan/output/implementation_plan.md.
> 2. Rely on native in-process ast.parse and Pyright LSP (lsp.enabled: true) to validate syntax and types immediately upon edit.
> 3. Verify live GPU memory (nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits) against rules/hardware_vram_invariants.md.
> 4. Record all modified file SHA-256 digests and LSP diagnostic outputs in output/execution_manifest.md.

## Outputs

| Artifact | Location | Format |
| :--- | :--- | :--- |
| Execution Manifest | stages/03-execute/output/execution_manifest.md | Markdown with SHA-256 table and live VRAM readout |

## Checkpoint & Audit

* **Checkpoint**: Halt immediately if Pyright LSP reports diagnostics > 0 or if jev-curator blocks an unauthorized skill mutation.
* **Audit**: [ ] Zero syntax/LSP errors; [ ] Live NVML VRAM verified against rules/hardware_vram_invariants.md; [ ] No untracked scripts created in scripts/.
