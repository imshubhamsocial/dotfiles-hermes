# Hermes Agent OS — Layer 1 Pipeline Router (CONTEXT.md)

## 1. Pipeline Sequence & Handoffs

Work progresses sequentially through four numbered folders. Each stage reads the prior stage's output/ artifact and writes solely to its own output/ directory.

| Stage | Folder | Single Responsibility | Output Artifact | Human/System Gate |
| :--- | :--- | :--- | :--- | :--- |
| **01** | stages/01-spec/ | Extract problem bounds & invariants | output/spec_packet.md | Intent & Scope Guard |
| **02** | stages/02-plan/ | Formulate file-level execution plan | output/implementation_plan.md | Rule Guard & Jev Plan Check |
| **03** | stages/03-execute/ | Apply changes & pass Pyright LSP | output/execution_manifest.md | Zero LSP Errors & VRAM Check |
| **04** | stages/04-verify/ | Cold-start verification via delegate_task | output/verification_receipt.md | Done, Claims & Commit Guards |

## 2. Shared Factory Reference Index (Layer 3)

* _config/substrate_ports.md: Port 8138 (GPU LLM), Port 8139 (CPU Embed), Port 8642 (Gateway), Port 1933 (OpenViking).
* rules/hardware_vram_invariants.md: Live NVML VRAM <= 5,400.0 MiB ceiling and CPU thread pinning (0-5 GPU, 6-11 CPU).
* rules/anti_rationalization_tables.md: Six System One Jev Gates (rashedint32/jev-gates).
* rules/anti_sycophancy_directives.md: 17 epistemic grounding rules (RinDig/GPTmetrics).
