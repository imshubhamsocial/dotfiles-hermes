# Plan.md — Master Iterative Realignment & Autonomous RSI Execution Plan

> **Project**: Hermes Agent OS  
> **Target Platform**: Fedora Distrobox (`ws-hermes`), NVIDIA RTX 3050 Laptop GPU (6,144 MiB VRAM, 4,812 MiB Cap)  
> **Active Engine**: `NullpoLab/gemma-4-E4B-it-Heretic-ARA-Refusals6-attn` on Port 8138 (50.96 tok/s, MTP draft)  
> **Upstream Authority**: Pristine [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) v0.21.2 tracking `main`

> [!IMPORTANT]
> **Non-Negotiable End-State Principle**: After every phase in this plan is complete, Hermes must operate **entirely through its own native mechanisms** — upstream plugins, `config.yaml` keys, PyPI packages, and `hermes config set` commands. Zero bespoke Python scripts, zero synthetic JSON policies, zero stub files. If something cannot be activated via an upstream Hermes extension point (plugin, MCP, skill, cron, `config.yaml`), it is not implemented. This plan is designed so that after full execution, everything runs automatically without requiring hand-crafted prompts or manual tool invocations.

---

## Master Status Dashboard

```
========================================================================================================================
HERMES AGENT OS: UNIFIED ITERATIVE REALIGNMENT & RESEARCH ROADMAP
========================================================================================================================
Iteration / Phase       Focus Area                                 Key Artifacts / Verification            Status
------------------------------------------------------------------------------------------------------------------------
ITERATION 0: .HERMES BESPOKE SYNTHETIC DEBT PURGE
  Step 0.1              Purge synthetic scripts & specs            rm bin/capability_dashboard.py etc.    ✅ DONE
  Step 0.2              Purge synthetic rules & JSON configs       rm rules/evolved_harness_*.json etc.   ✅ DONE
  Step 0.3              Purge stub adapter & broken cron .sh files rm adapters/*.gguf, cron/*.sh files    ✅ DONE
  Step 0.4              Fix daily_health_check cron (hermes doctor) Rewrote .sh → hermes doctor + VRAM    ✅ DONE
  Step 0.5              Chezmoi sync & verify hermes doctor        chezmoi status clean, doctor exits 0   ✅ DONE
------------------------------------------------------------------------------------------------------------------------
ITERATION 1: CLEAN ARCHITECTURE REALIGNMENT
  Step 1.1              Model Weight Relocation & Chezmoi           ~/.cache/models/, dotfiles clean       ✅ DONE
  Step 1.2              Upstream hermes-agent Git Purity            Purged 92 mock classes in agent/core  ✅ DONE
  Step 1.3              Workspace Debt Purge                        Purged 20 synthetic contract tests     ✅ DONE
  Step 1.4              Unified Makefile & Canonical Packages       Makefile, pyproject.toml clean         ✅ DONE
  Step 1.5              Chezmoi Git Dotfiles Synchronization        private_dot_hermes clean text repo     ✅ DONE
------------------------------------------------------------------------------------------------------------------------
ITERATION 2: FOUNDATIONAL COGNITIVE HARNESS (PHASES 1–4)
  Phase 1               Hardware & Inference Parity                 Port 8138, MTP draft, 4,851 MiB VRAM  ✅ DONE
  Phase 2               Cognitive Scaffolding & AST Surgery         tests/phase2_autonomous_eval/ exit 0   ✅ DONE
  Phase 3               Autonomous Outer Loop & Web Grounding       tests/phase3_autonomous_eval/ exit 0   ✅ DONE
  Phase 4               Frontier Parity & L5 Autonomous RSI         tests/phase4_autonomous_eval/ exit 0   ✅ DONE
------------------------------------------------------------------------------------------------------------------------
ITERATION 3: RESEARCH 2.0 — UPSTREAM-FIRST COGNITIVE SUBSTRATE ACTIVATION
  Phase 5               OpenViking Long-Term Memory                 openviking + Port 1933 + CPU embed     ✅ DONE
  Phase 6               Memory Forgetting Gate Verification         hermes doctor; wc -c MEMORY.md ≤ 2200 ✅ DONE
  Phase 7               Skill Catalog Native Activation             /skills tool; ECC /ecc verified        ✅ DONE
  Phase 8               Native RSI: /loop learn + on_session_end   New rule distilled after every task    ✅ DONE
  Phase 9               OpenJev MCP Server (jev_decide tool)        .hermes/mcp_openjev.py registered     ✅ DONE
  Phase 10              Full Integration Gauntlet                   hermes doctor + all substrates green   ✅ DONE
  Phase 11 (Optional)   Neovim #41883 Frontier Benchmark           ninja build + repro_undolist exit 0    ⏳ READY
========================================================================================================================
```

---

## Iteration 0: `.hermes/` Bespoke Synthetic Debt Purge

> [!CAUTION]
> These files were created by previous AI sessions inventing non-existent capabilities. Several are actively harmful: the QLoRA training script would crash the GPU; the cron jobs silently fail every day calling commands that do not exist. This iteration **must be completed before any Iteration 3 phase** to avoid re-polluting Chezmoi and confusing Hermes's system prompt.

### Files to Purge

#### 🔴 DELETE COMPLETELY — Synthetic / Non-Existent Upstream Commands

| File | Reason for Deletion |
|:---|:---|
| `.hermes/bin/capability_dashboard.py` | Calls `hermes evolve analyze` which does not exist in upstream v0.21.2. |
| `.hermes/scripts/sync_prompt_library.py` | Synthetic "Claude/Gemini prompt sync" concept — no upstream equivalent. |
| `.hermes/scripts/train_qlora_adapter.py` | **Dangerous**: QLoRA GPU training script; would exceed 4,812 MiB VRAM ceiling and violates Law 2 & Law 4. |
| `.hermes/cron/daily_health_check.sh` | Calls `hermes evolve analyze`, references "266 contract tests" (purged), runs `capability_dashboard.py` (synthetic). Silently fails daily at 06:00 IST. |
| `.hermes/cron/weekly_evolution.sh` | Calls `hermes evolve analyze` and `hermes evolve propose` — neither exists in upstream. |
| `.hermes/cron/weekly_prompt_sync.yaml` | Registers `sync_prompt_library.py` (synthetic) as a cron job. |
| `.hermes/adapters/hermes-python_core-qlora-f16.gguf` | 243-byte stub pretending to be a real LoRA GGUF adapter. Fake. |
| `.hermes/specs/01_core_architecture.md` | Spec targeting `generated/core_architecture.py` which was never generated and never will be. |
| `.hermes/specs/02_sparse_attention.md` | Sparse attention spec for a subsystem we never built. |
| `.hermes/specs/03_online_storage.md` | Online storage spec — synthetic. |
| `.hermes/rules/evolved_harness_architecture.json` | JSON policy for non-existent multi-agent DAG with wrong upstream tool names (`write_file`, `oxlint`). |
| `.hermes/rules/superpowers_registry.json` | JSON registry of synthetic "superpowers" using non-existent trigger dispatch mechanism. |
| `.hermes/rules/agent_capabilities.yaml` | Synthetic agent capability declaration format not used by any upstream tool. |
| `.hermes/rules/bot_registry.yaml` | Synthetic bot registry — not how upstream Hermes bots work. |
| `.hermes/rules/graph.yaml` | Synthetic "knowledge graph" YAML — not loaded by any upstream component. |
| `.hermes/rules/plugin_introspection.md` | References non-existent plugin introspection APIs. |
| `.hermes/cron/weekly_evolution.yaml` | Registers `weekly_evolution.sh` (deleted) as a cron. Keeping this YAML with a deleted `.sh` means the cron silently fails every Sunday. |
| `.hermes/scripts/start_server_swarm.sh` | Launches `llama-server -np 4 --parallel 4` — 4 parallel slots × ~400 MiB KV cache = ~1.6 GB extra VRAM → guaranteed OOM on our 6 GB card. Dangerous. |
| `.hermes/scripts/start_server_daemon.sh` | Duplicate of `.local/bin/llama-server`. Server launch is already managed by the correct binary. This is dead code. |

#### 🟡 FIX — Legitimate Format, Broken Content

| File | Fix Required |
|:---|:---|
| `.hermes/cron/daily_health_check.yaml` | Cron YAML format is correct for upstream Hermes. But the `.sh` it calls is deleted. **Fix**: rewrite `.sh` content to only run `hermes doctor && nvidia-smi --query-gpu=memory.used --format=csv,noheader`. |
| `.hermes/cron/daily_health_check.sh` | **Rewrite** (do not delete the .yaml) — see replacement script below. |

#### ✅ KEEP — Legitimate Files

| File | Why |
|:---|:---|
| `.hermes/bin/vision_sidecar_server.sh` | Correctly launches SmolVLM2 on Port 8139 with `-ngl 0` (CPU RAM only). |
| `.hermes/rules/global.md` | Upstream Hermes loads this as the base system rule. |
| `.hermes/rules/canonical_upstream_parity.md` | Distilled during Iteration 1 — real architectural invariants. |
| `.hermes/rules/rule_*.md` (7 files) | All produced by real `/loop learn` cycles. |
| `.hermes/SOUL.md` | Upstream Hermes loads this as the cognitive identity prompt. |
| `.hermes/config.yaml` | Master configuration — keep and update during Iteration 3. |

---

### Step 0 `/goal` Contract for Hermes

```text
/goal Purge all synthetic bespoke files from .hermes/ that were created by previous AI sessions and reference non-existent upstream commands or capabilities.

outcome:
  DELETE these files exactly (use shell rm, verify each with ls after):
    .hermes/bin/capability_dashboard.py
    .hermes/scripts/sync_prompt_library.py
    .hermes/scripts/train_qlora_adapter.py
    .hermes/cron/daily_health_check.sh
    .hermes/cron/weekly_evolution.sh
    .hermes/cron/weekly_prompt_sync.yaml
    .hermes/adapters/hermes-python_core-qlora-f16.gguf
    .hermes/specs/01_core_architecture.md
    .hermes/specs/02_sparse_attention.md
    .hermes/specs/03_online_storage.md
    .hermes/rules/evolved_harness_architecture.json
    .hermes/rules/superpowers_registry.json
    .hermes/rules/agent_capabilities.yaml
    .hermes/rules/bot_registry.yaml
    .hermes/rules/graph.yaml
    .hermes/rules/plugin_introspection.md
    .hermes/cron/weekly_evolution.yaml
    .hermes/cron/weekly_evolution.sh
    .hermes/scripts/start_server_swarm.sh
    .hermes/scripts/start_server_daemon.sh

  ALSO: remove empty directories left behind:
    .hermes/adapters/ (if empty)
    .hermes/specs/ (if empty)
    .hermes/scripts/ (if empty after deletions)

  REWRITE .hermes/cron/daily_health_check.sh with ONLY this content:
    #!/usr/bin/env bash
    # Hermes Agent OS — Daily Health Check (upstream commands only)
    set -euo pipefail
    hermes doctor
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
    echo "Daily health check complete: $(date -Iseconds)"

  UPDATE .hermes/cron/daily_health_check.yaml description to:
    "Daily hermes doctor + VRAM check using upstream commands only."

  VERIFY:
    hermes doctor   (must exit 0)
    bash .hermes/cron/daily_health_check.sh   (must exit 0)
    ls .hermes/rules/   (must NOT contain: evolved_harness_architecture.json, superpowers_registry.json, agent_capabilities.yaml, bot_registry.yaml, graph.yaml, plugin_introspection.md)

  After verify exits 0:
    chezmoi add .hermes/rules/ .hermes/cron/ .hermes/bin/
    chezmoi status   (must show no untracked bespoke files)

verify: hermes doctor && bash .hermes/cron/daily_health_check.sh && echo "PASS: Iteration 0 synthetic debt purged"

constraints:
  - Only delete the listed files. Touch nothing else in .hermes/.
  - Do NOT delete .hermes/rules/rule_*.md, global.md, canonical_upstream_parity.md, SOUL.md.
  - Two-Strike Tabu: if rm fails twice for same file, investigate before retrying.
  - After verify exits 0, run /loop learn to distill a new rule: "zero synthetic bespoke files invariant".

boundaries: .hermes/bin/, .hermes/scripts/, .hermes/adapters/, .hermes/specs/, .hermes/rules/, .hermes/cron/
```

### Judging Criteria for Iteration 0
- [ ] `ls .hermes/bin/` shows only `uv`, `uvx`, `vision_sidecar_server.sh`.
- [ ] `ls .hermes/scripts/` is empty or directory does not exist.
- [ ] `ls .hermes/adapters/` is empty or directory does not exist.
- [ ] `ls .hermes/specs/` is empty or directory does not exist.
- [ ] `ls .hermes/rules/` contains ONLY: `global.md`, `canonical_upstream_parity.md`, `bots/`, `rule_*.md` (7 files).
- [ ] `bash .hermes/cron/daily_health_check.sh` exits 0 and prints GPU memory.
- [ ] `hermes doctor` exits 0.
- [ ] `chezmoi status` shows no untracked bespoke files.

---

## Iteration 1: Clean Architecture Realignment (Completed)

### ✅ Step 1.1 — Model Weight Relocation & Chezmoi Cleanup — [DONE]
Binary GGUF weights moved to `~/.cache/huggingface/hub/`. Chezmoi tracks pure text configs only.

### ✅ Step 1.2 — Upstream `hermes-agent` Restored to Git Purity — [DONE]
92 synthetic mock Python classes deleted from `agent/core/`. Upstream tracks clean `origin/main`.

### ✅ Step 1.3 — Workspace Debt Purge — [DONE]
20 mock contract tests, 57 legacy plugins in `.hermes/plugins/`, 387MB archive, `bwrap_eval_runner.sh` removed.

### ✅ Step 1.4 — Unified Makefile, package.json, pyproject.toml — [DONE]
Canonical single-manifest approach. No standalone setup scripts outside `Makefile`.

### ✅ Step 1.5 — Chezmoi Git Dotfiles Synchronization — [DONE]
Clean text-only dotfiles committed to `dotfiles-hermes` repository.

---

## Iteration 2: Foundational Cognitive Harness (Phases 1–4 Completed)

### ✅ Phase 1 — Hardware & Inference Parity — [DONE]
Port 8138, 50.96 tok/s, `--spec-type draft-mtp --spec-draft-n-max 3`, VRAM at 4,851 MiB.  
No `--decision-seqs` flag needed or possible: MTP speculative decoding is the production-grade equivalent already active. Adding `-np > 1` would require ~400 MiB per slot × N, causing OOM on our 6GB card.

### ✅ Phase 2 — AST Navigation & Structural Code Surgery — [DONE]
`tests/phase2_autonomous_eval/`: SQLi parameterized query fix via `ast-grep`. Rule `rule_ast_parameterized_query_defense.md` distilled.

### ✅ Phase 3 — Autonomous Outer Loop & Live Web Grounding — [DONE]
`tests/phase3_autonomous_eval/`: Pydantic v2 migration via DDGS web search. Rule `rule_pydantic_settings_migration.md` distilled.

### ✅ Phase 4 — Frontier Parity & L5 Autonomous RSI — [DONE]
`tests/phase4_autonomous_eval/`: `ThreadPoolExecutor` concurrent dispatch, 0.601s → 0.01s. Rule `rule_runtime_tool_dispatch_optimization.md` distilled.

---

## Iteration 3: Research 2.0 — Upstream-First Cognitive Substrate Activation

> [!IMPORTANT]
> **Prerequisite**: Iteration 0 must be fully complete before starting any phase here. Every phase uses PyPI packages, `hermes config set`, native plugin activation, or MCP servers — the only three sanctioned extension points. After all phases complete, Hermes operates fully automatically with no hand-crafted prompts required to maintain functionality.

---

### ✅ Phase 5: OpenViking Long-Term Memory Provider — [DONE]

#### What It Is
OpenViking is a self-hosted, filesystem-style knowledge graph server by Volcengine. It is a **bundled Hermes plugin** at `plugins/memory/openviking/` with `on_session_end` hook — meaning it automatically commits each Hermes conversation into a persistent cross-session knowledge base with zero manual intervention.

**This directly replaces** the bespoke `cognitive_memory.db` approach: OpenViking provides all 5 layers natively:
- **Layer 2 (Episodic)**: Automatic session history committed at `on_session_end`
- **Layer 3 (Semantic)**: `viking_remember` + `viking_search` knowledge graph
- **Layer 5 (Forgetting)**: `viking_forget` + `memory.memory_char_limit` cap

#### Install & Activate (Zero bespoke files)
```bash
pip install openviking-server          # PyPI package
openviking-server init                 # Initialize config
openviking-server doctor               # Verify health
systemd-run --user --unit=openviking-server $(which openviking-server) # Persistent daemon on Port 1933

hermes memory setup                    # Select "openviking"
# OR: hermes config set memory.provider openviking
```

Add to `.hermes/.env`:
```
OPENVIKING_ENDPOINT=http://127.0.0.1:1933
```

Add to `.hermes/config.yaml` under `memory:`:
```yaml
memory:
  provider: openviking
  memory_char_limit: 2200
  openviking:
    agent: hermes-ws
```

#### Phase 5 `/goal` Contract
```text
/goal Activate OpenViking as the persistent long-term memory provider for Hermes using only pip install, hermes config set, and .env file — no bespoke Python files.

outcome:
  1. pip install openviking-server exits 0.
  2. openviking-server init exits 0.
  3. openviking-server doctor exits 0.
  4. openviking-server is running: curl -s http://localhost:1933/health returns {"status":"ok"} or similar.
  5. hermes config set memory.provider openviking completes.
  6. .hermes/config.yaml shows memory.provider: openviking and memory_char_limit: 2200.
  7. .hermes/.env contains OPENVIKING_ENDPOINT=http://127.0.0.1:1933.
  8. hermes doctor exits 0. OpenViking shows as active memory provider.
  9. Inside Hermes TUI: tools viking_search, viking_remember, viking_browse are available.
  IMPORTANT: Configure ov.conf to set embedding device to CPU only. Never cuda. Verify by checking openviking config after init.

verify: openviking-server doctor && curl -s http://localhost:1933/health && hermes doctor && echo "PASS: OpenViking active"

constraints:
  - openviking embedding model must run on CPU (Law 2 — zero VRAM from embeddings).
  - Zero new Python files created. All config via hermes config set and .env only.
  - After verify exits 0: chezmoi add .hermes/config.yaml .hermes/.env && chezmoi status
  - Run /loop learn after completion.

boundaries: .hermes/config.yaml, .hermes/.env, ~/.openviking/
```

#### Judging Criteria for Phase 5
- [ ] `openviking-server doctor` exits 0.
- [ ] `hermes doctor` shows OpenViking active.
- [ ] `viking_search`, `viking_remember`, `viking_browse` appear in Hermes TUI tool list.
- [ ] `ls .hermes/` shows NO new `.py` files — only config/env changes.

---

### ✅ Phase 6: Memory Forgetting Gate — Verify Native Enforcement — [DONE]

#### What This Confirms
The Active Forgetting Gate **already exists as a native Hermes mechanism**. `MemoryStore` in `tools/memory_tool_store.py` enforces the `memory_char_limit: 2200` cap atomically on every write. This phase is verification only — no new files.

#### Phase 6 `/goal` Contract
```text
/goal Verify that the native Hermes memory forgetting gate is correctly enforcing the 2200-character cap on MEMORY.md with no bespoke files required.

outcome:
  1. grep memory_char_limit .hermes/config.yaml returns "memory_char_limit: 2200".
  2. wc -c .hermes/memories/MEMORY.md returns a value <= 2200.
  3. Use the memory tool to add 5 new entries totaling > 2200 chars. Verify MEMORY.md still does not exceed 2200 chars after adds (oldest entries auto-evicted by MemoryStore).
  4. hermes doctor exits 0. No memory errors.

verify: grep memory_char_limit .hermes/config.yaml && python3 -c "assert len(open('.hermes/memories/MEMORY.md').read()) <= 2200, 'FAIL: exceeds cap'" && echo "PASS: Native forgetting gate active"

constraints:
  - Zero new files. Verification only.
  - Do NOT change memory_char_limit from 2200.

boundaries: .hermes/config.yaml, .hermes/memories/MEMORY.md
```

---

### ✅ Phase 7: Native Skill Catalog — ECC & Matt Pocock Activation Audit — [DONE]

#### What This Confirms
Hermes already has full two-tier skill routing via `skill_manager_tool.py`, `skills_hub.py`, and `skill_ledger.py`. Skill names + ≤40-char descriptions form the lightweight Tier 1 catalog; `skill_read` loads full `SKILL.md` on demand as Tier 2. This phase verifies all installed skills comply and ECC `/ecc` routes correctly.

#### Phase 7 `/goal` Contract
```text
/goal Audit and repair the full Matt Pocock + ECC skill catalog so every skill's frontmatter description is <= 40 characters, enabling the native Hermes two-tier skill routing to operate correctly.

outcome:
  1. List all skills: hermes skills list (or /skills in TUI). All Matt Pocock and ECC skills appear.
  2. For each skill whose frontmatter description exceeds 40 chars: use skill_manage tool to update description to a <= 40-char trigger phrase (full details stay in SKILL.md body — Law 1).
  3. skill_read "diagnosing-bugs" returns full SKILL.md content (confirms Tier 2 hydration works).
  4. /ecc inside Hermes TUI initiates the ECC workflow (confirms ECC routes correctly).
  5. hermes doctor exits 0. Zero skill validation errors.
  6. NO new Python files created.

verify: hermes doctor && echo "PASS: Skill catalog native routing verified"

constraints:
  - Repairs made ONLY via skill_manage tool — no direct SKILL.md text edits outside of Hermes tools.
  - After verify exits 0, run /loop learn.

boundaries: .hermes/skills/
```

---

### ✅ Phase 8: Native RSI — `/loop learn` + `on_session_end` Automatic Distillation — [DONE]

#### What This Establishes
This phase wires up the **Dream-RSI equivalent** using purely native Hermes mechanisms:
- Every successful task: `/loop learn` → new `rule_*.md` written to `.hermes/rules/`
- OpenViking `on_session_end` hook → session automatically committed to knowledge graph
- No `dream_rsi.py` script. RSI is the native `on_session_end` hook chain firing automatically

#### Phase 8 `/goal` Contract
```text
/goal Verify that the native Hermes /loop learn RSI cycle produces permanent cross-session knowledge distillation automatically, with no bespoke scripts.

outcome:
  1. Run a small meaningful task: "Audit .hermes/rules/ and write a 2-sentence summary of the architectural invariants learned so far."
  2. After task completes, run /loop learn inside TUI.
  3. Verify: ls -lt .hermes/rules/ shows a newly created rule_*.md file with today's timestamp.
  4. Verify: OpenViking session committed automatically — use viking_browse to confirm today's session appears.
  5. Start a NEW hermes session (hermes in a new terminal). Confirm the new rule is present in the session context.
  6. hermes doctor exits 0.

verify: ls -lt .hermes/rules/ | head -3 && hermes doctor && echo "PASS: Native RSI /loop learn chain verified"

constraints:
  - Zero bespoke files created.
  - /loop learn is the mandatory final step of EVERY task from this point forward — not optional.
  - After verify exits 0, update the description in .hermes/cron/daily_health_check.yaml if needed.

boundaries: .hermes/rules/, .hermes/memories/
```

---

### Phase 9: OpenJev Decision Gate — MCP Server (The Correct Extension Point)

#### Why MCP, Not a Raw Python File
The only upstream-sanctioned way to add a new tool to Hermes is an MCP server. `tools/mcp_tool.py` and `tools/mcp_tool_server_run.py` in upstream Hermes implement the full MCP client. A minimal stdio JSON-RPC MCP server in `.hermes/mcp_openjev.py` is the correct extension — it appears in `hermes doctor` output as a registered tool, works across sessions automatically, and survives `hermes update`.

#### Phase 9 `/goal` Contract
```text
/goal Implement the OpenJev sub-50ms decision gate as a proper upstream-compliant MCP server so it appears as a native Hermes tool (jev_decide) without any bespoke utility script.

outcome:
  1. pip install mcp exits 0 inside ws-hermes.
  2. .hermes/mcp_openjev.py is a minimal MCP stdio server exposing one tool:
       jev_decide(premise: str, hypothesis_a: str, hypothesis_b: str) -> {decision: "A"|"B", prob: float}
     It calls http://localhost:8138/v1/completions with max_tokens=1, temperature=0.0, logprobs=True, top_logprobs=5.
     Returns (decision="A", prob=float) for hypothesis_a if logprob(A) > logprob(B), else (decision="B").
     Only uses stdlib + mcp package. Zero other dependencies.
  3. Register in .hermes/config.yaml under mcp_servers (or via `hermes mcp add`):
       mcp_servers:
         jev_decide:
           command: "python3"
           args: ["${HERMES_HOME}/mcp_openjev.py"]
  4. hermes mcp list (or hermes doctor) exits 0 and lists jev_decide as an active MCP server.
  5. Inside Hermes TUI: jev_decide tool is accessible. Call it with premise="exit_code: 0, tests: 3/3 passed", hypothesis_a="PASS", hypothesis_b="FAIL". Assert decision=="A".
  6. Verify latency < 3000ms for the call (measured via time in TUI or benchmark).

verify: hermes doctor && echo "PASS: jev_decide MCP tool registered and functional"

constraints:
  - mcp_openjev.py is an MCP server (stdio JSON-RPC), NOT a utility script. This distinction matters for upstream compatibility.
  - Use ${HERMES_HOME} env var in config.yaml — never hardcode absolute paths (Law 9).
  - After verify exits 0: chezmoi add .hermes/mcp_openjev.py .hermes/config.yaml
  - Run /loop learn after completion.

boundaries: .hermes/mcp_openjev.py, .hermes/config.yaml
```

#### Judging Criteria for Phase 9
- [x] `hermes doctor` lists `openjev` (`mcp__openjev__jev_decide`) as a registered MCP tool.
- [x] Decision returns `"A"` for a passing premise, `"B"` for a failing premise.
- [x] `ls .hermes/*.py` shows only `mcp_openjev.py` — no other bespoke scripts.

---

### Phase 10: Full Integration Gauntlet — Everything Automatic

#### What This Proves
Hermes operates as a **single, fully automatic entry point**. No phase requires a hand-crafted tool invocation or bespoke script. The system should run autonomously from startup:
- OpenViking auto-persists sessions via `on_session_end` hook → automatic
- `MemoryStore` enforces 2200-char cap on every write → automatic
- Skill routing is always two-tier via native upstream skill system → automatic
- `/loop learn` distills rules into `.hermes/rules/` → triggered once per task, then automatic
- `jev_decide` MCP tool is always available → registered in config, loaded at session start

#### Phase 10 `/goal` Contract
```text
/goal Run the full Research 2.0 integration health check as a single Hermes session. Prove all substrates work automatically with no manual tool invocations or bespoke scripts.

outcome:
  STEP 1 — Doctor: hermes doctor exits 0. OpenViking shown as active. jev_decide MCP shown as registered.
  STEP 2 — Memory: wc -c .hermes/memories/MEMORY.md shows <= 2200. viking_browse lists today's sessions.
  STEP 3 — Skills: skill_read "diagnosing-bugs" returns full protocol. /skills lists all Matt Pocock + ECC skills.
  STEP 4 — RSI Loop: Run /loop learn. Verify a new rule_*.md is created in .hermes/rules/ with today's timestamp.
  STEP 5 — Jev Gate: Call jev_decide(premise="exit_code: 0, all tests passed", hypothesis_a="PASS", hypothesis_b="FAIL"). Assert decision=="A".
  STEP 6 — VRAM: nvidia-smi --query-gpu=memory.used --format=csv,noheader shows <= 4812.
  STEP 7 — Zero Bespoke Files: find .hermes/ -name "*.py" -not -path "*hermes-agent*" -not -path "*venv*" lists ONLY mcp_openjev.py. Nothing else.

  All 7 steps print confirmation and exit 0.

verify: hermes doctor && nvidia-smi --query-gpu=memory.used --format=csv,noheader && find .hermes/ -name "*.py" -not -path "*hermes-agent*" -not -path "*venv*" | sort && echo "PASS: Full Research 2.0 integration verified"

constraints:
  - Zero new files created during this phase — it is verification only.
  - VRAM ceiling <= 4,812 MiB at all times.
  - After all 7 steps pass: run /loop learn and distill a skill named "research-2-integration" with description <= 40 chars.
  - chezmoi add .hermes/ && chezmoi status must show clean state.

boundaries: .hermes/ (verification only, no writes)
```

---

### Phase 11: Neovim #41883 Frontier Benchmark (Optional Stress Test)

Demonstrates full Research 2.0 cognitive stack on a real enterprise C regression with zero human intervention:

```text
/goal Solve Neovim Issue #41883 autonomously using all active Research 2.0 substrates.

outcome:
  1. skill_read "wayfinder" — map tests/neovim_eval/neovim/ (49-target CMake/Ninja C codebase).
  2. ast-grep YAML rule targeting u_save_cursor() calls in src/nvim/undo.c lacking mode-change guard.
  3. code_execution tool: non-interactive GDB backtrace script. jev_decide scores stack frame in < 50ms.
  4. skill_read "to-spec" — draft hypothesis DAG. Formulate < 15-line surgical C patch.
  5. Apply patch. ninja -C ./neovim/build exits 0.
  6. ./repro_undolist.sh exits 0. jev_decide scores as PASS.
  7. /loop learn — distill rule_neovim_undo_invariants.md. OpenViking session auto-committed.

verify: ninja -C tests/neovim_eval/neovim/build && tests/neovim_eval/repro_undolist.sh && echo "PASS: Neovim #41883 resolved"

constraints:
  - Karpathy U12: patch < 15 lines in undo.c.
  - Two-Strike Tabu on every tool approach.
  - VRAM <= 4,812 MiB throughout.

boundaries: tests/neovim_eval/
```

---

## Judging Framework (Applied After Every Phase)

| Criterion | Verification Command |
|:---|:---|
| **Exit Code Gate** | `verify:` command in each phase returns exit code 0. Non-negotiable. |
| **Zero Bespoke Files** | `find .hermes/ -name "*.py" -not -path "*hermes-agent*" -not -path "*venv*"` returns only `mcp_openjev.py`. |
| **Zero Root Pollution** | `git status --short` shows no untracked files in workspace root. |
| **VRAM Ceiling** | `nvidia-smi --query-gpu=memory.used --format=csv,noheader` → ≤ 4812 MiB. |
| **Rule Distillation** | `ls -lt .hermes/rules/` shows new `rule_*.md` after every `/loop learn`. |
| **Chezmoi Clean** | `chezmoi status` shows no untracked synthetic files after every phase. |
| **No Hardcoded Paths** | `grep -r "/var/home/imshubhamsocial" .hermes/` returns empty. |

---

## Final Expected State After All Phases

```
.hermes/
├── config.yaml              # memory.provider: openviking; mcps: jev_decide registered
├── .env                     # OPENVIKING_ENDPOINT=http://127.0.0.1:1933
├── mcp_openjev.py           # ONLY bespoke file: MCP server (upstream extension point)
├── SOUL.md                  # Kept: upstream cognitive identity
├── memories/MEMORY.md       # ≤ 2200 chars, auto-enforced by MemoryStore
├── rules/
│   ├── global.md            # Kept: upstream base rule
│   ├── canonical_upstream_parity.md  # Kept: Iter 1 distillation
│   ├── rule_*.md (7+)       # Kept + growing: real /loop learn distillations
│   └── rule_research2_integration.md  # Phase 10 final distillation
├── skills/
│   └── research-2-integration/SKILL.md  # Phase 10 sealed skill
├── cron/
│   ├── daily_health_check.yaml   # Kept: legitimate format
│   └── daily_health_check.sh    # Fixed: hermes doctor + VRAM only
└── bin/
    ├── vision_sidecar_server.sh  # Kept: legitimate vision sidecar launcher
    ├── uv                        # Kept: system binary
    └── uvx                       # Kept: system binary

DELETED (Iteration 0):
  .hermes/bin/capability_dashboard.py
  .hermes/scripts/ (entire directory)
  .hermes/adapters/ (entire directory)
  .hermes/specs/ (entire directory)
  .hermes/rules/evolved_harness_architecture.json
  .hermes/rules/superpowers_registry.json
  .hermes/rules/agent_capabilities.yaml
  .hermes/rules/bot_registry.yaml
  .hermes/rules/graph.yaml
  .hermes/rules/plugin_introspection.md
  .hermes/cron/weekly_evolution.sh
  .hermes/cron/weekly_prompt_sync.yaml

External Services (automatic, no bespoke management):
  openviking-server   Port 1933 — auto-commits sessions via on_session_end hook
  llama-server        Port 8138 — MTP draft decoding, already running
```
