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

---

## Ecosystem Intelligence: Official Google Gemma Ecosystem Analysis

### 🔍 Comprehensive Analysis of awesome-gemma for Hermes Agent OS

The [google-gemma/awesome-gemma](https://github.com/google-gemma/awesome-gemma) repository is Google DeepMind's official index of the Gemma ecosystem.
Below is an evaluation of every section and link, categorized by what we can immediately use, what validates our architecture, and what to avoid.

---

### 1. Highly Useful & Actionable for Hermes (Recommended to Adopt)

| Resource / Link | What It Is | How Hermes Can Use It |
| :--- | :--- | :--- |
| [gemma-skills](https://github.com/google-gemma/gemma-skills) | Google's official agent skills repository (gemma-dev & gemma-trainer) formatted as standard `SKILL.md` packages. | **Direct Drop-in**: We can import gemma-dev and gemma-trainer straight into Hermes's skill hub (`~/.hermes/skills/`). It equips Hermes with exact knowledge of Gemma 4 prompting conventions, control tokens, and tuning parameters. |
| [Gemma 4 QAT](https://huggingface.co/collections/google/gemma-4-qat-q4-0) | Official Quantization-Aware Trained (QAT) 4-bit checkpoints (`Q4_0`). | **Model Upgrade**: Currently, we run standard post-training quantized GGUF (`gemma-4-E4B-it-Q4_K_M`). Google's QAT weights are trained with quantization awareness, delivering higher reasoning fidelity, lower perplexity, and better instruction adherence at the exact same VRAM footprint. |
| [EmbeddingGemma](https://huggingface.co/collections/google/embeddinggemma) | Compact 300M parameter embedding model designed specifically for on-device retrieval (2K token context, 128–768 dimensions). | **Future Retrieval Engine**: Could serve as a native Google alternative to `bge-small-en-v1.5` in `opencode_mem.py` (CPU ONNX), offering better semantic alignment with Gemma's tokenizer. |
| [Gemma-APS](https://huggingface.co/collections/google/gemma-aps-release) | Abstractive Proposition Segmentation: decomposes complex technical prose into atomic semantic claims. | **AST Fact-Checking**: Highly relevant for `draft_detective.py` to decompose model code explanations into testable claims before pre-commit. |

---

### 2. Architectural & Benchmark Validation (Confirms Hermes Design)

| Resource / Link | Core Finding | How It Validates Our Invariants |
| :--- | :--- | :--- |
| [Gemma 4 + MTP as Marathon Engine](https://dev.to/gde/the-local-model-that-doesnt-sleep-gemma-4-mtp-as-a-marathon-engine-4c9) | Deep empirical benchmark proving Gemma 4 + MTP speculative draft model sustains high throughput and stable memory over long context runs. | **Validates Hardware Config**: Validates our dual-model launch flags (`--model gemma-4-E4B-it-Q4_K_M --model-draft mtp-gemma-4-E4B-it-Q4_0 --spec-draft-ngl 99`), confirming high draft acceptance rate without KV degradation. |
| [Concurrent Gemma](https://github.com/google-gemma/cookbook/tree/main/apps/concurrent) | Recipes and concurrency tests for running multiple concurrent slots on local Gemma instances. | **Validates Dual-Slot Topology**: Confirms our `llama-server -np 2` dual-slot layout for parallel speculative patch testing (`TestTimeComputeSampler`) is the official best practice. |
| [Trajectix](https://www.kaggle.com/competitions/gemma-4-good-hackathon/writeups/trajectix-an-agentic-flight-recorder-for-ai-infra) | "Agentic Flight Recorder" for AI safety and action tracking. | **Validates Trajectory Engine**: Directly mirrors Hermes's hash-chained `trajectory.py` and `replay.py` design for verifiable, tamper-evident execution logs. |

---

### 3. Compelling Future Enhancements (Experimental / Long-Term)

| Resource / Link | Concept | Potential Role in Hermes |
| :--- | :--- | :--- |
| [Cactus Hybrid](https://github.com/cactus-compute/cactus-hybrid) | Post-trained Gemma models tuned to explicitly recognize when they make a mistake and flag uncertainty. | **Self-Correction Loops**: Could enhance Hermes's supervisory scan (`lineage.py`) and 2-strike tabu rule by having the agent self-report flawed code hypotheses before running tests. |
| [Unsloth Gemma 4 Training](https://unsloth.ai/docs/models/gemma-4/train) | Ultra-fast QLoRA fine-tuning for Gemma on consumer GPUs. | **Local Adapter Fine-Tuning**: If we ever want to train project-specific LoRA adapters on the RTX 3050 Laptop GPU for Hermes's U41 LoRA adapter manager. |
| [Gemma 4 Vision Token Budget](https://huggingface.co/spaces/google/gemma4_vision_token_budget) | Visual-token budget explorer for multimodal inputs. | **Visual Arbiter Optimization**: Useful for tuning `visual_arbiter.py` image downsampling to keep multimodal turns within strict token ceilings. |

