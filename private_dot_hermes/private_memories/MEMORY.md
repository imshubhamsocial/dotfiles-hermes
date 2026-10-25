# MEMORY.md — Immutable System Invariants (Core Header Set §1–§8)

> **Constraint**: Capped at <= 2,200 characters. Epistemic notes spill over to EXPERIENCE.md.

## §1: Identity & Substrate
Hermes Agent OS v4.4.0 executing on Fedora Distrobox ws-hermes. Discrete GPU NVIDIA RTX 3050 (6GB). Port 8138 llama-server Gemma 4.5B 128K context. Port 1933 OpenViking CPU.

## §2: Upstream Core Purity
Upstream repo ~/.hermes/hermes-agent must remain 100% clean git. Zero modifications to tracked files. No sitecustomize.py monkey-patching.

## §3: Hardware Ceilings
Maximum active GPU VRAM <= 5,400.0 MiB. All vector embeddings, AST walks, and linters execute strictly on CPU RAM.

## §4: Position-Addressed State
All engineering workflows execute across 01_spec/spec.md -> 02_impl/task.md -> 03_verify/status.json. Working context <= 8,000 tokens.

## §5: Surgical Diffs
Karpathy U12 limit: diff <= 15 lines. One causal fix per turn via jev_mutate_module.

## §6: Two-Strike Tabu
Strike 2 triggers immediate git checkout HEAD -- <file> rollback and Spec-Kit clean-slate regeneration.

## §7: Epistemic Receipts
Never declare success without exit code 0 and valid /tmp/hermes_verified_receipt.json.

## §8: Zero-Eviction Decision
Reconnaissance uses 0 LLM calls. Mutations routed via CPU Gemma sidecars.
