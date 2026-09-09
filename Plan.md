# Master Execution Plan: Future Roadmap & Nightly Memory Architecture

> **Status**: Future Living Execution Plan  
> **Target**: Detached Nightly Memory Consolidation ("Sleep Cycle") without Core Bloat  
> **Hardware Boundary**: NVIDIA RTX 3050 Laptop (6GB VRAM, ≤ 4,812 MiB limit), Off-Peak Batch Execution  

---

## Architectural Focus: Detached Nightly Memory Consolidation (Cognee Evaluation)

### Objective
Implement an autonomous, off-peak "Sleep / Memory Dream" consolidation cycle that ingests daily agent trajectories, diffs, and raw memory notes, distilling them into an entity-relation knowledge graph—without contaminating Hermes's core runtime with heavy dependencies or competing for GPU resources during interactive sessions.

### Invariant Architectural Rules
1. **Zero Core Contamination (Law #8)**:
   * **DO NOT** install `cognee`, `lancedb`, `ladybug`, `fakeredis`, or `litellm` into Hermes's core runtime (`ws-hermes`, `pyproject.toml`, or main `Makefile`).
   * Cognee and its dependency tree must live strictly inside a detached, isolated environment (e.g., `~/.local/share/cognee-env` or a separate sidecar container).
2. **Off-Peak Batch Window**:
   * Execution scheduled exclusively during off-peak hours (e.g., nightly at 03:00 AM via systemd user timer or cron).
   * Zero contention with interactive daytime coding turns on `llama-server` port 8138.
3. **Markdown-First Distillation Output**:
   * The worker digests transcripts and raw logs, but writes distilled relational findings into standard, human-readable Markdown cards in `~/.hermes/knowledge/` and `~/.hermes/memories/`.
   * Hermes core consumes these cards at daytime run-time via its existing native `second_brain.py` and `cog_vault.py` on CPU RAMDisk (<8ms latency, 0 MiB VRAM).
4. **Fail-Safe Decoupling**:
   * Any failure or crash in the nightly worker must never impact Hermes core CLI or agent execution.

---

## Phased Implementation Matrix

| Phase | Scope & Description | Status | Verification Criteria |
| :--- | :--- | :---: | :--- |
| **Phase 1** | **Isolated Environment Provisioning**<br>• Create dedicated virtual environment at `~/.local/share/cognee-env`<br>• Install `cognee` and verify isolated execution<br>• Confirm zero leakage into `ws-hermes` core user-site | 📋 **PLANNED** | `cognee --version` passes in isolated env; `python3.13 -c "import cognee"` fails cleanly in `ws-hermes` |
| **Phase 2** | **Nightly Ingestion & Distillation Pipeline**<br>• Author `.hermes/scripts/nightly_memory_consolidation.py`<br>• Read-only ingestion of `~/.hermes/sessions/`, `trajectory.jsonl`, and git logs<br>• Distill cross-session entity connections, recurring bugs, and project patterns | 📋 **PLANNED** | Script executes headless in dry-run mode, producing structured graph nodes in temporary cache |
| **Phase 3** | **Markdown Synthesis & Second Brain Bridge**<br>• Format extracted graph relationships into clean Markdown cards<br>• Populate cards with YAML frontmatter into `~/.hermes/knowledge/`<br>• Verify seamless retrieval by native `second_brain.py` and `cog_vault.py` | 📋 **PLANNED** | `second_brain.search(...)` locates synthesized cross-session concepts without LLM extraction overhead |
| **Phase 4** | **Systemd Timer / Cron Automation & VRAM Safeguards**<br>• Register user systemd service/timer (`hermes-memory-consolidation.timer`)<br>• Bind NVML check: only run if GPU is idle (`VRAM < 200 MiB` or when `llama-server` has 0 active requests)<br>• End-to-end integration run | 📋 **PLANNED** | Daemon runs unattended at scheduled hour; morning session verifies updated knowledge base with zero core regressions |
