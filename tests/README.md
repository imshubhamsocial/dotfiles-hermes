# Hermes Autonomous Capability Evaluation Testbeds (`tests/`)

This directory houses all prompt-driven, end-to-end evaluation testbeds designed to benchmark and demonstrate **GPT-Astra AGI Capabilities** and **Gemini 3.8-Cyber Capabilities** under production conditions.

---

## 1. Core Operating Principles

### A. Strict Subfolder & Git Isolation
* Every single testbed or experiment must reside in its own dedicated subfolder under `tests/` (e.g. `tests/01_ecommerce_rag/`, `tests/02_ast_refactor/`).
* Each testbed folder **must be an isolated git repository**:
  ```bash
  mkdir -p tests/<testbed_name>
  cd tests/<testbed_name>
  git init .
  ```
* Test artifacts, generated code, synthetic mock databases, and scratch logs must remain strictly contained within that isolated sub-repository.

### B. The `/loop` Autonomous Execution Mandate
* All workflows—both automated tests and interactive development—**must strictly adhere to the `/loop` autonomous execution model**.
* Hermes is required to operate with full agency without human micromanagement or repeated step-by-step steering:
  1. **Prompt & Goal Management**: Ingests raw objectives and refines them into verifiable goals.
  2. **Topological MRP Planning**: Decomposes complex problems into directed acyclic task graphs (DAGs) and executes in dependency waves.
  3. **Repository Knowledge Graph**: Autonomously leverages symbol indexing, AST parsing, and knowledge graph tools (`semantic_triples.db`, Graphiti) when encountering heavy codebases.
  4. **Dynamic Skill & Package Selection**: Identifies required capabilities, activates matching skills, downloads missing skills into `skills/`, and installs missing Python or system dependencies dynamically.
  5. **Context Compaction & Memory Triage**: Automatically flushes context via `/clear` at 80% capacity boundary (52,428 tokens), persists atomic state checkpoints to SQLite, and compacts experiences.
  6. **In-Flight Continuous Learning (`/learn`)**: Analyzes execution obstacles, categorizes failure modes, and synthesizes permanent markdown rules into `rules/` on the fly.
  7. **Autonomous Quality Assurance (QA)**: Designs and executes independent verification suites, checks invariants with AST and SymPy gates, and auto-repairs regressions before declaring completion.

---

## 2. Production TUI Execution Protocol

Production Hermes operates through its **rich terminal user interface (TUI)** rather than headless chat pipes. All prompt-based tests must be initiated using the TUI interface.

### Running a Test via Hermes TUI
To execute a test scenario:
```bash
# Direct TUI prompt invocation inside container
distrobox enter ws-hermes -- hermes "<prompt>"
```

### Launching via Dedicated Terminal Window (`konsole`)
For live visual monitoring of the TUI in desktop production environments:
```bash
konsole --new-tab -e distrobox enter ws-hermes -- hermes "<prompt>"
```
*Or dynamically launching from inside scripts:*
```bash
konsole -e bash -c "distrobox enter ws-hermes -- hermes \"$PROMPT\"; exec bash" &
```

---

## 3. Evaluation Target Matrix

| Capability Benchmark | Target Subsystem | Evaluation Metric | Autonomous Criteria |
|:---|:---|:---|:---|
| **GPT-Astra AGI Equivalence** | Reasoning, Multi-Agent MoA, Self-Evolution | Zero-shot planning, topological task decomposition, self-directed tool usage | 100% autonomous resolution without human intervention |
| **Gemini 3.8-Cyber Intelligence** | Security Guardrails, AST Verification, Self-Repair | Automated vulnerability isolation, blast-radius bounding, atomic rollbacks | Sub-5ms invariant enforcement, zero regression |
| **Long-Horizon Persistence** | BPE Memory Workspace, Context Compactor | Multi-turn `/loop` execution past 100K tokens with `/clear` checkpoints | Exact state recall across context boundary flushes |
