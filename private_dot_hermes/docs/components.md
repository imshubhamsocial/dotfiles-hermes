# Component Catalog & Ecosystem Registry

A structured directory of every open-source tool, library, package, and custom subsystem used in Hermes.

---

## 1. Upstream Open-Source Projects & Official Packages

| Component | Repository / Package | Purpose |
|---|---|---|
| **Hermes Agent** | [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent) | Upstream autonomous agent CLI, session manager, and Plugins v1 host |
| **Quorum** | [`berrzebb/quorum`](https://github.com/berrzebb/quorum) | Cross-model audit gate enforcing `edit → audit → agree → retro → commit` |
| **GEPA-Lite** | [`egmaminta/GEPA-Lite`](https://github.com/egmaminta/GEPA-Lite) | Lightweight Genetic-Pareto prompt and skill optimizer with natural language reflection |
| **llama.cpp** | [`ggml-org/llama.cpp`](https://github.com/ggml-org/llama.cpp) | High-performance C++ LLM inference engine with KV-cache slot persistence |
| **FastMCP** | [`jlowin/fastmcp`](https://github.com/jlowin/fastmcp) | High-speed Model Context Protocol transport for tool discovery and RPC |
| **nvidia-ml-py** | Official NVIDIA NVML | Python bindings to query real hardware GPU VRAM allocation directly from the driver |
| **Tree-Sitter** | `tree-sitter` + `tree-sitter-language-pack` | Polyglot incremental AST parser for Python, JS/TS, HTML, and C++ code graphs |
| **SQLModel / SQLite** | `sqlmodel` + `sqlite3` | Zero-VRAM persistent episodic memory engine with WAL journal mode |
| **SearXNG** | [`searxng/searxng`](https://github.com/searxng/searxng) | Local, keyless, privacy-respecting metasearch engine for web grounding |
| **Trafilatura** | `trafilatura` | High-efficiency web content extraction and HTML boilerplate stripping |
| **ddgs** | `ddgs` (DuckDuckGo Search) | Fast, keyless fallback search client |

---

## 2. Native Userland Plugins (`.hermes/plugins/`)

Hermes extends upstream functionality through idiomatic Plugins v1 modules located in `~/.hermes/plugins/` (tracked via `dotfiles-hermes` Chezmoi).

| Plugin | Capabilities & Purpose |
|---|---|
| **`adk_orchestrator`** | Google Agent Development Kit (ADK) Swarm engine, workflow composition, and agent delegation |
| **`agent_os`** | Standardized pre-commit planner, invariant assertions, and structured execution gates |
| **`branch_swapper`** | 2-Strike Tabu search and Git commit auto-rollback on recurring execution error loops |
| **`capability_guard`** | Role-based capability masks and tool security boundary enforcement |
| **`cog_verifier`** | Dual-agent adversarial verifier and second-brain retrieval vault |
| **`gepa_optimizer`** | Genetic-Pareto prompt and skill reflection optimizer hooked to session finalize |
| **`mcp_tools`** | FastMCP server providing Crawl4AI web extraction and ast-grep polyglot AST search |
| **`nemo_guardrails`** | NVIDIA NeMo Guardrails bridge enforcing formal Colang input, output, dialog, and loop rails |
| **`observer_gate`** | Autonomous observer lifecycle monitor with non-blocking execution tracing |
| **`openskills`** | OpenSkills progressive disclosure manager and skill manifest resolver |
| **`quorum_audit`** | Cross-model audit gate hooked to `pre_tool_call` (`edit → audit → agree → retro → commit`) |
| **`recirculation_adapter`** | System-2 prefill hook delivering reasoning lift via Lyapunov energy convergence |
| **`reflective_learner_adapter`** | TaskDAG trajectory recorder and SQLite WAL episodic memory learner hooked to `on_session_end` |
| **`symbol_index`** | Codebase Memory AST indexer and symbol graph server for fast AST lookups |
| **`synergy_bus_adapter`** | Asynchronous reactive event bus bridging session lifecycle events to subscribers |
| **`demo_validator`** | AST syntax validation gate for Python, JavaScript, and HTML artifacts |
| **`antigravity_bridge`** | Jules & Google DeepMind Antigravity 2.0 bridge with Magentic-One ledgers, thought signatures, and frontier API delegation |
| **`cua_bridge`** | Computer-Use Automation Driver (v0.21.0) desktop, AT-SPI tree, and GUI automation substrate |
| **`vision_sidecar`** | Lightweight multimodal vision client connecting to local port 8139 for image inspection without VRAM bloat |


