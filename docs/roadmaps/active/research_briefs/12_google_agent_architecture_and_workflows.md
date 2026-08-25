# 12. Google Agent Architecture: Memory, Execution, Sessions & Self-Evolution

> **Research Source Reference**: `hermes/web/` (`google/adk-python`, `google-gemini/gemini-cli`, `googleapis/python-genai`, `antigravity-guide`)  
> **Topic Category**: Frontier Agent OS, Cognitive Memory, Session Lifecycles & Self-Learning  
> **Sequential Index**: `12 / 12`

---

## 1. Executive Overview: The Google Agent Paradigm

Google's frontier agent infrastructure (spanning **Google DeepMind**, **Google Antigravity (AGY)**, and the **Google Agent Development Kit (ADK 2.0)**) models an AI agent not as a single conversational loop, but as a **hierarchical, reactive state machine operating over an asynchronous execution graph**.

This document captures the complete architectural blueprint of how Google handles:
1. **Memory Management & Context Compaction**
2. **Task Execution & Graph Orchestration**
3. **Session Lifecycle & State Persistence**
4. **Hardware & Token Optimization (System-2 Dynamics)**
5. **Continuous Self-Evolving & Autonomous Learning (`/learn`)**

---

## 2. Metacognitive Lifecycle: From Prompt to Execution

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 GOOGLE AGENT COGNITIVE PIPELINE                                  │
├─────────────────┬────────────────────────────────────────────────────────────────────────────────┤
│ 1. Ingestion    │ System Prompt Slotting + Hierarchical Rules Discovery (GEMINI.md / AGENTS.md) │
├─────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 2. Grounding    │ Static Discovery + Progressive Disclosure (Indexing Skills without Body Load) │
├─────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 3. Planning     │ Graph-Based Task Decomposition (Task API / Multi-Agent Delegation Nodes)      │
├─────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 4. Execution    │ Reactive Tool Calling + Thought Signature Propagation + Asynchronous Dispatch  │
├─────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 5. Memory & Log │ JSONL Chronological Transcripts + Artifact Persistence + Vector Episodic Store │
├─────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 6. Evolution    │ Self-Learning Hook (/learn) -> Autonomous Rule & Skill Promotion               │
└─────────────────┴────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Architectural Mechanisms

### 3.1. Memory Management & Multi-Tier Storage
Google avoids dumping raw chat logs into prompts. Memory is partitioned across four distinct tiers:
1. **Working Memory (Active Context Window)**: Contains only the immediate turn, active file diffs, and injected skill instructions.
2. **Episodic & Architectural Memory (`<appDataDir>/brain/<id>/`)**: Large reports, diffs, architectural plans, and interactive diagrams are persisted as structured Markdown artifacts (`artifact.md`) rather than cluttering conversation history.
3. **Chronological Event Ledger (`transcript.jsonl` & `transcript_full.jsonl`)**: Token-efficient JSONL event stream capturing every tool invocation, model thought, and system response. The agent reads specific lines of its own past transcripts via `head`/`grep` on-demand.
4. **Hierarchical Knowledge Graph**: Integrates Tree-sitter AST symbol graphs and vector indexing for sub-millisecond retrieval of symbols and documentation.

---

### 3.2. Task Execution & Graph Workflow Runtime (ADK 2.0 Task API)
When an agent receives a complex prompt, it avoids immediate code synthesis. It decomposes work into an execution graph:
* **Workflow Runtime Nodes**: Graph nodes support conditional routing, parallel fan-out/fan-in, retry backoff, and nested sub-workflows.
* **Structured Delegation (Task API)**: Parent agents spawn isolated subagents (`researcher`, `debugger`, `implementer`) with bounded scopes, communicating over an asynchronous message bus rather than shared monolithic history.
* **Reactive Dispatch (Zero Polling)**: The agent yields control after dispatching async operations (e.g. background builds, test suites, or long-running timers), waking up purely upon receiving event messages.
* **Thought Signatures (`extra_content`)**: Reasoning and thinking tokens are attached to tool calls and replayed in subsequent turns to maintain mathematical continuity across multiple function invocations.

---

### 3.3. Session Lifecycles & State Persistence
* **State Ledger (`state.db`)**: All session variables, task DAG states, and branch checkpoints are persisted in SQLite WAL mode.
* **Survives Process Interrupts**: If a host machine or container restarts, the session is resumed seamlessly from the exact step index without lost context.
* **Isolated Workspaces**: Subagents can be launched in isolated workspaces (`Workspace: 'branch'` or `'share'`) to experiment without contaminating the parent project repository.

---

### 3.4. Continuous Self-Evolving & Autonomous Learning (`/learn`)
Google agents feature automated mechanisms for self-improvement and rule evolution:
1. **User Correction Ingestion**: When a user corrects an agent (e.g., "Always use `python3.13`" or "Never run bare command X"), the agent triggers a `/learn` sequence.
2. **Automated Rule Synthesis**: The correction is distilled into a concise behavioral constraint and written to `.agents/rules/` or `GEMINI.md`.
3. **Progressive Skill Promotion**: Newly synthesized procedural workflows that prove successful across multiple tasks are promoted into permanent reusable `.agents/skills/<name>/SKILL.md` packages with standardized YAML frontmatter.
4. **Deduplication & Drift Prevention**: Rules and skills are deduplicated by resolved inode/path and continuously validated against test benchmarks to prevent prompt drift.

---

## 4. Blueprint for Hermes Roadmap 4 Integration

| Google Component | Hermes Core Implementation Mapping |
| :--- | :--- |
| **Hierarchical Rule Discovery** | Port into `~/.hermes/` and `.agents/` dynamic discovery engine. |
| **Progressive Disclosure Skills** | Standardize `.hermes/skills/` with YAML `name + description` index. |
| **ADK Graph Task DAG** | Leverage `task_graph.py` SQLite WAL DAG for multi-agent fan-out. |
| **Artifact & Thought Anchors** | Implement `.hermes/plan.json` and persistent session artifacts. |
| **Self-Learning (`/learn`)** | Autonomous negative constraint capture & rule file synthesis in `.hermes/rules/`. |
