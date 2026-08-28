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
