# Hermes Agent OS: Master Execution Plan & Living Architecture Roadmap

> **Document Status**: Living Architectural Specification & Execution Order  
> **Target Hardware Boundary**: NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM, ≤ 4,812 MiB hard allocation ceiling)  
> **Runtime Philosophy**: CPU-first background batching, zero core package bloat (Law #8), decoupled sidecars, RAMDisk fast-paths (<8ms).

---

## 1. Architectural Invariants (Non-Negotiable Guardrails)

Every item on this roadmap must strictly adhere to the following invariants:

1. **Zero Core Contamination (Law #8)**:
   * **Never** install heavy external frameworks (`cognee`, `lancedb`, `transformers`, `torch`, `unsloth`, `litellm`) into the interactive core environment (`ws-hermes`, `pyproject.toml`, or default Python site-packages).
   * Experimental or batch workloads must live strictly inside isolated environments (e.g., `~/.local/share/cognee-env`, dedicated venvs, or ephemeral sidecars).
2. **Deterministic VRAM Budget Ceiling**:
   * Interactive runtime (`llama-server` with `gemma-4-E4B-it-Q4_K_M` + `mtp-gemma-4-E4B-it-Q4_0` dual-slot `-np 2`) consumes ~4.7 GiB VRAM.
   * Background batch tasks must **never** execute while an interactive session is active on the GPU. NVML idle checks (`active_requests == 0` and `VRAM < 200 MiB` reserved) must gate all batch GPU jobs.
3. **Markdown & RAMDisk Knowledge Bridge**:
   * Background workers digest raw traces and graphs, but serialize their findings into human-readable Markdown cards (`~/.hermes/knowledge/`, `~/.hermes/memories/`) with YAML frontmatter.
   * Hermes core consumes these cards at daytime runtime via native `second_brain.py` and `cog_vault.py` on RAMDisk with zero LLM query overhead.
4. **Contract Test Gate & Chezmoi Synchronization**:
   * No phase is marked complete without passing deterministic unit/contract tests running in `make test-internal`.
   * All configurations, scripts, and tests must be synchronized with `.local/share/chezmoi`.

---

## 2. Completed Milestones Baseline (Current Status)

The following baseline capabilities are implemented, tested, and active:

* [x] **Milestone 0.1: Gemma 4 QAT + MTP Speculative Inference Engine**
  * Base: `gemma-4-E4B-it-Q4_K_M` (direct Google DeepMind QAT-trained tensors via Unsloth/bartowski).
  * Speculative Draft: `mtp-gemma-4-E4B-it-Q4_0` on port 8138 with `--spec-draft-ngl 99`.
  * Dual-slot parallel processing (`-np 2`) for speculative patch testing (`TestTimeComputeSampler`).
* [x] **Milestone 0.2: Tamper-Evident Agent Flight Recorder**
  * Hash-chained deterministic execution ledger (`trajectory.py` and `replay.py`).
* [x] **Milestone 0.3: Official Google `gemma-skills` Integration**
  * Imported `gemma-dev` and `gemma-trainer` into `.hermes/skills/mlops/models/`.
  * Complete contract test suite `test_gemma_skills.py` passing (L0 discovery <100 tokens, dynamic JIT lifecycle, BM25 routing, AST syntax).
  * Overall test suite passing at **188 tests** (`make test-internal`).

---

## 3. Sequential Execution Roadmap (Chronological Implementation Order)

The roadmap is strictly sequenced into prioritized phases. Subsequent tracks build upon the outputs of preceding phases.

```
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 1: Detached Nightly Memory Consolidation (Cognee Evaluation)    │
│ Phase 1.1 (Env) ──► Phase 1.2 (Worker) ──► Phase 1.3 (Cards) ──► 1.4 (Timer)
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 2: Reasoning & Fact-Checking Upgrades (Gemma Ecosystem)         │
│ Phase 2.1 (Gemma-APS in Draft Detective) ──► Phase 2.2 (EmbeddingGemma)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 3: Self-Correction, Adapters & Multimodal Tuning                │
│ Phase 3.1 (Cactus Uncertainty) ──► Phase 3.2 (QLoRA) ──► 3.3 (Vision) │
└────────────────────────────────────────────────────────────────────────┘
```

### Track 1: Detached Nightly Memory Consolidation (Cognee Evaluation)
*Goal: Autonomous, off-peak "Sleep / Memory Dream" cycle distilling daily trajectories and git diffs into knowledge cards without core bloat.*

| Sequence | Milestone & Scope | Deliverables & Implementation Details | Gate / Verification Criteria |
| :---: | :--- | :--- | :--- |
| **1.1** | **Isolated Virtualenv Provisioning** | • Provision dedicated directory `~/.local/share/cognee-env`<br>• Install `cognee` and minimal graph dependencies strictly inside this venv<br>• Zero exposure to `ws-hermes` or `pyproject.toml` | `~/.local/share/cognee-env/bin/python -c "import cognee"` succeeds; core container `python3.13 -c "import cognee"` raises `ModuleNotFoundError`. |
| **1.2** | **Nightly Ingestion & Distillation Worker** | • Author `.hermes/scripts/nightly_memory_consolidation.py`<br>• Read-only ingestion of daily `~/.hermes/sessions/`, `trajectory.jsonl`, and git commit diffs<br>• Extract recurring patterns, bug solutions, and entity graphs | Dry-run script runs headless in isolated environment, parsing raw trajectories and generating structured intermediate graph nodes. |
| **1.3** | **Markdown Synthesis & Second Brain Bridge** | • Serialize extracted graph relations into formatted Markdown cards with YAML frontmatter<br>• Populate cards into `~/.hermes/knowledge/` and `~/.hermes/memories/`<br>• Bridge into native `second_brain.py` and `cog_vault.py` | `second_brain.search(...)` locates synthesized cross-session concepts on RAMDisk in <8ms with 0 MiB VRAM overhead. |
| **1.4** | **Systemd Timer Automation & VRAM Safeguards** | • Author systemd user unit `hermes-memory-consolidation.service` and `.timer` (scheduled at 03:00 AM)<br>• Pre-exec NVML check: abort if GPU is busy or interactive `llama-server` has active requests | Systemd timer triggers cleanly; logs demonstrate execution completes and exits cleanly before morning sessions. |

---

### Track 2: Reasoning & Fact-Checking Upgrades
*Goal: Enhance pre-commit code verification and vector retrieval alignment using Google DeepMind's specialized models.*

| Sequence | Milestone & Scope | Deliverables & Implementation Details | Gate / Verification Criteria |
| :---: | :--- | :--- | :--- |
| **2.1** | **Gemma-APS Claim Deconstruction in Draft Detective** | • Integrate Abstractive Proposition Segmentation (APS) principles into `draft_detective.py`<br>• Decompose model code explanations and docstrings into atomic semantic claims<br>• Cross-reference claims against AST static analysis before commits | Unit tests verify that generated claims are mapped to AST function signatures and flagged if docstrings contradict code behavior. |
| **2.2** | **EmbeddingGemma On-Device Evaluation** | • Benchmark EmbeddingGemma (300M, CPU ONNX) against current `bge-small-en-v1.5` in `opencode_mem.py`<br>• Evaluate tokenizer alignment with Gemma 4 vocabulary and retrieval accuracy across repo search | EmbeddingGemma achieves comparable or superior retrieval Recall@5 on Hermes codebase with CPU latency <25ms per chunk. |

---

### Track 3: Long-Term & Experimental Enhancements
*Goal: Local adapter fine-tuning, self-correction loops, and multimodal vision token optimization.*

| Sequence | Milestone & Scope | Deliverables & Implementation Details | Gate / Verification Criteria |
| :---: | :--- | :--- | :--- |
| **3.1** | **Cactus Hybrid Uncertainty Detection** | • Study Cactus Hybrid self-reporting techniques for uncertainty identification<br>• Integrate uncertainty scoring into supervisory scan (`lineage.py`) and 2-strike tabu rule | Agent autonomously halts execution and asks clarifying questions when confidence drops below threshold before destructive edits. |
| **3.2** | **Unsloth On-Device QLoRA Fine-Tuning** | • Leverage bundled `gemma-trainer` assets with Unsloth in a detached container<br>• Train task-specific low-rank adapters for Hermes U41 LoRA adapter manager on the RTX 3050 Laptop GPU | LoRA adapter exports cleanly to GGUF format and hot-swaps onto base Gemma 4 model with zero baseline regression. |
| **3.3** | **Multimodal Vision Token Optimization** | • Calibrate `visual_arbiter.py` using Google's Gemma 4 Vision Token Budget formulas<br>• Dynamic downsampling and patch budgeting to keep image inputs within tight context bounds | Visual inspector turns remain strictly within the allocated token budget without truncating chat history. |

---

## 4. Ecosystem Intelligence & Validation Register

This register benchmarks official Google Gemma ecosystem assets against Hermes Agent OS architecture.

### Actionable Assets (Integrated or Scheduled)
| Asset | Category | Hermes Integration Point | Current Status |
| :--- | :--- | :--- | :---: |
| [gemma-skills](https://github.com/google-gemma/gemma-skills) | Skills Hub | Drop-in standard skill packages (`gemma-dev` & `gemma-trainer`) in `.hermes/skills/mlops/models/` | ✅ **Active & Verified** (188 tests passing) |
| [Gemma 4 QAT](https://huggingface.co/collections/google/gemma-4-qat-q4-0) | Core Weights | Official Quantization-Aware Trained 4-bit weights (`Q4_0` / `Q4_K_M`) for base and draft | ✅ **Active in Runtime** |
| [EmbeddingGemma](https://huggingface.co/collections/google/embeddinggemma) | Embeddings | Compact 300M embedding model for CPU ONNX retrieval in `opencode_mem.py` | 📋 Scheduled (Track 2.2) |
| [Gemma-APS](https://huggingface.co/collections/google/gemma-aps-release) | Verification | Abstractive Proposition Segmentation for atomic claim verification in `draft_detective.py` | 📋 Scheduled (Track 2.1) |

### Architectural Validation (Invariants Confirmed)
| Asset | Core Validation Finding | Hermes Design Confirmation |
| :--- | :--- | :--- |
| [Gemma 4 + MTP Marathon Engine](https://dev.to/gde/the-local-model-that-doesnt-sleep-gemma-4-mtp-as-a-marathon-engine-4c9) | Confirms Gemma 4 + MTP speculative draft sustains high throughput and stable memory over long context | Confirms `--model-draft mtp-gemma-4-E4B-it-Q4_0 --spec-draft-ngl 99` is optimal |
| [Concurrent Gemma](https://github.com/google-gemma/cookbook/tree/main/apps/concurrent) | Confirms multi-slot local Gemma concurrency patterns | Confirms our `llama-server -np 2` dual-slot layout for `TestTimeComputeSampler` |
| [Trajectix](https://www.kaggle.com/competitions/gemma-4-good-hackathon/writeups/trajectix-an-agentic-flight-recorder-for-ai-infra) | Confirms necessity of tamper-evident action tracking | Confirms hash-chained `trajectory.py` and `replay.py` design |

---

## 5. Protocol for Updating Plan.md & Ingesting New Discoveries ("Updating More Stuff")

To maintain architectural integrity and prevent roadmap fragmentation, any new tool, research paper, or feature request must pass through the **4-Gate Ingestion Protocol** before being added to this document:

```
[New Proposal / Link]
          │
          ▼
┌────────────────────────────────────────┐
│ Gate 1: Zero Core Contamination?       │──► NO  ──► Reject or isolate to Sidecar
└──────────────────┬─────────────────────┘
                   │ YES
                   ▼
┌────────────────────────────────────────┐
│ Gate 2: Fits ≤ 4,812 MiB VRAM Ceiling? │──► NO  ──► Route to Off-Peak CPU Batch
└──────────────────┬─────────────────────┘
                   │ YES
                   ▼
┌────────────────────────────────────────┐
│ Gate 3: Deterministic Contract Test?   │──► NO  ──► Require mockable test plan
└──────────────────┬─────────────────────┘
                   │ YES
                   ▼
┌────────────────────────────────────────┐
│ Gate 4: Chezmoi Tracking Compatible?   │──► NO  ──► Refactor into dotfile paths
└──────────────────┬─────────────────────┘
                   │ YES
                   ▼
    [Assign Track & Sequence ID]
```

### Standard Intake Template for New Items
When adding a new item to `Plan.md`, use this exact schema:

```markdown
### Phase X.Y: [Feature / Research Name]
* **Category**: [Track 1 (Memory) | Track 2 (Reasoning) | Track 3 (Experimental) | Tooling]
* **Trigger / Motivation**: [Why this is needed and what problem it solves]
* **Resource Link**: [Link to repository, paper, or model card]
* **Architecture Isolation**: [In-core | Sidecar Env | Off-peak Batch | Skill Package]
* **Hardware Impact**: [0 MiB VRAM / CPU-only | Batch NVML Gated | Interactive Budget]
* **Deliverables**:
  1. [Code changes / script paths]
  2. [Contract test path]
* **Verification Gate**: [Exact command or test that proves success]
* **Chezmoi Files**: [Paths tracked in .local/share/chezmoi]
```
