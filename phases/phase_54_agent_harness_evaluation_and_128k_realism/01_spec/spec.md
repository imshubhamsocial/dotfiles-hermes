# Phase 54 Specification: Agent Harness Evaluation & 128K Hardware Realism

## 1. Problem Statement

> 1. **The 32K Context & 5,400 MiB VRAM Drift**: Upstream NousResearch/hermes-agent enforces MINIMUM_CONTEXT_LENGTH = 64_000 in agent/model_metadata.py and agent/agent_init.py. Furthermore, live NVML telemetry on the NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB GDDR6) confirms Disp.A: Off (Wayland runs on the AMD Radeon iGPU using 6 MiB on the NVIDIA card). At 128K context (-c 131072) with Google TurboQuant Q4_0 KV cache (-ctk q4_0 -ctv q4_0), active VRAM is 5,201–5,239 MiB measured on Baseline and projected at 5,128–5,554 MiB across all three candidate models. However, AGENTS.md, CONTEXT.md, stages/03-execute/CONTEXT.md, and rules/hardware_vram_invariants.md still duplicate the obsolete 5,400.0 MiB cap, violating ICM Walk Test Point 5 (Single Source of Truth) and blocking Tier 1B (Nemotron-3.5-Bolt-E4B + DFlash at 5,554 MiB).
> 2. **The Layer A vs. Layer B Benchmarking Mismatch**: Pointing passive schema-emission benchmarks (inspect_evals/bfcl) at Port 8642 yields false negatives (0.000) because hermes gateway autonomously executes tools via _run_agent() and returns the completed answer in message.content. Conversely, pointing benchmarks at Port 8138 bypasses Hermes Agent OS entirely.

## 2. Inputs & References

* Layer 0 Workspace Map: AGENTS.md
* Layer 1 Pipeline Router: CONTEXT.md
* Layer 2 Stage 03 Contract: stages/03-execute/CONTEXT.md
* Layer 3 Hardware Invariants: rules/hardware_vram_invariants.md
* Canonical Configuration: private_dot_hermes/config.yaml (~/.hermes/config.yaml)
* Build & Evaluation Orchestrator: Makefile

## 3. Core Invariants & Token Budgets

* **Zero Bespoke Code**: 0 custom .py or .sh wrappers in scripts/ or plugins/.
* **Upstream Substrate Purity**: .hermes/hermes-agent must have 0 uncommitted git modifications.
* **Line & Token Discipline**: All CONTEXT.md files <= 80 lines; all Layer 3 rules/*.md files <= 200 lines; active working context strictly within 2,000–8,000 tokens.
* **128K Hardware Invariant**: -c 131072 (context_length: 131072) with -ctk q4_0 -ctv q4_0, Disp.A: Off, and live NVML VRAM <= 5,800.0 MiB (leaving >= 344 MiB hard safety buffer below 6,144 MiB physical GDDR6).

## 4. Acceptance Criteria

* [x] rules/hardware_vram_invariants.md is established as the single source of truth for the 5,800.0 MiB ceiling, Disp.A: Off, and -c 131072 -ctk q4_0 -ctv q4_0.
* [x] AGENTS.md, CONTEXT.md, and stages/03-execute/CONTEXT.md link to rules/hardware_vram_invariants.md without duplicating raw MiB literals (passing ICM Walk Test Point 5).
* [x] private_dot_hermes/config.yaml registers all three candidate models (gemma-4-E4B-it-qat, gemma-4-E4B-it-qat-exact, nemotron-3.5-bolt-e4b) at context_length: 131072 and includes execution_guidance: false.
* [x] Makefile defines canonical Layer B Agent Harness targets (benchmark-harness-gaia, benchmark-harness-tau-react, benchmark-harness-tau2, benchmark-adk, run-eval).
* [x] 03_verify/contract.sh passes all 10 deterministic assertions and seals 03_verify/status.json and phases/status_ledger.json at Phase 54.
