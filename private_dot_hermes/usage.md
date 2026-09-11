# Hermes Usage Guide — Enforced Spec-Kit & Loop-Driven Workflow

> **This document is LAW. Every session — by you OR Hermes — follows this workflow without exception.**
> No deviations. No shortcuts. The loop is the contract.

---

## The Golden Rule

> **SPEC BEFORE CODE. VERIFY BEFORE DONE. COMMIT BEFORE RESET.**

Every interaction with Hermes must flow through the same 5-phase loop — whether you are asking a simple question, building a feature, debugging a regression, or running an experiment. The loop is non-negotiable.

---

## Phase 0 — Session Initialization (Every Single Session)

Before anything else:

```bash
# 1. Confirm server health
curl -s http://127.0.0.1:8138/health
# Expected: {"status":"ok"}

# 2. Check VRAM (must be ≤ 4,812 MiB)
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits

# 3. Check container context
command -v python3.13
# If not found → prefix all commands with: distrobox enter ws-hermes --

# 4. Start Hermes (interactive)
hermes
# OR for one-shot
hermes -z "<your task here>" --yolo
```

**If server is NOT running:**
```bash
bash ~/.hermes/scripts/start_server_daemon.sh
sleep 5
curl -s http://127.0.0.1:8138/health
```

---

## Phase 1 — Spec-Kit (MANDATORY FIRST STEP FOR EVERY TASK)

Before writing ANY code or making ANY change, you MUST emit a spec. No exceptions.

### 1A. Define the Experiment / Task

Answer these 4 questions in plain text (or tell Hermes to do it):

```
WHAT: What is the minimal implementation delivering 80% of value?
SKIP: What is explicitly deferred (gold-plating)?
VALIDATE: What single invariant, if broken, invalidates the approach?
TEST: What is the cheapest sub-second test that proves viability?
```

### 1B. Hermes Emits the Spec

Tell Hermes:
```
"Spec-kit this task: <your task description>"
```

Hermes will produce and persist:
```json
// .hermes/plan.json
{
  "task": "<name>",
  "hypothesis": "<what we expect to happen>",
  "milestones": [
    { "id": "M1", "goal": "...", "status": "PENDING" },
    { "id": "M2", "goal": "...", "status": "PENDING" }
  ],
  "done_when": "<acceptance criterion>",
  "measure": "<metric to verify success>"
}
```

### 1C. Domain Decomposition

Hermes identifies the core domain and assigns bots:
- `@architect` → Spec + blueprint + plan.json
- `@coder` → Implementation
- `@tester` → Contract tests + observer gate
- `@researcher` → Web grounding for unfamiliar APIs (isolated scratchpad)

**Trigger**: Say "decompose this task" or Hermes does it automatically for any non-trivial request.

---

## Phase 2 — Context Sieve (No Bloat in Context Window)

Hermes NEVER dumps full files into context. The sieve enforces these limits:

| Source | Budget |
|--------|--------|
| Plugin discovery summary | ≤ 150 tokens |
| Single skill injection | ≤ 200 tokens |
| Template retrieval | ≤ 400 tokens |
| Minimal system prompt | ≤ 350 tokens |

**How to trigger context sieve manually:**
```bash
python3.13 ~/.hermes/bin/skill_router.py "<query about what you need>"
# Returns: matched skill + instructions, ≤ 200 tokens
```

**AST search (never read files manually):**
```bash
rg -n "<pattern>"                          # Sub-20ms text search
ast-grep -p "<pattern>" --lang python      # AST-level symbol search
```

---

## Phase 3 — Loop-Driven Implementation (Act + Verify Cycle)

### The Implementation Loop

```
┌─────────────────────────────────────────────────────────┐
│                   IMPLEMENTATION LOOP                    │
│                                                          │
│  1. IMPLEMENT → Single surgical patch (no full rewrites) │
│        │                                                 │
│        ▼                                                 │
│  2. VERIFY   → Observer gate + syntax check              │
│        │                                                 │
│        ├─ PASS → Proceed to next milestone               │
│        │                                                 │
│        └─ FAIL → Strike 1: Form new hypothesis, retry   │
│                  Strike 2: STOP. Rollback. New approach. │
│                                                          │
│  3. TEST     → Run contract tests after each milestone   │
│        │                                                 │
│        ├─ GREEN → Mark milestone COMPLETED               │
│        └─ RED   → 2-Strike Tabu Rule applies             │
└─────────────────────────────────────────────────────────┘
```

### Implementation Rules

1. **Surgical patches only** — never rewrite whole files
2. **One milestone at a time** — never skip to M3 before M1 is verified
3. **No speculation** — verify API signatures with `rg`, `ast-grep`, or web grounding before using them
4. **No mannered prose** — dense, factual, direct only
5. **3-Turn session limit for local 4B models** — after 3 heavy implementation turns, reset session

### 2-Strike Tabu Rule (MANDATORY)

```
Attempt 1 fails → DISCARD that hypothesis. Form a strictly different alternative.
Attempt 2 fails → STOP. Run /rollback. Record failure in hypothesis_tree.json. Start fresh session.

FORBIDDEN: Toggling back to a previously failed pattern.
```

```bash
# Rollback if stuck
/rollback

# Record failure
python3.13 ~/.hermes/bin/hypothesis_tree.py --add-failure "<error description>"

# Start fresh
hermes  # new session reads disk as ground truth
```

---

## Phase 4 — Pre-Commit Verification Gate (MANDATORY BEFORE DONE)

**A task is NEVER complete until this gate passes.** No exceptions. No "I think it's done."

```bash
# Step 1: Observer gate (6-point check)
python3.13 ~/.hermes/bin/observer_gate.py <modified_file>
# Expected: "APPROVED: All 6 gates passed"

# Step 2: Contract test suite
python3.13 -m pytest tests/harness_contracts/ -q
# Expected: 614 passed (≈ 26s)
# NOTE: Run inside ws-hermes container if on host

# Step 3: Master capability audit
python3.13 ~/.hermes/bin/verify_harness_integrity.py
# Expected: "APPROVED: 10/10 capabilities"

# Step 4: Live Hermes verification
hermes -z "<test prompt matching the task>" --yolo --usage-file /dev/shm/usage.json
```

**If ANY step fails → return to Phase 3. Apply 2-Strike Tabu Rule.**

### Observer Gate Checks (What It Verifies)

1. Syntax validity (no unclosed braces, missing imports)
2. Scope audit (no global variable collisions)
3. Brace/bracket parity
4. File size ceiling (no unintended bloat)
5. Import graph integrity (no circular imports)
6. Interface contract preservation (exported APIs unchanged)

---

## Phase 5 — Commit & Chezmoi Synchronization

```bash
# Track changes in Chezmoi (version control for all config/scripts/skills)
chezmoi add <changed_file>
git -C ~/.local/share/chezmoi add -A
git -C ~/.local/share/chezmoi commit -m "<type>(<scope>): <summary>"
git -C ~/.local/share/chezmoi push origin master
```

**Commit types**: `feat`, `fix`, `refactor`, `chore`, `test`, `docs`

**After milestone commit:**
1. Update `plan.json` milestone status to `"COMPLETED"`
2. Recommend `/reset` for next milestone (fresh attention window)

---

## The Experiment Session Model (Vaibhav Sisinty Integration)

Every Hermes session can be framed as an **experiment**:

```bash
# Start with explicit experiment framing
hermes -z "EXPERIMENT: <hypothesis> | MEASURE: <metric> | DONE_WHEN: <criterion>" --yolo

# After session completes, capture playbook
# Hermes automatically writes to: ~/.hermes/knowledge/playbooks/<date>-<experiment>.md
```

**Weekly review cadence:**
- Review all playbooks from the week
- Feed successful patterns into GEPA optimizer
- Feed failed experiments into hypothesis_tree.json
- Let GEPA evolve better prompts for next week

---

## Quick Command Reference

| Action | Command | Expected Output |
|--------|---------|----------------|
| Server health check | `curl -s http://127.0.0.1:8138/health` | `{"status":"ok"}` |
| Start server daemon | `bash ~/.hermes/scripts/start_server_daemon.sh` | Health check returns ok |
| Start interactive chat | `hermes` | Live TUI / REPL |
| One-shot prompt | `hermes -z "<prompt>" --yolo` | Exit code 0 |
| Observer gate | `python3.13 ~/.hermes/bin/observer_gate.py <file>` | APPROVED: All 6 gates |
| Full contract tests | `python3.13 -m pytest tests/harness_contracts/ -q` | 614 passed |
| Master self-audit | `python3.13 ~/.hermes/bin/verify_harness_integrity.py` | 10/10 capabilities |
| Skill lookup | `python3.13 ~/.hermes/bin/skill_router.py "<query>"` | Skill in ≤ 200 tok |
| Web grounding | `python3.13 ~/.hermes/bin/web_grounding.py "<query>"` | Context in ≤ 150 tok |
| VRAM check | `nvidia-smi` | ≤ 4,812 MiB |
| Chezmoi status | `chezmoi status` | 0 lines (clean) |
| Rollback | `/rollback` | Pre-mutation snapshot restored |
| Reset session | `/reset` or start `hermes` fresh | Clean attention window |

---

## Anti-Patterns (NEVER DO THESE)

| Anti-Pattern | Why Forbidden | What To Do Instead |
|-------------|--------------|-------------------|
| Writing code without a spec | Violates Law #2 (Spec-First) | Run spec-kit first (Phase 1) |
| Claiming "done" without observer gate | Violates Law #5 | Always run verification gate (Phase 4) |
| Full file rewrites via `write_file` | Violates Coding Law #3 | Surgical patches only |
| Repeating a failed patch pattern | Violates Tabu Rule (Law #6) | Form a strictly different hypothesis |
| Dumping full repos into context | Violates Law #1 (Zero Token Waste) | Use rg + ast-grep + AST sieve |
| Running heavy Python on host OS | Violates container rule | `distrobox enter ws-hermes -- <cmd>` |
| VRAM > 4,812 MiB | Violates hardware guard | Reduce context tier or restart |
| Hardcoded absolute paths in code | Violates relative paths law | Use $HOME or relative paths only |
| Not committing to Chezmoi | Config lost on reinstall | Always `chezmoi add` after changes |
| Skipping contract tests | Regressions sneak in | `pytest tests/harness_contracts/ -q` |

---

## Hermes for Vaibhav-Style Growth Experiments

When running growth/productivity experiments through Hermes:

```bash
# Frame as experiment
hermes -z "EXPERIMENT: Test if Perplexity grounding improves research quality over SearXNG
           MEASURE: Token count + accuracy of grounding output
           DONE_WHEN: 10 research queries compared side-by-side with quality scores"

# Hermes will:
# 1. Spec-kit the experiment (Phase 1)
# 2. Implement measurement harness (Phase 2-3)
# 3. Run experiments + verify (Phase 4)
# 4. Write playbook to ~/.hermes/knowledge/playbooks/ (Phase 5)
# 5. Report: hypothesis confirmed/rejected + learnings
```

---

## Session Lifecycle Summary

```
NEW SESSION
    │
    ▼
[Phase 0] Init: health check + VRAM check
    │
    ▼
[Phase 1] Spec-Kit: What / Skip / Validate / Test → plan.json
    │
    ▼
[Phase 2] Context Sieve: ≤ 150 tok plugins, ≤ 400 tok templates
    │
    ▼
[Phase 3] Loop: Implement → Verify → Test → (2-Strike Tabu) → repeat
    │
    ▼
[Phase 4] Gate: Observer gate → 614 tests → 10/10 audit → live verify
    │
    ▼
[Phase 5] Commit: chezmoi add → git commit → plan.json COMPLETED → /reset
    │
    ▼
NEXT SESSION (fresh context, disk as ground truth)
```

---

## The 5 Immovable Hardware Invariants

1. **VRAM ≤ 4,812 MiB** — enforced by context_window_guard.py
2. **Inference on GPU, embeddings on CPU** — zero GPU contention for vectors
3. **All Python runs inside `ws-hermes` distrobox** — never on host Fedora Kinoite
4. **llama-server on port 8138** — dedicated, no port sharing
5. **Hot writes to /dev/shm RAMDisk** — SQLite WAL, trajectories, test scratchpads

---

> **This workflow applies to EVERY session, EVERY task, EVERY experiment.**
> There are no exceptions. The loop is what makes Hermes rigorous.
> Vaibhav ships experiments fast. Hermes ships them correctly. The combination is optimal.
