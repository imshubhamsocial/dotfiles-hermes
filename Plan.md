# Hermes Agent OS: Master Execution Plan & Living Architecture Roadmap

> **Document Status**: Living Architectural Specification & Execution Order  
> **Target Hardware Boundary**: NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM, ≤ 4,812 MiB hard allocation ceiling)  
> **Runtime Philosophy**: CPU-first background batching, zero core package bloat (Law #8), decoupled sidecars, RAMDisk fast-paths (<8ms).

---

## 1. Architectural Invariants (Non-Negotiable Guardrails)

Every item on this roadmap must strictly adhere to the following invariants:

1. **Zero Core Contamination (Law #8)**:
   * **Never** install heavy external frameworks (`graphifyy`, `tree-sitter`, `cognee`, `lancedb`, `transformers`, `torch`, `unsloth`, `litellm`) into the interactive core environment (`ws-hermes`, `pyproject.toml`, or default Python site-packages).
   * External graph parsers and batch workloads must live strictly inside isolated environments (e.g., `~/.local/share/graphify-env`, `~/.local/share/cognee-env`, or dedicated CLI tools).
2. **Deterministic VRAM Budget Ceiling**:
   * Interactive runtime (`llama-server` with `gemma-4-E4B-it-Q4_K_M` + `mtp-gemma-4-E4B-it-Q4_0` dual-slot `-np 2`) consumes ~4.7 GiB VRAM.
   * Background batch tasks must **never** compete for GPU resources during an interactive session. AST parsing via Graphify is **100% CPU-bound** (0 MiB VRAM), making it completely collision-free.
3. **Markdown & RAMDisk Knowledge Bridge**:
   * Background workers digest code ASTs, SQL schemas, and traces, serializing findings into human-readable Markdown cards (`~/.hermes/knowledge/codebase/`, `~/.hermes/memories/`) with YAML frontmatter.
   * Hermes core consumes these cards at daytime runtime via native `second_brain.py` and `cog_vault.py` on RAMDisk with zero LLM query overhead.
4. **Contract Test Gate & Chezmoi Synchronization**:
   * No phase is marked complete without passing deterministic unit/contract tests running in `make test-internal`.
   * All configurations, scripts, and tests must be synchronized with `.local/share/chezmoi`.
5. **Harness-First Native Self-Audit (Zero Loose Tests Objective)**:
   * Standalone test files created during experimentation are scaffolding.
   * Once an end-to-end capability stabilizes, its contract verification probes must be folded directly into Hermes's native self-audit harness (`verify_harness_integrity.py`, `hermes doctor`, internal health probes).
   * The ultimate architectural state of Hermes Agent OS is self-evaluating and self-auditing, eliminating the need for bulky, external loose test directories.

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
* [x] **Milestone 0.4: Local AST Codebase Knowledge Graph via Graphify**
  * Provisioned decoupled environment `~/.local/share/graphify-env` with zero core contamination (Law #8).
  * Authored `.hermes/scripts/build_codebase_graph.py` with headless AST extraction and SecondBrain bridge.
  * Installed Hermes skill package `graphify` into `.hermes/skills/engineering/code/graphify/`.
  * Complete contract test suite `test_graphify_bridge.py` passing (193 total internal tests passing via `make test-internal`).
* [x] **Milestone 0.5: Gemma-APS Proposition Deconstruction in Draft Detective**
  * Enhanced `draft_detective.py` with `PropositionSegmenter` and `ASTPropositionVerifier`.
  * Deconstructs technical prose into atomic propositions (signatures, defaults, returns, exceptions, classes).
  * Enforces static AST ground-truth matching and catches contradictory claims before pre-commit.
  * Native harness probe `probe_draft_detective_gemma_aps()` integrated into master self-audit (197 total internal tests passing via `make test-internal`).

---

## 3. Sequential Execution Roadmap (Chronological Implementation Order)

The roadmap is strictly sequenced into prioritized phases. Subsequent tracks build upon the outputs of preceding phases.

```
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 1: Local AST Codebase Knowledge Graph via Graphify (COMPLETED)   │
│ ✅ Phase 1.1 (Env) ──► ✅ 1.2 (Worker) ──► ✅ 1.3 (Wiki) ──► ✅ 1.4 (Tests)
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 2: Conversational Memory Dream Consolidation (Cognee) [ON HOLD]  │
│ ⏸️ Placed on hold for future multi-turn episodic memory evaluation    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 3: Reasoning & Fact-Checking Upgrades (Gemma Ecosystem)         │
│ Phase 3.1 (Gemma-APS in Draft Detective) ──► Phase 3.2 (EmbeddingGemma)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TRACK 4: Self-Correction, Adapters & Multimodal Tuning                │
│ Phase 4.1 (Cactus Uncertainty) ──► Phase 4.2 (QLoRA) ──► 4.3 (Vision) │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Track 1: Local AST Codebase Knowledge Graph via Graphify (✅ COMPLETED)
*Goal: Deterministic, vector-store-free knowledge graph generation for codebases, schemas, and architecture docs. Converts code into Markdown wiki articles for Hermes's native RAMDisk second brain.*

| Sequence | Milestone & Scope | Status | Deliverables & Implementation Details | Gate / Verification Criteria |
| :---: | :--- | :---: | :--- | :--- |
| **1.1** | **Isolated Graphify Environment Provisioning** | ✅ **DONE** | • Provisioned dedicated directory `~/.local/share/graphify-env` via `uv`<br>• Installed `graphifyy` with tree-sitter bindings strictly inside this venv<br>• Zero exposure to `ws-hermes` or `pyproject.toml` | `~/.local/share/graphify-env/bin/graphify --version` succeeds; core container `python3.13 -c "import graphifyy"` raises `ModuleNotFoundError`. |
| **1.2** | **Codebase Graph Ingestion Script** | ✅ **DONE** | • Authored `.hermes/scripts/build_codebase_graph.py`<br>• Invokes isolated graphify CLI headlessly to generate AST graph, community clusters, and god node reports | Script generates `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` on Hermes repository in CPU user space. |
| **1.3** | **Markdown Wiki & Second Brain Bridge** | ✅ **DONE** | • Bridges `graphify-out/wiki/` articles into `~/.hermes/knowledge/concepts/`<br>• Verified fast-path search by `second_brain.py` (<8ms, 0 MiB VRAM)<br>• Added Hermes skill `graphify` under `.hermes/skills/engineering/code/graphify/` | Hermes queries locate cross-module AST relationships and call graphs from RAMDisk without reading raw source files into context. |
| **1.4** | **Contract Tests & Chezmoi Sync** | ✅ **DONE** | • Authored `.hermes/tests/core/test_graphify_bridge.py`<br>• Validated L0 skill discovery, JSON graph parsing, and Wiki Markdown ingestion<br>• Committed to Chezmoi | `pytest .hermes/tests/core/test_graphify_bridge.py` passes 5/5; `make test-internal` passes with 193/193 tests green. |

---

### Track 2: Conversational Memory Dream Consolidation (Cognee Evaluation) — [⏸️ ON HOLD FOR FUTURE]
*Goal: Autonomous, off-peak "Sleep / Memory Dream" cycle distilling multi-session conversation trajectories into knowledge cards. Marked on hold until episodic multi-turn memory consolidation is specifically scheduled.*

| Sequence | Milestone & Scope | Status | Deliverables & Implementation Details |
| :---: | :--- | :---: | :--- |
| **2.1** | **Isolated Sidecar Virtualenv** | ⏸️ **ON HOLD** | Dedicated `~/.local/share/cognee-env` provisioned via `uv` with `cognee` and minimal graph dependencies. |
| **2.2** | **Nightly Ingestion Worker** | ⏸️ **ON HOLD** | Ingests `~/.hermes/sessions/` and `trajectory.jsonl` off-peak to extract entity-relation triples. |
| **2.3** | **Knowledge Card Synthesis** | ⏸️ **ON HOLD** | Writes distilled findings to `~/.hermes/knowledge/memories/` for `second_brain.py`. |
| **2.4** | **Systemd Timer Automation** | ⏸️ **ON HOLD** | 03:00 AM user timer with NVML GPU idle safety check (`VRAM < 200 MiB`). |

---

### Track 3: Reasoning & Fact-Checking Upgrades
*Goal: Enhance pre-commit code verification and vector retrieval alignment using Google DeepMind's specialized models.*

| Sequence | Milestone & Scope | Status | Deliverables & Implementation Details | Gate / Verification Criteria |
| :---: | :--- | :---: | :--- | :--- |
| **3.1** | **Gemma-APS Claim Deconstruction in Draft Detective** | ✅ **DONE** | • Integrated Abstractive Proposition Segmentation (APS) into `draft_detective.py`<br>• Decomposes prose into atomic propositions (signatures, defaults, returns, exceptions, classes)<br>• Static AST verification flags contradictory docstring claims before pre-commit | `probe_draft_detective_gemma_aps()` passes in `verify_harness_integrity.py`; `make test-internal` passes with 197/197 tests green. |
| **3.2** | **EmbeddingGemma On-Device Evaluation** | ✅ **DONE** | • Benchmarked `google/embeddinggemma-300m` vs `BAAI/bge-small-en-v1.5` on CPU ONNX<br>• Evaluated code tokenization (Gemma 256k vocab yields 1.69 tokens/sym vs BGE 3.77 tokens/sym; 2.23x fewer subwords)<br>• Integrated `EmbeddingModelProfile` in `hermes_core.embeddings`<br>• Verified 0 MB GPU VRAM bound via `probe_embedding_substrate_evaluation()` in harness | `probe_embedding_substrate_evaluation()` passes; 602/602 contract spikes and 197/197 internal tests green; zero VRAM contention. |

---

### Track 4: Long-Term & Experimental Enhancements
*Goal: Local adapter fine-tuning, self-correction loops, and multimodal vision token optimization.*

| Sequence | Milestone & Scope | Status | Deliverables & Implementation Details | Gate / Verification Criteria |
| :---: | :--- | :---: | :--- | :--- |
| **4.1** | **Cactus Hybrid Uncertainty Detection** | ✅ **DONE** | • Implemented `CactusHybridDetector` in `hermes_core/cactus.py`<br>• Synthesized verbalized linguistic hedging, structural blast-radius risk, and failure streaks<br>• Integrated `STOP_UNCERTAINTY_BREACH` into `LoopController` (`loop_contracts.py`)<br>• Integrated `CLARIFY_OR_HALT` intervention into `supervisory_scan` (`lineage.py`)<br>• Authored `test_cactus_uncertainty.py` & native self-audit probe in harness | Agent halts before destructive mutations when uncertainty >= 0.70 and generates targeted clarifying queries; `probe_cactus_hybrid_uncertainty()` passes; 203/203 unit tests green. |
| **4.2** | **Unsloth On-Device QLoRA Fine-Tuning** | ✅ **DONE** | • Implemented `LoRAAdapterManager` in `hermes_core/lora_adapter.py` with 5 domain adapters<br>• Enforced per-adapter VRAM guard (<150 MiB) and hardware safety ceiling (<= 4,812 MiB)<br>• Single Active Adapter invariant & autonomous intent routing via AST/prompt keywords<br>• Authored detached training harness & GGUF exporter `.hermes/scripts/train_qlora_adapter.py`<br>• Enforced baseline non-regression verification (delta loss <= 0.05) & llama-server payload formatting | `probe_lora_adapter_ecosystem()` passes in harness; 210/210 internal unit tests and 602/602 contract spikes green; GGUF export verified. |
| **4.3** | **Multimodal Vision Token Optimization** | 📋 **PLANNED** | • Calibrate `visual_arbiter.py` using Google's Gemma 4 Vision Token Budget formulas<br>• Dynamic downsampling and patch budgeting to keep image inputs within tight context bounds | Visual inspector turns remain strictly within the allocated token budget without truncating chat history. |

---

## 4. Ecosystem Intelligence & Validation Register

This register benchmarks official Google Gemma and graph ecosystem assets against Hermes Agent OS architecture.

### Actionable Assets
| Asset | Category | Hermes Integration Point | Current Status |
| :--- | :--- | :--- | :---: |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Codebase Graph | Deterministic AST parsing for codebase wikis in `second_brain.py` | ✅ **Completed** (Track 1) |
| [gemma-skills](https://github.com/google-gemma/gemma-skills) | Skills Hub | Drop-in standard skill packages (`gemma-dev` & `gemma-trainer`) in `.hermes/skills/mlops/models/` | ✅ **Active & Verified** (188+ tests passing) |
| [Gemma 4 QAT](https://huggingface.co/collections/google/gemma-4-qat-q4-0) | Core Weights | Official Quantization-Aware Trained 4-bit weights (`Q4_0` / `Q4_K_M`) for base and draft | ✅ **Active in Runtime** |
| [Cognee](https://github.com/topoteretes/cognee) | Memory Graph | Off-peak conversational trajectory dream consolidation sidecar | ⏸️ **On Hold for Future** (Track 2) |
| [EmbeddingGemma](https://huggingface.co/collections/google/embeddinggemma) | Embeddings | Compact 300M embedding model for CPU ONNX retrieval in `opencode_mem.py` | ✅ **Evaluated & Profiled** (Track 3.2) |
| [Gemma-APS](https://huggingface.co/collections/google/gemma-aps-release) | Verification | Abstractive Proposition Segmentation for atomic claim verification in `draft_detective.py` | ✅ **Active in DraftDetective** (Track 3.1) |

---

## 5. Protocol for Updating Plan.md & Ingesting New Discoveries ("Updating More Stuff")

To maintain architectural integrity and prevent roadmap fragmentation, any new tool, research paper, or feature request must pass through the **4-Gate Ingestion Protocol**:

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
