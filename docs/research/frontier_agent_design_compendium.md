# Frontier Agent Architecture & Design Briefs

> A comprehensive compendium of 13 foundational research briefs covering system prompts, universal skills, persistent memory, cognitive architectures, and agent workflows.

---

# 01. Anthropic System Prompts & Persona Architecture

> **Research Source Reference**: `https://platform.claude.com/docs/en/release-notes/system-prompts/overview`  
> **Topic Category**: Metacognitive Prompting & Instruction Boundaries  
> **Sequential Index**: `01 / 11`

---

## 1. What the Reference Means

Anthropic publishes official versioned release notes for their production system prompts (used across Claude web and mobile interfaces). Unlike basic chat prompts, these system prompts define a **strict operational envelope** for frontier models, prioritizing:

1. **Temporal & Environmental Grounding**: Explicit date, location, and capability bounding at the very top of the prompt.
2. **Behavioral Invariants**: Formal rules for code formatting (e.g. strict markdown, avoiding conversational boilerplate before code blocks).
3. **Tool Call Formatting & Anti-Hallucination Boundaries**: Strict segregation between reasoning/thinking blocks and final user-facing responses.
4. **Non-Intrusive Guidance**: Giving the model clear refusal boundaries without sounding preachy or defensive.

---

## 2. Core Architectural Mechanisms

* **Explicit Slot Allocation**: System prompts are broken into orthogonal, immutable slots (Identity, Capability Scope, Behavioral Laws, Output Formatting).
* **Role-Based Instruction Isolation**: The model is instructed never to let user conversation override fundamental operating constraints.
* **Prompt Caching Compatibility**: Static instructions are structured at the front of the prompt to maximize KV-cache prefix hits across turns.

---

## 3. Key Takeaways for Agent OS Design

* **Modular System Prompt Hierarchy**: Instead of a monolithic prompt string, the system prompt must be assembled from version-controlled, cache-friendly blocks.
* **Separation of Reasoning vs. Emission**: Ensure tool arguments and thoughts are cleanly segmented from tool response text.
* **Zero Boilerplate Output**: Enforce immediate, direct tool execution without conversational preamble.


---

# 02. Anthropic Universal Skills Catalog & Specification

> **Research Source Reference**: `https://github.com/anthropics/skills` (`agentskills.io`)  
> **Topic Category**: Agent Skills Architecture & Progressive Disclosure  
> **Sequential Index**: `02 / 11`

---

## 1. What the Reference Means

The `anthropics/skills` repository formalizes an open, standardized specification for packaging specialized procedural knowledge and executable tools into modular directory structures that AI agents can load dynamically on demand.

---

## 2. Core Architectural Mechanisms

1. **Standardized Directory Structure**:
   * `SKILL.md`: Mandatory entrypoint containing YAML frontmatter (`name`, `description`) and comprehensive markdown instructions.
   * `scripts/`: Deterministic executable code (Python, Bash) for executing actions.
   * `references/`: On-demand detailed documentation and knowledge bases.
   * `assets/` & `templates/`: Boilerplates, configuration snippets, and static resources.

2. **Progressive Disclosure Principle**:
   * Token economy is preserved by loading only the `name` and `description` into the agent's active system prompt at startup.
   * The full `SKILL.md` body and supporting reference documents are only fetched into context when the agent autonomously decides the skill is relevant.

---

## 3. Key Takeaways for Agent OS Design

* **Zero Context Window Bloat**: Keep the agent's baseline prompt lightweight by indexing skills declaratively.
* **Portable Skill Schema**: Adhere to the `name + description` YAML frontmatter open standard so skills are interchangeable across agent runtimes.


---

# 03. OpenCode-Mem: Local Vector Episodic Memory

> **Research Source Reference**: `https://github.com/tickernelz/opencode-mem`  
> **Topic Category**: Persistent Context & Episodic Vector Storage  
> **Sequential Index**: `03 / 11`

---

## 1. What the Reference Means

`opencode-mem` is a persistent memory plugin for AI coding agents that addresses context amnesia across independent sessions. Instead of relying entirely on raw chat logs, it uses a local vector database to store and retrieve project facts, user conventions, and past execution failures.

---

## 2. Core Architectural Mechanisms

1. **Auto-Capture Subsystem**: Intercepts user corrections, architectural decisions, and bug-fix patterns during a session and indexes them into embeddings.
2. **Local Vector Database**: Stores semantic chunks locally without requiring external cloud databases or SaaS subscriptions.
3. **Tagged Subpath Exports**: Uses standardized tagging (`#convention`, `#architecture`, `#negative_constraint`) allowing third-party tools and plugins to query memory slices deterministically.

---

## 3. Key Takeaways for Agent OS Design

* **Cross-Session Retention**: Store learned negative constraints (e.g. "Do not use flag X on library Y") permanently across restarts.
* **Prompt Sieve Integration**: Query the vector database at turn initialization to retrieve only relevant past learnings rather than carrying full chat history.


---

# 04. Agent OS: Spec-Driven Coding & Standards Substrate

> **Research Source Reference**: `https://github.com/buildermethods/agent-os`  
> **Topic Category**: Standards Injection & Spec-Driven Development  
> **Sequential Index**: `04 / 11`

---

## 1. What the Reference Means

`Agent-OS` (by Builder Methods) is an open-source system designed to capture, maintain, and deploy strict coding standards and formal product specifications across AI-assisted development workflows.

---

## 2. Core Architectural Mechanisms

1. **Two-Tier Standards Directory (`~/.agent-os/` & `.agent-os/`)**:
   * Global Developer Standards: User preferences, universal idioms, and workflow requirements.
   * Project-Level Standards: Specific architectural patterns, test assertions, lint rules, and stack constraints.
2. **Spec-Driven Pre-Implementation Phase**:
   * Enforces that formal design specifications (data shapes, UI layouts, and API interfaces) are agreed upon before an autonomous coding agent touches code.
3. **Explicit Standards Injection (`/inject-standards`)**:
   * Uses targeted command triggers to inject relevant standards into the agent's working memory at key lifecycle moments.

---

## 3. Key Takeaways for Agent OS Design

* **Formal Pre-Execution Specification**: Never allow an autonomous agent to generate complex multi-file code without first generating and validating a `.hermes/plan.json` interface specification.
* **Separation of Global vs Project Rules**: Maintain distinct rule layers for universal developer habits vs repository-specific architectures.


---

# 05. COG Second Brain: Markdown-First Knowledge Management

> **Research Source Reference**: `https://github.com/huytieu/COG-second-brain`  
> **Topic Category**: Cognitive Graph, Markdown Vaults & Verifier Harness  
> **Sequential Index**: `05 / 11`

---

## 1. What the Reference Means

`COG-second-brain` (Cognition + Obsidian + Git) is an open-source knowledge management system built on the philosophy that a second brain should live in pure, portable markdown files organized and maintained by autonomous AI agents.

---

## 2. Core Architectural Mechanisms

1. **Zero Vendor Lock-In**: Complete avoidance of proprietary SaaS or complex database dependencies; all entities, memories, and daily logs are standard Markdown files version-controlled via Git.
2. **V-Model Closed-Loop Verification**: Employs a dual-agent pattern where a "worker agent" generates or organizes content, and a distinct "verifier agent" audits the output against ground truth.
3. **Task-Specific Micro-Skills**: Includes dozens of specialized procedural skills (`auto-research`, `knowledge-consolidation`, `daily-brief`) for structured knowledge consolidation.

---

## 3. Key Takeaways for Agent OS Design

* **Markdown as Primary Memory Format**: Ensure all persistent agent memories, plans, and ledgers remain human-readable, portable Markdown files.
* **Dual-Agent Verification**: Implement a separate validation pass for complex cognitive operations rather than having the generator grade itself.


---

# 06. Codebase Memory MCP: High-Performance Structural Graph

> **Research Source Reference**: `https://github.com/DeusData/codebase-memory-mcp`  
> **Topic Category**: Model Context Protocol & Tree-Sitter Codebase Graph  
> **Sequential Index**: `06 / 11`

---

## 1. What the Reference Means

`codebase-memory-mcp` is a native, single-binary Model Context Protocol (MCP) server that indexes codebases into a persistent structural knowledge graph (call chains, class hierarchies, HTTP endpoints, cross-service links) using Tree-sitter.

---

## 2. Core Architectural Mechanisms

1. **99% Token Reduction**: Instead of dumping entire files into the prompt, the agent queries the MCP server for exact structural relationships (e.g. `who_calls_function`, `find_subclasses`, `get_api_route`).
2. **Blazing Fast Local Indexing**: Single static binary with zero external runtime dependencies; indexes entire repositories in milliseconds.
3. **Multi-Language Tree-Sitter Support**: Native support across 150+ languages for exact AST parsing without LLM hallucinations.

---

## 3. Key Takeaways for Agent OS Design

* **Structural Graph Navigation over Raw Text Dumps**: Equip Hermes with Tree-sitter structural query tools to resolve symbol dependencies in sub-millisecond time.
* **Standardized MCP Interface**: Serve repository knowledge via standard Model Context Protocol endpoints for seamless inter-agent tool use.


---

# 07. NVIDIA SkillEvaluator: Multi-Tier Skill Lift Benchmarking

> **Research Source Reference**: `https://github.com/NVIDIA/SkillEvaluator`  
> **Topic Category**: Empirical Skill Lift Evaluation & A/B Trajectory Benchmarking  
> **Sequential Index**: `07 / 11`

---

## 1. What the Reference Means

`NVIDIA SkillEvaluator` is a 3-tier evaluation framework from the NVIDIA Verified Skills team designed to systematically measure whether an agent skill actually improves performance on real-world coding and planning tasks.

---

## 2. Core Architectural Mechanisms

1. **Tier 1 (Validation)**: Deterministic static analysis (schema compliance, security boundaries, linter checks, and PII inspection).
2. **Tier 2 (Deduplication)**: Embedding-based semantic similarity analysis to detect duplicate or conflicting guidance across the catalog.
3. **Tier 3 (Live A/B Trajectory Evaluation)**: Evaluates **Skill Lift** by executing identical synthetic coding tasks with and without the skill loaded, comparing completion rates, token consumption, and error rates.

---

## 3. Key Takeaways for Agent OS Design

* **Skill Lift Metric**: Never accept a new skill into the core catalog based on theory alone; measure empirical A/B lift against a clean baseline.
* **Trajectory Normalization**: Capture standardized execution trajectories for replay and deterministic grading.


---

# 08. Google DeepMind Recirculation: Inference-Time Dynamical Recurrence

> **Research Source Reference**: `arxiv:2608.17981` (*Google DeepMind, Aug 2026*)  
> **Topic Category**: Inference-Time Recurrence & Dynamical State Tracking  
> **Sequential Index**: `08 / 11`

---

## 1. What the Reference Means

The Google DeepMind paper *Recirculation* introduces a **training-free inference-time recurrence mechanism** for transformer models. By passing intermediate activations from deeper transformer layers back into shallower layers at subsequent timesteps, the model transforms into a dynamical system capable of tracking evolving belief states without mutating model parameters.

---

## 2. Core Architectural Mechanisms

1. **Training-Free Recurrence**: Operates directly on frozen foundation models (empirically proven on Gemma 3/4 architectures).
2. **Significant Reasoning Lift**: Demonstrates a **23% reduction in perplexity** and a **21% boost in multi-step reasoning accuracy (GSM8k)**.
3. **Zero Generation Latency Overhead**: Re-circulates activations during prefill passes, adding virtually zero latency during subsequent auto-regressive token generation.

---

## 3. Key Takeaways for Agent OS Design

* **System-2 Recurrent Thinking**: Use multi-pass activation feedback on complex code planning phases to eliminate hallucinations before emitting code.
* **Compatibility with Small Language Models**: Specifically powerful for dense 4B/8B parameter models where depth recurrence compensates for raw parameter scale.


---

# 09. OpenViking: Hierarchical Virtual Filesystem Context Database

> **Research Source Reference**: `https://github.com/volcengine/OpenViking`  
> **Topic Category**: Virtual Filesystem Context & Tiered Information Retrieval  
> **Sequential Index**: `09 / 11`

---

## 1. What the Reference Means

`OpenViking` (by Volcengine / ByteDance) is an open-source context database designed specifically for AI agents that replaces flat vector stores with a **hierarchical virtual filesystem paradigm** (`viking://`).

---

## 2. Core Architectural Mechanisms

1. **VFS Navigation Paradigm**: Agents query and navigate context using natural POSIX tools (`ls`, `tree`, `find`, `grep`) over structured knowledge hierarchies.
2. **3-Tier Context Representation**:
   * **L0 (Abstract)**: $\approx 100\text{ token}$ ultra-compact summaries for instant routing.
   * **L1 (Overview)**: $\approx 2,000\text{ token}$ structural outline for high-level planning.
   * **L2 (Full Detail)**: Complete unabridged documents loaded only when an exact symbol/file is modified.
3. **Directory Recursive Retrieval**: Combines semantic vector embeddings with tree traversal to prune unneeded context subtrees before retrieving content.

---

## 3. Key Takeaways for Agent OS Design

* **Hierarchical Token Scaling**: Structure agent knowledge and memory in L0/L1/L2 layers to maximize context efficiency.
* **Tool Familiarity**: Expose context retrieval through standard filesystem abstractions that code-generation models already excel at using.


---

# 10. Schema.org & Semantic Structured Data Protocols

> **Research Source Reference**: `https://www.semrush.com/blog/schema-markup` (`schema.org`)  
> **Topic Category**: Semantic Entity Grounding & Machine-Readable Artifacts  
> **Sequential Index**: `10 / 11`

---

## 1. What the Reference Means

Schema markup (JSON-LD structured data) provides an explicit machine-readable vocabulary for defining entities, relationships, dependencies, and actions. In the context of AI agent systems, schema markup acts as a **semantic grounding layer** that eliminates ambiguity for downstream LLM evaluators and search engines.

---

## 2. Core Architectural Mechanisms

1. **Entity Disambiguation**: Explicitly categorizes artifacts (e.g. `SoftwareSourceCode`, `APIReference`, `TaskSpecification`, `HowTo`) to prevent misclassification.
2. **Deterministic Entity Graphs**: Connects related components (e.g. `isBasedOn`, `targetProduct`, `author`, `codeRepository`) via standardized graph links.
3. **Grounding & Fact Verification**: Provides clear structured claims that automated verification gates can validate without fuzzy heuristics.

---

## 3. Key Takeaways for Agent OS Design

* **JSON-LD Artifact Metadata**: Embed structured schema metadata into all agent-generated documentation and architecture plans.
* **Grounding Anchor**: Use schema definitions to enable deterministic AST and verification gates.


---

# 11. Draft-Detective & Graft: Adversarial Verification & AST Refactoring

> **Research Source Reference**: `https://github.com/agencyenterprise/draft-detective` & `GRAFT AST Migration`  
> **Topic Category**: Adversarial Verification Gates & AST Code Refactoring  
> **Sequential Index**: `11 / 11`

---

## 1. What the Reference Means

* **Draft-Detective** (by Agency Enterprise / AE Studio): An automated verification framework built to adversarially cross-examine generated claims, technical specifications, and reference links against actual ground-truth files to flag hallucinations and unsupported assertions.
* **Graft (AST Refactoring & Migration)**: Automated structural code transformation and API dependency graph generation using Tree-sitter and compiler error feedback loops.

---

## 2. Core Architectural Mechanisms

1. **Adversarial Claim Verification**: Every statement or architectural assertion made by an agent is checked against real workspace files; unverified claims are flagged as violations.
2. **Compiler-Feedback Synthesis**: Validates code refactorings against real compiler / test runner outputs and feeds exact error diagnostics back to the repair loop.
3. **MCP & Plugin Accessibility**: Exposes audit results as structured Model Context Protocol tools for continuous quality gating.

---

## 3. Key Takeaways for Agent OS Design

* **Pre-Commit Adversarial Gate**: Run a dedicated verification pass that scans generated PR descriptions and documentation for factual alignment with actual code diffs.
* **AST-Aware Transformation**: Perform surgical code migrations using formal AST graphs rather than relying on unstructured text replacement.


---

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


---

# 13. Perplexity Local-First On-Device Agent Harness & OpenSkills

> **Research Source Reference**: `https://www.perplexity.ai/hub/blog/a-local-first-agent-for-private-and-cost-effective-knowledge-work` & `https://github.com/numman-ali/openskills`  
> **Topic Category**: On-Device SLM Co-Design, Context Sieve, On-Demand Skills & OpenSkills Universal Loader  
> **Sequential Index**: `13 / 13`

---

## 1. Core Philosophy: Co-Designing Harness for On-Device SLMs

Perplexity's research validates the exact core thesis we established: **general-purpose frontier harnesses (like default Hermes or Pi) fail on local devices because they assume massive context windows and infinite cloud compute.**

On-device models (e.g. Gemma 4B, Qwen 27B) technically advertise large context windows, but **empirically degrade in reasoning and instruction following as context expands**.

Therefore, the harness must be co-designed around 3 non-negotiable principles:
1. **Succinct Minimal Core**: Ultra-compact system prompt + minimal core tool primitives (read/write/eval).
2. **On-Demand Skills Lifecycle**: Skills load and unload dynamically throughout the trajectory rather than living permanently in context.
3. **Active Context Compaction & Summarization**: Stale conversational history is continuously compacted so the model stays within its peak cognitive window.

---

## 2. OpenSkills (`numman-ali/openskills`) Universal Package Paradigm

`openskills` provides a universal, agent-agnostic package loader for modular skills:
* **Standardized Registry**: Skills are version-controlled and installable across multiple agents (Claude Code, Antigravity, Hermes).
* **Dynamic Syncing**: Syncs installed skill packages directly into `.hermes/skills/` or `.claude/skills/`.
* **Zero Boilerplate Execution**: Exposes skills as modular CLI-driven tool packages.

---

## 3. Integration Takeaways for Hermes OS

* **Replace Raw Ad-Hoc Scripts**: Convert loose Python helper scripts into standardized, portable `openskills`-compliant packages.
* **Context Compaction Gate**: Implement automated trajectory summarizing when token count approaches threshold.
* **Tight 4B Envelope**: Never allow baseline working memory to exceed $2,500\text{ tokens}$ prior to skill injection.


---

