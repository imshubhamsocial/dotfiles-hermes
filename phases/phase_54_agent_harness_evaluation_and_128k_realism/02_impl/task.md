# Phase 54 Implementation Task Plan: Declarative File Updates & CLI Execution

## Step 1: Update Layer 3 Hardware Invariants (rules/hardware_vram_invariants.md)
Established `rules/hardware_vram_invariants.md` as the single source of truth for the 5,800.0 MiB ceiling, 128K context window (`-c 131072`), Google TurboQuant Q4_0 KV cache (`-ctk q4_0 -ctv q4_0`), and dedicated GPU envelope (`Disp.A: Off`).

## Step 2: Deduplicate VRAM Literals in AGENTS.md, CONTEXT.md, and stages/
Purged obsolete 5,400.0 MiB hardcoded numbers from `AGENTS.md`, `CONTEXT.md`, `stages/01-spec/CONTEXT.md`, and `stages/03-execute/CONTEXT.md`, linking directly to `rules/hardware_vram_invariants.md`.

## Step 3: Update Canonical Configuration (~/.hermes/config.yaml & private_dot_hermes/config.yaml)
Registered all three candidate models at `context_length: 131072`, added `execution_guidance: false` under `agent:`, set `approvals.mode: "off"`, and added `~/.hermes/skills` to `skills.external_dirs`.

## Step 4: Update Makefile Benchmark Targets (Layer B Agent Harness Suite)
Added canonical Layer B evaluation targets (`benchmark-harness-gaia`, `benchmark-harness-tau-react`, `benchmark-harness-tau2`, `benchmark-adk`, `run-eval`) against Port 8642 and CLI.
