# Hermes Agent OS — Implementation Plan

> **Based on**: `research.md` (46 milestones, 5 eras) cross-referenced against live system state.  
> **Written**: 2026-09-10  
> **Invariants**: All developer commands use native `hermes <cmd>` subcommands or `/cmd` slash commands only — **zero raw python, zero make, zero shell wrappers**.

---

## Audit Summary: What We Have vs What We Should Have

### System State (as of this writing)
- **16 plugins active** in `config.yaml`: all registered correctly.
- **107 synthetic junk files** in `.hermes/knowledge/concepts/` — all `ast_community_*.md`.
- **`demo_validator` plugin**: stub — `register()` is a no-op `pass`.
- **`cog_verifier` plugin**: stub — `register()` is a no-op `pass`.
- **No `lora_adapter` plugin** in `.hermes/plugins/` — only a test file exists.
- **No `cactus_uncertainty` plugin** in `.hermes/plugins/` — only a test file exists.
- **No `embedding_gemma` plugin** in `.hermes/plugins/`.
- **`hypothesis_tree.py` in `bin/`** — standalone script writing to `/dev/shm/`, not wired as a native Hermes hook.
- **`biome`** is installed at `~/.local/bin/biome` but **not wired** into `demo_validator`.
- **NeMo Guardrails `colang_version: "1.0"`** — `nemoguardrails==0.24.0` supports Colang 2.0.
- **`n8n` MCP stub** present in `optional-mcps/` — discard artifact.
- **`skills/`** has 16 category folders — content untested, no usage monitoring.
- **NoRA** is documentation only — no online training pipeline wired.

### Critical Findings
| Finding | Severity | Impact |
|:--------|:--------:|:-------|
| `demo_validator` is an empty stub | HIGH | HTML artifacts go unvalidated — violates Finish-First |
| `cog_verifier` is an empty stub | HIGH | Knowledge vault has no verification gate |
| 107 synthetic junk concept files | HIGH | Corrupts COG second brain; pollutes semantic search |
| `hypothesis_tree.py` is a standalone bin/ script | HIGH | Two-Strike Tabu not hooked into agent lifecycle |
| Cactus uncertainty uses mock entropy | MED | Clarification gate fires on fake math, not real logits |
| EmbeddingGemma has no CPU-only enforcement | MED | Risk of VRAM thrashing alongside Gemma 4B |
| NoRA has no training pipeline | MED | Weight normalization is theory-only |
| NeMo Guardrails still on Colang 1.0 | MED | Missing Colang 2.0 `execution_rails` |
| `n8n` MCP stub still present | LOW | Dead code; cloud dependency violation |
| Skills folder untested, unmonitored | LOW | Unknown dead skills consuming context budget |

---

## Phase 1 — Purge: Remove What Doesn't Belong

**Goal**: Clean dead weight from the system. No new code until the graveyard is cleared.

### 1.1 — Delete 107 Synthetic Concept Files

**Problem**: `research.md` item #5 — we generated 107 `ast_community_*.md` synthetic mock files with zero real content. They pollute the knowledge vault and corrupt any semantic search over `.hermes/knowledge/concepts/`.

**Action**:
- Delete all 107 `ast_community_*.md` files from `.hermes/knowledge/concepts/`.
- Retain any non-synthetic real concept documents (if any exist alongside them).
- Verify: `hermes exam` must still pass 98/98 after deletion.

**Verification**: `hermes exam` → 98/98 PASSED

---

### 1.2 — Delete n8n MCP Stub

**Problem**: `research.md` item #17 — n8n is a cloud webhook automation stack. Its MCP manifest at `.hermes/hermes-agent/optional-mcps/n8n/` is dead code that references cloud endpoints, violating the local-first mandate.

**Action**:
- Remove `.hermes/hermes-agent/optional-mcps/n8n/` directory entirely.

**Verification**: `hermes exam` → 98/98 PASSED

---

### 1.3 — Audit and Prune Dead Skills

**Problem**: `research.md` item #23 — 16 skill category folders exist with unknown content. Skills like `social-media`, `mlops`, `apple`, `note-taking` have unknown/unmonitored content. No usage tracking exists.

**Action**:
- Inspect each category in `.hermes/skills/`.
- Remove skill categories that are: (a) cloud-dependent, (b) social-media related, (c) have zero invocations.
- Keep: `software-development`, `engineering`, `research`, `devops`, `github`.
- Discard candidates: `social-media`, `apple` (Apple-specific), `smart-home`, `media`, `creative` (unless content is verifiable and local).
- After pruning, register a `hermes skills list` subcommand via `openskills` plugin to enumerate active skills by category.

**Verification**: `hermes exam` → 98/98 PASSED

---

## Phase 2 — Fix: Implement What's Broken (Stubs → Real Plugins)

### 2.1 — Implement `demo_validator` Plugin

**Problem**: `research.md` item #20 — `demo_validator` is a complete stub (`register()` → `pass`). HTML artifacts from the generative UI system go unvalidated. This violates the Finish-First invariant.

**What We Missed**: Used naive character-counter regexes in the original implementation. Now we have `biome` at `~/.local/bin/biome` — a Rust-based JS/TS/HTML formatter/linter — and `ast-grep-py` for Tree-sitter HTML AST parsing.

**Action**:
- Implement `demo_validator/__init__.py`:
  - `validate_html(html_str: str) -> dict` — uses `biome check --stdin-filepath=artifact.html` for structural validation.
  - `validate_js(js_str: str) -> dict` — uses `biome check --stdin-filepath=artifact.js`.
  - Register `hermes validate <file>` CLI subcommand.
  - Register `/validate <file>` slash command.
  - Register `pre_verify` hook: auto-validate any `.html`/`.js` artifact modified during a turn before completion.
- Use `biome` via `subprocess` (it's a native binary at `~/.local/bin/biome`) — NOT as a wrapper/script; `demo_validator` is the native Hermes integration layer.

**Verification**: `hermes validate <demo_file.html>` → `APPROVED ✓` or `REJECTED ✗` with specific error lines.

---

### 2.2 — Implement `cog_verifier` Plugin

**Problem**: `research.md` item #5 — `cog_verifier` is a complete stub. The knowledge vault at `.hermes/knowledge/concepts/` has no verification gate — any markdown file (including synthetic junk) passes through unquestioned.

**What We Missed**: COG verifier should enforce YAML frontmatter schema on each concept file: required fields `title`, `tags`, `source`, `era`, `status`.

**Action**:
- Implement `cog_verifier/__init__.py`:
  - `verify_concept(path: str) -> dict` — parses YAML frontmatter, checks required fields, validates `status` is one of `[active, partial, deprecated]`.
  - `list_concepts() -> list[dict]` — returns all valid concept files with their metadata.
  - Register `hermes concepts list` CLI subcommand.
  - Register `hermes concepts verify <file>` CLI subcommand.
  - Register `/concepts` slash command → calls `list_concepts()`.
  - Register `on_session_start` hook: scans `.hermes/knowledge/concepts/` on boot, reports count and any schema violations to context.
- After Phase 1.1 (junk deletion), seed 5–10 real concept files with correct frontmatter covering: `graphiti-core`, `NeMo-guardrails`, `ast-grep-py`, `recirculation-adapter`, `branch-swapper`.

**Verification**: `hermes concepts list` → shows real concept files. `hermes concepts verify <file>` → validates schema.

---

### 2.3 — Wire `hypothesis_tree.py` as a Native Plugin Hook

**Problem**: `research.md` item #19 — `hypothesis_tree.py` is a standalone bin/ script writing to `/dev/shm/hypothesis_tree.json`. It must be manually invoked. This directly violates the Zero-Wrapper mandate.

**What We Missed**: `hypothesis_tree.py` has the full Two-Strike Tabu MCTS implementation — it just isn't registered as a Hermes hook.

**Action**:
- Extend `branch_swapper/__init__.py` to import `hypothesis_tree` logic directly:
  - The plugin imports `HypothesisNode`, `HypothesisTree` from the existing `bin/hypothesis_tree.py` (move module to `plugins/branch_swapper/hypothesis_tree.py`).
  - Register `pre_verify` hook: on each turn, if a test fails, call `HypothesisTree.record_failure(branch_id, error)` and automatically backtrack.
  - Register `hermes hypothesis status` CLI subcommand → shows current tree state from `/dev/shm/hypothesis_tree.json`.
  - Register `/hypothesis` slash command → dumps active DAG.
- Remove `bin/hypothesis_tree.py` after logic is moved to plugin (no orphan bin/ logic).

**Verification**: `hermes hypothesis status` → shows tree. After a failing test, automatic backtrack is triggered via hook without manual invocation.

---

## Phase 3 — Complete: Finish the Partials

### 3.1 — Cactus Uncertainty: Connect to Real Logprobs

**Problem**: `research.md` item #29 — `test_cactus_uncertainty.py` uses synthetic mock entropy math (hardcoded floats). The clarification gate fires based on fake entropy values rather than real logit distributions from `llama-server`.

**What We Missed**: `llama-server` at `http://127.0.0.1:8138` exposes `/completion` with `logprobs: true` parameter. Real token-level probability distributions are available.

**Action**:
- Create `.hermes/plugins/cactus_uncertainty/__init__.py`:
  - `extract_logprobs(prompt: str, n_tokens: int = 5) -> list[dict]` — calls `POST /completion` with `{"logprobs": 5, "n_predict": 1}`, extracts top-k token probabilities.
  - `compute_entropy(logprobs: list[float]) -> float` — real Shannon entropy from actual logit values.
  - `should_clarify(entropy: float, threshold: float = 1.8) -> bool` — threshold calibrated to real model output.
  - Register `pre_tool_call` hook: before any high-consequence mutation tool (write_file, run_command with mutations), call `should_clarify()` on the pending action plan.
  - Register `hermes uncertainty <prompt>` CLI subcommand.
  - Register `/uncertainty <prompt>` slash command.
- Update `test_cactus_uncertainty.py` to call the real endpoint (skip if server not running).

**Verification**: `hermes uncertainty "delete all logs"` → entropy above threshold → prints `CLARIFY BEFORE PROCEEDING`.

---

### 3.2 — EmbeddingGemma: CPU-Only Enforcement

**Problem**: `research.md` item #28 — the embedding model risks being loaded onto GPU VRAM simultaneously with Gemma 4B (6GB card). This causes VRAM thrashing and OOM.

**What We Missed**: No explicit CPU-device pinning is configured. The embedding profile exists but has no hard device constraint.

**Action**:
- Create `.hermes/plugins/embedding_gemma/__init__.py`:
  - `get_embedder() -> SentenceTransformer` — explicitly sets `device="cpu"` in the constructor; never GPU.
  - `embed(texts: list[str]) -> list[list[float]]` — returns normalized dense vectors.
  - `semantic_search(query: str, corpus: list[str], top_k: int = 5) -> list[tuple]` — cosine similarity search.
  - Register as an LLM-callable tool: `semantic_search` exposed via `ctx.register_tool`.
  - Config: add `embedding_gemma.device: cpu` to `config.yaml` with a guard that raises if `cuda` is set.
- Write a contract test: `test_embedding_device.py` — asserts `get_embedder().device == "cpu"`.

**Verification**: `hermes exam` → test_embedding_device passes. VRAM usage unchanged when embedding is used.

---

### 3.3 — SkillEvaluator: Wire to Live Benchmarks

**Problem**: `research.md` item #7 — the SkillEvaluator harness in `test_quorum_and_gepa.py` runs against static synthetic prompts hardcoded in the test file. No live task benchmark exists.

**What We Missed**: A real benchmark should probe the live `llama-server` with before/after skill injection and measure delta task completion.

**Action**:
- Create `.hermes/benchmarks/skill_lift/` directory with:
  - `benchmark.yaml` — define 10 canonical task prompts (coding tasks, debugging, refactoring) that represent real developer workflows.
  - `runner.py` (called only via plugin, never directly) — imports `hermes_cli` API, runs each benchmark prompt with skill disabled then enabled, records token delta, latency, correctness score.
- Register `hermes benchmark skills` CLI subcommand → runs the live benchmark suite.
- Update `gepa_optimizer` plugin to consume benchmark results to auto-optimize GEPA prompts.

**Verification**: `hermes benchmark skills` → outputs delta table showing skill lift per skill.

---

### 3.4 — NoRA: Wire Online Adaptation Pipeline (Stage 1)

**Problem**: `research.md` item #38 — NoRA (Normalized Low-Rank Adaptation) is documented in test files and mathematical comments but has no running pipeline. Weight updates don't flow from verified task outcomes back into the model.

**What We Missed**: An online adaptation loop requires: (1) a training signal from verified outcomes, (2) weight update via LoRA, (3) hot-swap of adapter in `llama-server`.

**Action** (Stage 1 — Signal Capture only; Stages 2–4 blocked on llama.cpp API):
- `reflective_learner_adapter` `on_session_end` hook: capture task outcome (pass/fail) + skill trace → write to `~/.hermes/training_buffer/` as JSONL.
- Register `hermes nora status` CLI subcommand → shows buffer size, pending updates, and last verified outcome.
- Create `.hermes/knowledge/concepts/nora-pipeline.md` — documents all 4 stages and the Stage 2–4 blocker (llama.cpp lacks public LoRA hot-swap API).

**Verification**: `hermes nora status` → shows training buffer state after a session ends.

---

### 3.5 — Declarative Attention: Document the Ceiling

**Problem**: `research.md` item #36 — the context compactor emulates attention mask control via prompt trimming. Real attention mask editing requires PyTorch/vLLM internal hooks that llama.cpp doesn't expose.

**Action**:
- Create `.hermes/knowledge/concepts/declarative-attention.md` with YAML frontmatter `status: partial`.
- Content: "True attention mask editing requires vLLM or PyTorch model access. Current implementation uses context compaction (slot pruning) as an approximation via `recirculation_adapter`. This is an architectural ceiling until llama.cpp exposes internal layer attention APIs."
- Add a note in `SOUL.md` system capabilities section.

**Verification**: `hermes concepts verify declarative-attention.md` → schema valid.

---

## Phase 4 — Upgrade: Modernize What's Outdated

### 4.1 — NeMo Guardrails: Migrate to Colang 2.0

**Problem**: `research.md` item #45 — `nemoguardrails==0.24.0` supports Colang 2.0 with `execution_rails` (event-driven reactive flows), but `guardrails/config.yml` is pinned to `colang_version: "1.0"`.

**What We Gain**: Colang 2.0 introduces `flow` definitions, `activate` statements, and event-driven rail triggers — significantly more expressive than Colang 1.0 pattern matching.

**Action**:
- Read NeMo Guardrails 0.24.0 migration guide for Colang 2.0 syntax differences.
- Migrate `.hermes/guardrails/`:
  - `config.yml`: change `colang_version: "1.0"` → `colang_version: "2.x"`.
  - `input_rails.co` → rewrite blocked patterns using Colang 2.0 `flow` syntax.
  - `dialog_rails.co` → rewrite role checks using Colang 2.0 `activation` patterns.
  - `output_rails.co` → migrate secret redaction patterns.
  - `loop_rails.co` → rewrite loop ceiling using Colang 2.0 event triggers.
- Run full contract test suite after migration: `hermes exam` → 98/98 PASSED.
- Update `nemo_guardrails/__init__.py` `HermesGuardrailsEngine` if method signatures changed in 0.24.0.

**Verification**: `hermes exam` → 98/98 PASSED with Colang 2.0 active.

---

## Phase 5 — Seed: Real Knowledge Vault Content

**Problem**: After deleting 107 synthetic junk files (Phase 1.1), the knowledge vault will be empty. It needs real, high-signal concept documents representing the actual research ingested into Hermes.

**Action**:
- Create 10 canonical concept files with correct YAML frontmatter (`title`, `tags`, `source`, `era`, `status`):

| File | Concept |
|:-----|:--------|
| `graphiti-core.md` | Temporal knowledge graph and episodic memory |
| `nemo-guardrails.md` | Colang rail system for input/dialog/output/loop safety |
| `ast-grep-py.md` | Tree-sitter structural AST search and syntax validation |
| `recirculation-adapter.md` | System-2 prefill loops and Lyapunov convergence proxy |
| `branch-swapper.md` | Two-Strike Tabu MCTS hypothesis tree and rollback |
| `adk-orchestrator.md` | Google ADK 2.8.0 SequentialAgent/LoopAgent/RouterAgent topologies |
| `observer-gate.md` | Pre-verify ruff + ast-grep-py audit gate |
| `lora-adapter-manager.md` | Dynamic LoRA hot-swap under 6GB VRAM envelope |
| `cactus-uncertainty.md` | Real logprob entropy gate for clarification triggering |
| `declarative-attention.md` | Context compaction ceiling + true attention mask blocker |

- Each file must pass `hermes concepts verify <file>`.

**Verification**: `hermes concepts list` → 10 entries, all schema-valid.

---

## Completion Criteria

All phases are done when:

1. `hermes exam` → **98/98 PASSED** (or higher, if new tests are added).
2. `hermes concepts list` → shows **10 real concept files**, zero `ast_community_*` entries.
3. `hermes validate <html_file>` → returns APPROVED/REJECTED (not stub).
4. `hermes concepts verify <file>` → validates frontmatter schema (not stub).
5. `hermes hypothesis status` → shows live hypothesis tree (not bin/ script).
6. `hermes uncertainty "..."` → uses real llama-server logprobs (not mock math).
7. `hermes benchmark skills` → outputs real skill lift delta table.
8. `hermes nora status` → shows training buffer state.
9. `hermes exam` → Colang 2.0 rails active, all safety tests passing.
10. `.hermes/hermes-agent/optional-mcps/n8n/` → deleted.

---

## Execution Order

```
Phase 1 (Purge)           Phase 2 (Fix Stubs)          Phase 3 (Complete Partials)
  1.1 Delete junk    →      2.1 demo_validator     →      3.1 Cactus live logprobs
  1.2 Remove n8n            2.2 cog_verifier               3.2 EmbeddingGemma CPU-only
  1.3 Prune skills          2.3 hypothesis_tree hook        3.3 SkillEvaluator benchmarks
                                                             3.4 NoRA pipeline Stage 1
                                                             3.5 Document attention ceiling

Phase 4 (Upgrade)         Phase 5 (Seed Content)
  4.1 Colang 2.0     →      5.x 10 real concept files
```

> **Rule**: Never proceed to the next phase item until `hermes exam` passes after the current item. The Finish-First invariant applies to the Plan itself.
