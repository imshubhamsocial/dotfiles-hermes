# 12. Google Agent Architecture, Workflows & Antigravity Metacognition

> **Research Source Reference**: `hermes/web/` (`google/adk-python`, `google-gemini/gemini-cli`, `googleapis/python-genai`, `antigravity-guide`)  
> **Topic Category**: Frontier Agent OS, Graph Decomposition & Reactive Dispatch  
> **Sequential Index**: `12 / 12`

---

## 1. Executive Overview: The Google Agent Paradigm

Google's frontier agent infrastructure (spanning **Google DeepMind**, **Google Antigravity (AGY)**, and the **Google Agent Development Kit (ADK 2.0)**) models an AI agent not as a single conversational loop, but as a **hierarchical, reactive state machine operating over an asynchronous execution graph**.

This document captures the complete architectural blueprint of how Google builds, decomposes, and executes autonomous agent workflows.

---

## 2. Metacognitive Lifecycle: From Prompt to Execution

Google decomposes user intent into real-world code through a strict **5-Stage Cognitive Pipeline**:

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
│ 5. Verification │ Closed-Loop HITL Confirmation + Artifact Persistence + Structured State Ledger │
└─────────────────┴────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Architectural Pillars

### 3.1. Hierarchical Rules & Contextual Precedence
Google agents never rely on a single massive system prompt. Instead, rules and guidelines are loaded dynamically via a **5-tier precedence hierarchy**:
1. **Workspace Project Rules** (Highest Priority: walking from CWD up to `.git` root).
2. **Declared Project Configurations** (`skills.json`, `plugins.json`).
3. **Global User Configuration** (`~/.gemini/config/` / `~/.config/`).
4. **Built-in System Tools & Skills** (Hardened built-ins mounted by name).
5. **Global Machine Defaults** (Lowest Priority).

**Deduplication Invariant**: Every rule file is tracked by its resolved absolute inode/path and injected strictly once per turn.

---

### 3.2. Progressive Disclosure & Token Preservation
To operate efficiently across high-complexity tasks without context window exhaustion:
* **Level 0 (Manifest Registration)**: Only the `name` and `description` YAML frontmatter of skills are kept in the agent's baseline system prompt.
* **Level 1 (On-Demand Activation)**: The full instruction body (`SKILL.md`) is loaded into context *only* when the model explicitly routes to that skill.
* **Level 2 (Auxiliary Execution)**: Sub-scripts (`scripts/`), references (`references/`), and templates (`templates/`) are read on demand via standard read tools.

---

### 3.3. Task Decomposition & Graph Workflow Runtime (ADK 2.0 Task API)
When an agent receives a complex prompt, it avoids immediate code synthesis. It decomposes work into an execution graph:
* **Workflow Runtime Nodes**: Graph nodes support conditional routing, parallel fan-out/fan-in, retry backoff, and nested sub-workflows.
* **Structured Delegation (Task API)**: Parent agents spawn isolated subagents (`researcher`, `debugger`, `implementer`) with bounded scopes, communicating over an asynchronous message bus rather than shared monolithic history.
* **State Management**: Execution state is tracked in a persistent state ledger (`state.db`), allowing sessions to survive restarts, crashes, or long-running async background tasks.

---

### 3.4. Reactive Dispatch & Thought Signature Propagation
For tool execution and reasoning integrity:
* **Thought Signatures (`extra_content`)**: Reasoning and thinking tokens are attached to tool calls and replayed in subsequent turns to maintain mathematical continuity across multiple function invocations.
* **Parallel Tool Invocation**: Tools can be invoked concurrently; results are batched and returned to the model simultaneously.
* **Reactive Wakeup**: The agent yields control after dispatching async operations (e.g. background builds or test runs), waking up only when background task completion events or subagent messages arrive.

---

### 3.5. Artifacts & Human-in-the-Loop (HITL) Gate
* **Artifact Subsystem**: Large reports, diffs, architectural plans, and interactive diagrams are persisted as structured Markdown artifacts (`<appDataDir>/brain/<id>/`) rather than cluttering conversation history.
* **Tool Confirmation Flow**: High-risk actions (file overwrites, git commits, destructive shell commands) trigger explicit confirmation gates or human-in-the-loop review nodes before execution.

---

## 4. Summary: Blueprint for Hermes Roadmap 4 Integration

| Google Component | Hermes Core Implementation Mapping |
| :--- | :--- |
| **Hierarchical Rule Discovery** | Port into `~/.hermes/` and `.agents/` dynamic discovery engine. |
| **Progressive Disclosure Skills** | Standardize `.hermes/skills/` with YAML `name + description` index. |
| **ADK Graph Task DAG** | Leverage `task_graph.py` SQLite WAL DAG for multi-agent fan-out. |
| **Artifact & Thought Anchors** | Implement `.hermes/plan.json` and persistent session artifacts. |
