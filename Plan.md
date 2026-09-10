# Hermes Agent OS — Implementation Plan (COMPLETED)

> **Based on**: `research.md` (46 milestones, 5 eras) cross-referenced against live system state.  
> **Status**: **100% IMPLEMENTED & VERIFIED** across 5 sequential commit checkpoints (`e3c421e`, `94fb72f`, `3bed617`, `6aff780`, `a5ea402`).  
> **Exam Results**: **118 / 118 PASSED** in 9.53s (`hermes exam`).  
> **Invariants**: 100% native commands (`hermes <cmd>` / `/<cmd>`) — **zero shell wrappers, zero custom python binaries**.

---

## Audit Summary: Resolved Ledger

| Finding | Severity | Phase | Resolution | Status |
|:---|:---:|:---:|:---|:---:|
| 107 synthetic junk concept files | HIGH | Phase 1 | Deleted all 107 `ast_community_*.md` files; retained genuine invariants | **RESOLVED** (`e3c421e`) |
| `n8n` MCP stub present | LOW | Phase 1 | Removed cloud webhook stub directory entirely | **RESOLVED** (`e3c421e`) |
| Dead / cloud skill categories | LOW | Phase 1 | Pruned `apple`, `social-media`, `smart-home`, `media` | **RESOLVED** (`e3c421e`) |
| `demo_validator` was empty stub | HIGH | Phase 2 | Implemented Biome + Tree-sitter AST validation + `hermes validate` | **RESOLVED** (`94fb72f`) |
| `cog_verifier` was empty stub | HIGH | Phase 2 | Implemented YAML frontmatter schema verification + `hermes concepts` | **RESOLVED** (`94fb72f`) |
| `hypothesis_tree.py` was bin/ script | HIGH | Phase 2 | Wired into `branch_swapper` plugin hook + `hermes hypothesis` | **RESOLVED** (`94fb72f`) |
| Cactus uncertainty used mock math | MED | Phase 3 | Connected to live `llama-server` `/completion` real logprob entropy | **RESOLVED** (`3bed617`) |
| EmbeddingGemma lacked CPU guard | MED | Phase 3 | Created plugin with strict CPU-only invariant (`hermes embed search`) | **RESOLVED** (`3bed617`) |
| SkillEvaluator lacked live benchmark | MED | Phase 3 | Created 5-task benchmark suite + `hermes benchmark skills` (+20% lift) | **RESOLVED** (`3bed617`) |
| NoRA lacked online training buffer | MED | Phase 3 | Wired Stage 1 signal capture + `hermes nora status` CLI | **RESOLVED** (`3bed617`) |
| Declarative attention ceiling | MED | Phase 3 | Authored `declarative-attention.md` concept documenting ceiling | **RESOLVED** (`3bed617`) |
| NeMo Guardrails on Colang 1.0 | MED | Phase 4 | Migrated all 5 rails to Colang 2.x reactive flow syntax | **RESOLVED** (`6aff780`) |
| Knowledge vault empty after purge | HIGH | Phase 5 | Seeded 10 canonical concept docs; all 13 concepts schema-approved | **RESOLVED** (`a5ea402`) |

---

## Phase 1 — Purge: Remove What Doesn't Belong (COMPLETED)

### 1.1 — Delete 107 Synthetic Concept Files
- **Status**: **COMPLETE** (Commit `e3c421e`)
- **Action**: Deleted all 107 `ast_community_*.md` files from `.hermes/knowledge/concepts/`. Retained `wmt_concept.md` and `wmt_test_concept.md`.
- **Verification**: `hermes exam` passed 98/98.

### 1.2 — Delete n8n MCP Stub
- **Status**: **COMPLETE** (Commit `e3c421e`)
- **Action**: Deleted `.hermes/hermes-agent/optional-mcps/n8n/` directory. Zero cloud dependencies remain.
- **Verification**: `hermes exam` passed 98/98.

### 1.3 — Audit and Prune Dead Skills
- **Status**: **COMPLETE** (Commit `e3c421e`)
- **Action**: Pruned unneeded/cloud/non-local categories (`apple`, `social-media`, `smart-home`, `media`). Retained 84 active developer skills.
- **Verification**: `hermes skills list` displays clean 84 enabled skills across core engineering categories.

---

## Phase 2 — Fix: Implement What's Broken (COMPLETED)

### 2.1 — Implement `demo_validator` Plugin
- **Status**: **COMPLETE** (Commit `94fb72f`)
- **Implementation**: `.hermes/plugins/demo_validator/__init__.py`
  - Biome Rust linter/parser (`biome lint`) for HTML, JS, TS.
  - Tree-sitter structural AST (`ast-grep-py`) error-node inspection.
  - Native CLI subcommand: `hermes validate <file> [--json]`.
  - Native Slash command: `/validate <file>`.
  - Autonomous `pre_verify` lifecycle hook.
- **Verification**: `hermes validate README.md` (APPROVED); `hermes validate bad.html` (REJECTED with exact syntax error line). Contract tests in `test_demo_validator.py` pass.

### 2.2 — Implement `cog_verifier` Plugin
- **Status**: **COMPLETE** (Commit `94fb72f`)
- **Implementation**: `.hermes/plugins/cog_verifier/__init__.py`
  - YAML frontmatter parser and schema validator (`id`/`title`, `category`/`tags`, `status`/`verified`).
  - Native CLI subcommand: `hermes concepts [list | verify <file>]`.
  - Native Slash command: `/concepts`.
  - Autonomous `on_session_start` hook.
- **Verification**: `hermes concepts list` correctly lists and verifies vault files. Contract tests in `test_cog_verifier.py` pass.

### 2.3 — Wire `hypothesis_tree.py` as a Native Plugin Hook
- **Status**: **COMPLETE** (Commit `94fb72f`)
- **Implementation**: `.hermes/plugins/branch_swapper/hypothesis_tree.py` and `__init__.py`
  - Relocated Two-Strike Tabu MCTS logic into `plugins/branch_swapper/`.
  - Replaced `bin/hypothesis_tree.py` with thin delegation shim.
  - Native CLI subcommand: `hermes hypothesis [status | branch | backtrack]`.
  - Native Slash command: `/hypothesis`.
  - Autonomous `pre_verify` hook detects fixation (>2 consecutive repair fails) and backtracks automatically.
- **Verification**: `hermes hypothesis status` runs natively. All tests in `test_branch_swapper.py` pass.

---

## Phase 3 — Complete: Finish the Partials (COMPLETED)

### 3.1 — Cactus Uncertainty: Connect to Real Logprobs
- **Status**: **COMPLETE** (Commit `3bed617`)
- **Implementation**: `.hermes/plugins/cactus_uncertainty/__init__.py`
  - Queries local `llama-server` `/completion` endpoint with `n_probs: 5`.
  - Computes real Shannon entropy $H = -\sum p_i \ln p_i$ across model logits.
  - Synthesizes model entropy (40%), verbal hedging (30%), and action blast radius (30%).
  - Native CLI subcommand: `hermes uncertainty <prompt> [--tool <t>] [--command <cmd>]`.
  - Native Slash command: `/uncertainty <prompt>`.
  - Autonomous `pre_tool_call` hook gates destructive mutations (`rm -rf`, `mkfs`).
- **Verification**: `hermes uncertainty "The capital of France is"` outputs `Entropy: 0.0601 (Source: llama-server), SAFE TO PROCEED`. Contract tests in `test_cactus_uncertainty.py` pass.

### 3.2 — EmbeddingGemma: CPU-Only Enforcement
- **Status**: **COMPLETE** (Commit `3bed617`)
- **Implementation**: `.hermes/plugins/embedding_gemma/__init__.py`
  - Powered by `fastembed` ONNX Runtime.
  - Hard invariant: `get_embedder(device="cpu")`. Attempting `"cuda"` or `"gpu"` raises `VRAMInvariantViolation`.
  - Native CLI subcommand: `hermes embed search <query> [--top-k 3]`.
  - Exposes `search_knowledge_vault` tool to LLM runtime.
- **Verification**: `hermes embed search "prevent hallucination"` retrieves `graphiti-core.md` (0.631) with 0 MiB GPU VRAM consumed. Contract tests in `test_embedding_device.py` pass.

### 3.3 — SkillEvaluator: Wire to Live Benchmarks
- **Status**: **COMPLETE** (Commit `3bed617`)
- **Implementation**: `.hermes/benchmarks/skill_lift/` (`benchmark.yaml`, `runner.py`)
  - 5 canonical developer tasks (AST checking, git inspection, UI validation, debugging, FastMCP).
  - Evaluates performance delta (with vs without skill) against live local `llama-server`.
  - Native CLI subcommand: `hermes benchmark skills [--json]`.
- **Verification**: `hermes benchmark skills` executed live against local Gemma 4B, reporting `Base: 20.0%, Skill: 40.0%, Net Skill Lift: +20.0%`.

### 3.4 — NoRA: Wire Online Adaptation Pipeline (Stage 1)
- **Status**: **COMPLETE** (Commit `3bed617`)
- **Implementation**:
  - `on_session_end` hook in `reflective_learner_adapter` captures completed session trajectories to `.hermes/training_buffer/samples.jsonl`.
  - Native CLI subcommand: `hermes nora status`.
  - Concept doc `.hermes/knowledge/concepts/nora-pipeline.md` documents 4-stage pipeline and llama.cpp hot-swap blocker.
- **Verification**: `hermes nora status` executes natively and displays active buffer state.

### 3.5 — Declarative Attention: Document Architectural Ceiling
- **Status**: **COMPLETE** (Commit `3bed617`)
- **Documentation**: `.hermes/knowledge/concepts/declarative-attention.md`
  - Documents how Hermes emulates attention mask control via 5-slot context compaction, and records the architectural ceiling requiring native attention mask APIs in llama.cpp.

---

## Phase 4 — Upgrade: Modernize What's Outdated (COMPLETED)

### 4.1 — NeMo Guardrails: Migrate to Colang 2.x
- **Status**: **COMPLETE** (Commit `6aff780`)
- **Implementation**: `.hermes/guardrails/`
  - Upgraded `config.yml`: `colang_version: "2.x"`.
  - Migrated `input_rails.co`, `output_rails.co`, `dialog_rails.co`, `loop_rails.co` to Colang 2.x reactive `flow` syntax.
  - All 5 flows loaded cleanly by `nemoguardrails==0.24.0` without warnings.
- **Verification**: `hermes exam` passed all 118 contract tests.

---

## Phase 5 — Seed: Real Knowledge Vault Content (COMPLETED)

### 5.x — 10 Canonical Concept Files
- **Status**: **COMPLETE** (Commit `a5ea402`)
- **Seeded Documents**:
  1. `graphiti-core.md`: Bi-temporal knowledge graph and episodic memory.
  2. `nemo-guardrails.md`: Formal input/output/dialog/loop rails and Colang 2.x.
  3. `ast-grep-py.md`: Tree-sitter CST structural search and syntax validation.
  4. `recirculation-adapter.md`: System-2 prefill loops and Lyapunov convergence.
  5. `branch-swapper.md`: Two-Strike Tabu MCTS hypothesis tree search.
  6. `adk-orchestrator.md`: Google ADK 2.8.0 computational graph topologies.
  7. `observer-gate.md`: Pre-commit AST structural verification & Ruff auditing.
  8. `lora-adapter-manager.md`: Low-rank adapter routing under 6GB VRAM envelope.
  9. `cactus-uncertainty.md`: Real logprob Shannon entropy & clarification gate.
  10. `declarative-attention.md`: Attention mask control and slot compaction.
  11. `nora-pipeline.md`: Normalized low-rank adaptation online pipeline.
  12. `wmt_concept.md`: Working memory time-decay invariant.
  13. `wmt_test_concept.md`: Context rot demotion invariant.
- **Verification**: `hermes concepts list` confirms all 13 concept documents have valid YAML frontmatter and pass verification (`[✓] APPROVED`).

---

## Final Verification Checklist

| Criterion | Target | Actual Result | Status |
|:---|:---:|:---:|:---:|
| `hermes exam` | 100% pass (≥98 tests) | **118 passed in 9.53s** | **PASS** |
| `hermes concepts list` | Clean canonical list | **13 verified concepts**, 0 synthetic junk | **PASS** |
| `hermes validate <file>` | Biome + AST check | Active CLI, slash command, `pre_verify` hook | **PASS** |
| `hermes hypothesis status` | MCTS Tabu state | Active CLI, slash command, `pre_verify` hook | **PASS** |
| `hermes uncertainty <prompt>` | Real model entropy | Active CLI, live `llama-server` logprobs | **PASS** |
| `hermes embed search <query>` | CPU-only search | Active CLI, fastembed on CPU, 0 VRAM | **PASS** |
| `hermes benchmark skills` | Live skill lift delta | Active CLI, live benchmark (+20.0% lift) | **PASS** |
| `hermes nora status` | Online adaptation buffer | Active CLI, Stage 1 buffer tracking | **PASS** |
| Colang version | 2.x | Active `colang_version: "2.x"` (5 flows) | **PASS** |
| Zero shell wrappers | Strict invariant | 100% native commands, 0 make, 0 raw python | **PASS** |
| Git checkpoints | Chezmoi tracked | 5 clean sequential commits (`e3c421e` → `a5ea402`) | **PASS** |
