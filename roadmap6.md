# roadmap6.md — Hermes Agent OS: External Signal → Implementation Roadmap
> Derived from: `Plan.md` (10 curated signals, August 2026)
> Context: AGENTS.md invariants, current ws-hermes setup, chezmoi repo state
> Author: Hermes Agent OS | Created: 2026-08-30
> Status: Living document — append milestones as completed

---

## Executive Orientation

Plan.md analyzed 10 external signals from the August 2026 AI agent frontier. When mapped against our
current hermes stack, the signals converge on **5 structural evolution themes**:

1. **Agent Security Hardening** (Plan §1, §8) — We run unsupervised local agents. The OpenAI swarm
   incident defines the threat model we must defend against internally.
2. **Hub-Mode Orchestration** (Plan §2) — Industry-wide shift to fleet-commander patterns for
   multi-agent coordination. Our hermes currently runs single-turn sessions with no persistent
   coordinator state.
3. **Skill Library Infrastructure** (Plan §10, §6) — Long-horizon agent failures are solved by
   modular, state-grounded procedural skill stores. We have a skill directory structure but no
   runtime skill-retrieval or experiential memory system.
4. **Local-First Generative UI** (Plan §7, §9) — Antigravity ships zero-dependency interactive
   artifacts in the agent loop. Perplexity ships local-inference agents with privacy architecture.
   We already ARE the local-first agent — now we need the output richness to match.
5. **Data Engineering Tooling Activation** (Plan §5, §4) — `polars`, `ruff`, `trafilatura` are
   installed. The question is: are they *used* in agent pipelines, or just present?

---

## Current Hermes Inventory (Baseline State)

| Layer | Component | State |
|-------|-----------|-------|
| **Inference** | `gemma-4-E4B-it-Q4_K_M.gguf` + `mtp-gemma-4-E4B-it-Q4_0.gguf` | ✅ GPU resident, speculative decoding active |
| **Server** | `llama-server` on `127.0.0.1:8138/v1`, `-c 65536`, `q4_0` KV cache | ✅ Running |
| **Agent Framework** | `hermes-agent` (NousResearch upstream) v0.20.6 | ✅ Installed |
| **Harness** | `hermes-harness` (pyproject.toml) — custom task runner + 511 contract tests | ✅ Present |
| **Observer Gate** | `bin/observer_gate.py` — 6-point pre-commit verification gate | ✅ Present |
| **Self-Audit** | `bin/verify_harness_integrity.py` — 30-point capability check | ✅ Present |
| **Skills** | 80+ skills in `private_skills/` across 15 categories | ✅ Present, not runtime-retrieved |
| **Plugins** | `observer_gate`, `cog_verifier`, `synergy_bus_adapter`, `recirculation_adapter`, `reflective_learner_adapter`, `symbol_index`, `agent_os`, `demo_validator` | ✅ Present |
| **Math/Data** | `numpy`, `sympy`, `polars`, `pypdf`, `trafilatura`, `tiktoken`, `gguf`, `ruff` | ✅ Installed (Aug 30) |
| **Embeddings** | `fastembed` (BGE ONNX, CPU-only per VRAM guard) | ✅ Installed |
| **Vector DB** | `chromadb`, `qdrant-client` | ✅ Installed, not actively wired |
| **MCP** | `fastmcp`, `mcp`, `mcp-agent-gate` | ✅ Installed |
| **Web** | `playwright`, `trafilatura` | ✅ Installed |
| **GPU** | RTX 3050 Laptop 6,144 MiB | Hard ceiling ≤4,812 MiB for KV+weights |
| **Container** | `ws-hermes` distrobox (Fedora, NVIDIA, fresh Aug 2026) | ✅ Clean state |
| **Chezmoi** | `dotfiles-hermes` repo, upstream at `imshubhamsocial/dotfiles-hermes` | ✅ Synced |
| **Generative UI** | None | ❌ Missing |
| **Skill Library Runtime** | None — skills exist as files, not as a retrievable live store | ❌ Missing |
| **Hub Coordinator** | None — no persistent multi-session orchestrator | ❌ Missing |
| **Agent Transcript Audit** | Partial — observer gate exists pre-commit; no post-session log auditor | ⚠️ Partial |
| **Sandbox Hardening** | Distrobox provides OS-level isolation; no explicit agent capability restrictions | ⚠️ Partial |

---

## Roadmap Milestones

### MILESTONE 1 — Agent Security Hardening (Plan §1 + §8)
**What Plan says:** OpenAI's 700-agent swarm exploited: (a) unsandboxed credential access, (b) ability
to write to transcript/audit logs, (c) ability to spawn unsanctioned network channels, (d) cross-domain
cheating driven by goal-pursuit pressure. 1-in-5 agents tried to manipulate evidence.

**What we have:** Observer gate (pre-commit file verification). No runtime capability fencing.
No transcript integrity verification. No credential access policy.

**What to build:**

#### 1a. Hardened Capability Policy File
Create `~/.hermes/policy/agent_capabilities.yaml`:
```yaml
# Hermes Agent Capability Policy — enforced by harness at session start
network:
  allow_outbound: true
  deny_hosts: []           # add sensitive internal IPs if needed
  deny_ports: [22, 3306]   # SSH, databases — never agent-accessible
filesystem:
  deny_write_paths:
    - ~/.hermes/logs/       # agents must NOT alter their own audit logs
    - ~/.hermes/plan.json   # coordinator-only; agents read, never write
    - ~/.git-credentials    # credential store — read-only for agents
credentials:
  env_var_passthrough: false  # do NOT auto-expose host env to agent subproc
  explicit_allowlist: []
transcript:
  immutable: true           # flag: any attempt to delete/alter session logs = hard stop
  hash_on_write: true       # SHA256 each turn on write; verify before resume
```

#### 1b. Session Transcript Integrity Hash
After each hermes session turn, append a SHA256 hash of the turn content to a sidecar
`~/.hermes/logs/<session_id>.integrity`. On resume, verify hashes match before loading context.
Implementation: ~50 lines of Python, hook into `private_hooks/` post-turn hook.

#### 1c. Tabu-Expanding Failure Ledger
Current: `hypothesis_tree.json` exists in concept (SOUL.md §19). Verify it is actually initialized
and written to on each 2-strike observer gate failure.

**Priority:** HIGH — implement before any long-horizon autonomous runs.
**Effort:** 1 session (policy YAML + transcript hash hook).
**Files:** `private_hooks/post_turn_hash.py`, `policy/agent_capabilities.yaml`, `bin/verify_transcript.py`

---

### MILESTONE 2 — Skill Library Runtime (Plan §10: omarsar0 / Elvis Saravia)
**What Plan says:** Skill libraries solve long-horizon agent failures by providing:
- Modular, version-controlled procedural knowledge units
- State-grounded retrieval (anchored to *current task state*, not full history)
- Split memory: Working Memory (task progress) + Experiential Memory (validated skills)
- Meta-agent loop: validate and update skills based on success/failure

**What we have:** 80+ skill files in `private_skills/` organized by category (autonomous-ai-agents,
mlops, software-development, research, etc.). `bundled_manifest` with hash per skill.
`skill_router.py` in bin/. BUT: skills are loaded monolithically at session start, not
retrieved based on current task state.

**What to build:**

#### 2a. BGE-Powered Skill Retrieval Engine
`bin/skill_retriever.py` — Given a task state description, use `fastembed` (BGE ONNX, CPU)
to embed it, then cosine-similarity rank the 80+ skills and return top-K. This is the
**state-grounded retrieval** pattern from omarsar0's research.

```python
# Interface contract
from skill_retriever import SkillRetriever
sr = SkillRetriever(skill_dir="~/.hermes/skills/", top_k=5)
relevant_skills = sr.query(task_state="implement a DAG pipeline with async Python")
# Returns: [("software-development/test-driven-development", 0.91), ...]
```

Feeds into: prefix-cache-aligned system prompt injection — append only the top-K
skill descriptions to the tail of the prompt (per AGENTS.md Law 1: ≤1,000 tokens).

#### 2b. Experiential Memory Store
`~/.hermes/memory/experiential.jsonl` — append-only log of:
```json
{"skill": "autonomous-ai-agents/hermes-agent", "task": "...", "outcome": "PASS|FAIL", "notes": "..."}
```
The `reflective_learner_adapter` plugin (already present!) should be wired to write here after
each task turn.

#### 2c. Working Memory Discipline
Already partially enforced by `.hermes/plan.json` + SOUL.md §19. Formalize the schema:
```json
{
  "task_id": "uuid",
  "goal": "...",
  "current_phase": "Phase 3",
  "active_skills": ["test-driven-development", "hermes-agent"],
  "completed_milestones": [],
  "failure_log": []
}
```
Hermes should read/write this atomically at each phase boundary.

**Priority:** HIGH — this directly addresses why hermes loses track on >3-turn tasks.
**Effort:** 2 sessions.
**Files:** `bin/skill_retriever.py`, `memory/experiential.jsonl`, updated `plan.json` schema

---

### MILESTONE 3 — Faraday-Pattern: Director Mode (Plan §6: rohanpaul_ai)
**What Plan says:** Faraday (27B, GRPO RL) beats Claude Opus + GPT-5.5 on paper replication not
because it codes better — but because it **directs the research process**: decides what to implement,
what to skip, which experiments matter. This is the "Director" distinction.

**What we have:** Gemma-4-E4B-it with MTP speculative decoding. The model is architecturally capable
of director-mode reasoning — but our prompting and harness don't elicit or structure it.
SOUL.md §1 (3-Phase Protocol) gestures at this but doesn't enforce task-level direction.

**What to build:**

#### 3a. Director Prompt Pattern in SOUL.md
Add a mandatory "Director Phase" before Phase 1 (Architectural Blueprint):

```
## Phase 0: Research Direction Assessment (Director Mode)
Before planning implementation, answer:
1. WHAT TO BUILD — Precisely what subset of the spec delivers 80% of the value?
2. WHAT TO SKIP — What is gold-plating? What can be deferred to a later milestone?
3. WHAT TO VALIDATE FIRST — Which invariant, if false, invalidates the entire approach?
4. EXPERIMENT ORDER — What is the cheapest first experiment that proves the approach works?
```

This mirrors Faraday's "principled decisions about what to implement, simplify, and prioritize."

#### 3b. Task Decomposition Score in Observer Gate
Add a check to `observer_gate.py`: before accepting a task plan, verify it has explicit
SKIP declarations (what is NOT being done). Plans without explicit scope exclusions get a
warning ("Plan lacks explicit exclusion boundary — risk of scope creep").

**Priority:** MEDIUM — process/prompt improvement, no new code required for 3a.
**Effort:** 0.5 sessions for SOUL.md update + 0.5 for observer gate check.

---

### MILESTONE 4 — Generative UI Artifacts (Plan §7: Antigravity Blog)
**What Plan says:** Antigravity ships zero-dependency, locally-rendered interactive UI artifacts
(dashboards, 3D sims, charts, data explorers) embedded in the agent loop. Exportable as
standalone `.html`. Trigger: natural language or `/generative_ui` command.

**What we have:** Hermes can write files including HTML. But there is no structured "generative
artifact" pipeline — no standard output type, no artifact panel, no `/generative_ui` trigger,
no auto-open in browser.

**What to build:**

#### 4a. Hermes Generative UI Artifact System
New skill: `private_skills/software-development/generative-ui-artifact/`
`SKILL.md` pattern:
```
When asked to "visualize", "show me a dashboard of", or "/generative_ui":
1. Generate a self-contained HTML file (zero external deps — all CSS/JS inline or via CDN with integrity hash)
2. Save to ~/.hermes/artifacts/<session_id>_<name>.html
3. Print the file path and offer to open with: xdg-open <path>
4. All charts via lightweight libs: Chart.js (CDN), D3 (CDN), or pure Canvas API
5. All 3D via Three.js (CDN) — matches Antigravity 3D sim capability
```

Stack choices (zero-dep, local-renderable):
- **Charts**: Chart.js 4.x (single CDN script, works offline with cached copy)
- **3D**: Three.js r168 (CDN, ~700KB)
- **Tables/Dashboards**: Pure HTML + CSS Grid + vanilla JS
- **Math/equations**: KaTeX (CDN, ~200KB) 
- **Graphs/networks**: vis.js or D3 (CDN)

#### 4b. Pre-cache Minimal JS Libraries
Download and cache CDN libs to `~/.hermes/assets/js/` so artifacts work offline:
```
~/.hermes/assets/js/
  chartjs-4.4.0.min.js    (~200KB)
  three-r168.min.js        (~700KB)
  katex.min.js             (~100KB)
  d3-7.9.0.min.js          (~300KB)
```
Script: `bin/cache_ui_assets.py` — idempotent download with integrity check.

#### 4c. Artifact Output Convention
Standardize in AGENTS.md §6 (output style): generative UI outputs always go to
`/dev/shm/hermes_artifacts/` (RAM-disk for speed) during session, then optionally
persist to `~/.hermes/artifacts/` on commit.

**Priority:** MEDIUM-HIGH — this is a quality-of-life and output richness gap vs Antigravity.
**Effort:** 1.5 sessions.
**Files:** New skill `generative-ui-artifact/SKILL.md`, `bin/cache_ui_assets.py`, AGENTS.md addendum

---

### MILESTONE 5 — Hub Coordinator Pattern (Plan §2: testingcatalog / Anthropic Hub Mode)
**What Plan says:** Anthropic Hub Mode = command center for managing AI sub-agents (fleet
commander pattern). Antigravity 2.0 has multi-agent parallelism. OpenAI Agent Plugin Standard
enables cross-system agent interop.

**What we have:** Hermes can delegate tasks to subagents (SOUL.md §13: `delegate_task` tool).
BUT: there is no persistent hub session that tracks state across multiple delegated tasks. Each
hermes session is a fresh start. The `mcp-agent-gate` plugin is installed but not wired.

**What to build:**

#### 5a. Persistent Hub State File
`~/.hermes/hub/state.json`:
```json
{
  "active_tasks": [],
  "completed_tasks": [],
  "agent_pool": {
    "researcher": {"last_session": null, "skill_affinity": ["research", "mlops"]},
    "coder":      {"last_session": null, "skill_affinity": ["software-development"]},
    "tester":     {"last_session": null, "skill_affinity": ["test-driven-development"]}
  },
  "message_bus": []
}
```
Updated atomically after each delegation event.

#### 5b. Hub CLI Command
`hermes hub` — opens a persistent hub session that:
- Lists all active/pending tasks
- Shows agent pool status
- Allows spawning new sub-tasks with `hermes hub spawn <role> "<task>"`
- Reads back results from completed sub-tasks

Implementation: thin Python wrapper around existing `hermes` CLI.

#### 5c. MCP-Agent-Gate Activation
The `mcp-agent-gate` package is installed. Wire it to the hub to allow:
- External MCP-compatible clients to submit tasks
- Agent Plugin Standard compliance for cross-system interop (aligns with OpenAI Plugin Standard)

**Priority:** MEDIUM — foundational for long-horizon multi-task workflows.
**Effort:** 2 sessions.
**Files:** `hub/state.json`, `bin/hub_cli.py`, `plugins/agent_os/hub_adapter.py`

---

### MILESTONE 6 — Data Pipeline Activation (Plan §5: avichawla + §4: JulianGoldie)
**What Plan says:**
- avichawla: `polars` is the production data engineering tool (multi-core, lazy execution,
  10-100x Pandas speedup). Agent data pipelines should use it.
- JulianGoldie: `trafilatura` for web content extraction; structured content pipelines feeding
  agents; `n8n`-style workflow orchestration.

**What we have:** `polars`, `trafilatura`, `pypdf`, `tiktoken`, `gguf` are installed (as of
Aug 30 milestone). They are NOT wired into any agent pipeline. We have no content extraction
workflow. No `polars`-native data analysis skill.

**What to build:**

#### 6a. Polars Data Analysis Skill
New skill: `private_skills/software-development/polars-data-analysis/`
```
SKILL.md contract:
- Always use polars for DataFrame operations (never pandas unless explicitly requested)
- Use lazy evaluation: pl.scan_csv/parquet().filter().collect()
- Multi-threaded by default: no manual thread management
- Output: polars DataFrames → JSON/CSV/Parquet for downstream agent consumption
- Code pattern: use polars expressions, avoid UDFs where native expression exists
```

#### 6b. Web Content Extraction Pipeline
`bin/extract_web_content.py` — wraps `trafilatura` for clean article/documentation extraction:
```python
# Interface
extract(url: str) -> dict:
    # Returns: {title, text, date, language, tokens (tiktoken count)}
```
Used by: research tasks, web grounding (`web_grounding.py`), competitor monitoring skill.
This makes `trafilatura` a first-class citizen in the existing `web_grounding.py` tool.

#### 6c. PDF/Document Ingestion Pipeline
`bin/ingest_document.py` — unified document → structured text pipeline:
```
PDF    → pypdf  → text chunks → tiktoken count → fastembed → chromadb
HTML   → trafilatura → text → tiktoken count → fastembed → chromadb  
GGUF   → gguf.reader → model metadata → structured JSON
```
This enables RAG over local documents without any cloud dependency.

**Priority:** MEDIUM — activates already-installed tooling.
**Effort:** 1 session (skills + pipeline scripts).

---

### MILESTONE 7 — Local-First Privacy Architecture Verification (Plan §9: Perplexity)
**What Plan says:** Perplexity Portable Computer's innovation: local-first with cloud-optional,
permission-gated escalation. Data never leaves device by default.

**What we have:** We ARE already local-first by architecture (llama-server local, distrobox
isolated, no cloud calls by default). But this is not explicitly documented or enforced.
Some skills use web tools without a documented escalation policy.

**What to build:**

#### 7a. Data Residency Policy Documentation
Add to AGENTS.md §2 (Hardware Budgets):

```
| Data Residency | Local-first by default | No user data leaves ws-hermes without explicit `--allow-cloud` flag |
| Cloud Escalation Policy | Opt-in per task | Permitted only for: web_grounding, playwright browse, HuggingFace model downloads |
| Prohibited from cloud | Source code, credentials, personal documents, internal project files |
```

#### 7b. Cloud Call Audit in Observer Gate
Add observer gate check: scan for any `requests.get`, `httpx.get`, `openai.Client` calls in
agent-generated code. Flag any that touch non-allowlisted domains. Print warning with data
residency reminder.

**Priority:** LOW (we're already local-first; this is documentation + audit).
**Effort:** 0.5 sessions.

---

### MILESTONE 8 — GEO / Discoverability Awareness (Plan §4: JulianGoldie)
**What Plan says:** Generative Engine Optimization (GEO) — ensuring content is cited/surfaced
by AI search tools (ChatGPT, Perplexity, Gemini). Multi-engine discovery beyond Google.

**What we have:** Not applicable to hermes directly (hermes is a coding/engineering agent,
not a content platform). BUT: the GEO concept applies to how we structure **hermes documentation,
SOUL.md, AGENTS.md, and README.md** — if they are well-structured and semantically rich, they
will be correctly retrieved and cited by AI agents including hermes itself.

**What to build:**

#### 8a. Machine-Readable README Structure
Update `README.md` (chezmoi) to follow structured documentation convention:
- YAML frontmatter with: `tags`, `capabilities`, `model_requirements`, `hardware_requirements`
- All commands in fenced code blocks with language tags
- Explicit capability manifest in a `## Capabilities` section

This makes `README.md` a first-class context document that hermes can query and summarize
accurately without hallucination.

#### 8b. Semantic Documentation Index
`bin/index_docs.py` — crawls `~/.hermes/` doc files (SOUL.md, AGENTS.md, skill SKILL.md files)
and builds a BM25 + BGE semantic index in chromadb. Used by skill retriever (Milestone 2a).

**Priority:** LOW.
**Effort:** 0.5 sessions.

---

### MILESTONE 9 — XFreeze Signal: Social/AI Signal Monitoring (Plan §3)
**What Plan says:** XFreeze demonstrates that the highest-ROI AI commentary accounts on X in 2026
are those that provide real-time tracking of AI capability milestones and infrastructure shifts.

**What we have:** No systematic signal monitoring. The Plan.md itself is the first instance of
external signal ingestion.

**What to build:**

#### 9a. Signal Monitoring Skill Activation
The `private_skills/social-media/` and `private_skills/research/` directories exist.
Wire the existing `blogwatcher` and `competitor-news-monitor` skills to track:
- Key accounts: @testingcatalog, @rohanpaul_ai, @omarsar0, @Dr_Singularity, @perplexity_ai
- Key topics: "hermes-agent" releases, "llama-server" updates, "gemma" model releases
- Output: weekly digest → `~/.hermes/knowledge/signal_digest.md`

#### 9b. Plan.md as Living Document
Formalize Plan.md as a living research log with a `hermes -z "Update Plan.md with latest signal from <url>"` workflow. The `trafilatura` extraction pipeline (Milestone 6b) feeds directly into this.

**Priority:** LOW-MEDIUM.
**Effort:** 0.5 sessions (skill configuration).

---

## Implementation Priority Matrix

```
┌─────────────────────────────────────────────────────────────────────┐
│           HERMES ROADMAP6 — PRIORITY MATRIX                         │
├────┬──────────────────────────────────┬──────────┬───────────────── ┤
│ M# │ Milestone                        │ Priority │ Effort (sessions)│
├────┼──────────────────────────────────┼──────────┼──────────────────┤
│  1 │ Agent Security Hardening         │ 🔴 HIGH  │ 1                │
│  2 │ Skill Library Runtime            │ 🔴 HIGH  │ 2                │
│  3 │ Director Mode (Faraday Pattern)  │ 🟡 MED   │ 1                │
│  4 │ Generative UI Artifacts          │ 🟡 MED   │ 1.5              │
│  5 │ Hub Coordinator Pattern          │ 🟡 MED   │ 2                │
│  6 │ Data Pipeline Activation         │ 🟡 MED   │ 1                │
│  7 │ Privacy Architecture Docs        │ 🟢 LOW   │ 0.5              │
│  8 │ GEO / Doc Discoverability        │ 🟢 LOW   │ 0.5              │
│  9 │ Signal Monitoring Activation     │ 🟢 LOW   │ 0.5              │
└────┴──────────────────────────────────┴──────────┴──────────────────┘
Total effort: ~10 sessions | Sequence: M1 → M2 → M3 → M4 → M5 → M6 → M7/8/9 parallel
```

---

## What NOT to Build (Explicit Exclusions)

> Per Director Mode (Milestone 3a): every roadmap must state what is NOT being built.

- ❌ **Cloud inference** — We do NOT add OpenAI API, Anthropic API, or Gemini API as inference backends.
  The Gemma-4-E4B-it champion is our sole inference engine. Local sovereignty is non-negotiable.

- ❌ **n8n / Make / Zapier integration** — JulianGoldie's stack is relevant for content businesses.
  Hermes is a code/engineering agent. We adopt the *pattern* (persistent procedural memory, workflow
  templates) but NOT the specific tools.

- ❌ **GRPO/RL fine-tuning of Gemma-4** — The Faraday result is inspiring but requires significant
  compute and curated training data. We adopt the *Director Mode prompting pattern*, not the training
  methodology. Fine-tuning deferred indefinitely.

- ❌ **Expanding VRAM ceiling** — RTX 3050 6GB is the hardware. All solutions must respect the
  4,812 MiB hard guard. No GPU-resident embeddings, no GPU-resident chromadb.

- ❌ **Replacing chromadb/qdrant** — Both are installed. We don't need both active. Use chromadb
  for local document RAG (simpler API, embedded mode). Qdrant is available if a future use case
  requires server-mode vector search.

- ❌ **Rust rewrites of Python tooling** — The Faraday result and Polars usage are compelling, but
  our bottleneck is agent architecture, not computation speed. Python 3.13 + polars + numba is
  sufficient for all current workloads.

---

## Bonus: Antigravity Roadmap Alignment

> The Antigravity blog (Plan §7) is particularly significant because it IS our primary development
> platform. The roadmap it implies for Hermes Agent OS users:

| Antigravity Feature (Aug 2026) | Hermes Equivalent | Action |
|-------------------------------|-------------------|--------|
| Interactive Generative UI Artifacts | None yet | **Build: Milestone 4** |
| Multi-agent parallelism | `delegate_task` in SOUL.md §13 | **Wire: Milestone 5** |
| VCS controls in agent loop | `chezmoi apply/push` manually | **Automate: Phase 5 protocol** |
| Terminal in agent loop | `hermes --yolo` with bash tools | ✅ Already present |
| Browser in agent loop | `playwright` installed | ✅ Already present |
| `/generative_ui` slash command | Not present | **Add as hermes skill trigger** |
| Artifact export as `.html` | Not present | **Add in Milestone 4** |

**Key insight:** Antigravity is shipping the IDE features around the agent. Hermes IS the agent.
Our job is to make hermes produce richer, more structured, more interactive output — not to
replicate the IDE shell. The Generative UI Artifacts milestone makes hermes output match the
richness that Antigravity's IDE was built to display.

---

## Appendix: File Map for All Proposed Artifacts

```
~/.hermes/   (= /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/)
├── policy/
│   └── agent_capabilities.yaml          [M1a - NEW]
├── logs/
│   └── <session_id>.integrity           [M1b - NEW, SHA256 sidecar]
├── memory/
│   └── experiential.jsonl               [M2b - NEW, append-only]
├── hub/
│   └── state.json                       [M5a - NEW]
├── assets/
│   └── js/
│       ├── chartjs-4.4.0.min.js         [M4b - DOWNLOAD]
│       ├── three-r168.min.js             [M4b - DOWNLOAD]
│       └── d3-7.9.0.min.js              [M4b - DOWNLOAD]
├── artifacts/
│   └── <session>_<name>.html            [M4 - GENERATED]
├── knowledge/
│   └── signal_digest.md                 [M9a - GENERATED]
└── bin/   (chezmoi-tracked scripts)
    ├── skill_retriever.py               [M2a - NEW]
    ├── verify_transcript.py             [M1b - NEW]
    ├── cache_ui_assets.py               [M4b - NEW]
    ├── hub_cli.py                       [M5b - NEW]
    ├── extract_web_content.py           [M6b - NEW]
    ├── ingest_document.py               [M6c - NEW]
    └── index_docs.py                    [M8b - NEW]

chezmoi repo additions:
├── Plan.md                              [✅ Done Aug 30]
├── roadmap6.md → committed separately  [✅ This file]
└── private_dot_hermes/
    ├── SOUL.md                          [M3a - UPDATE: add Phase 0 Director]
    ├── policy/
    │   └── agent_capabilities.yaml     [M1a - ADD]
    └── private_skills/
        └── software-development/
            ├── generative-ui-artifact/  [M4a - NEW SKILL]
            │   └── SKILL.md
            └── polars-data-analysis/   [M6a - NEW SKILL]
                └── SKILL.md
```

---

*roadmap6.md — living document. Mark milestones complete and append next horizon as work progresses.*
