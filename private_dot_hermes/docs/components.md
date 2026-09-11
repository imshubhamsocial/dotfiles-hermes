# Component Catalog & Ecosystem Registry

A structured directory of every open-source tool, library, package, and custom subsystem used in Hermes Agent OS.

---

## 1. Upstream Open-Source Projects & Official Frameworks

| Component | Repository / Package | Purpose |
|---|---|---|
| **Google ADK** | `google-adk` (Agent Development Kit 2.8+) | Directed Acyclic Graph (TaskDAG) multi-agent workflow orchestration |
| **Google A2A** | Google Agent2Agent Protocol Standard | Open standard for cross-agent collaboration, Agent Cards, and JSON-RPC 2.0 streaming |
| **Google Antigravity 2.0** | DeepMind Antigravity Core (`agy`) | Generative UI artifacts, Markdown alerts, Mermaid charts, Carousels, and HTML auxiliary pane |
| **NVIDIA NeMo Guardrails** | [`NVIDIA/NeMo-Guardrails`](https://github.com/NVIDIA/NeMo-Guardrails) | Event-driven Colang 2.0 execution rails, loop interception, and Shannon entropy monitoring |
| **Microsoft Agent Framework** | Microsoft MAF & Magentic-One | Dual Ledgers (Task & Progress) with 2-turn stall circuit breaker |
| **Meta AI Meta-Harness** | Meta FAIR (arXiv:2603.28052) | Outer-loop self-evolution engine with zero-regression test gates |
| **smolagents** | Hugging Face `smolagents` | Code-as-Action (`CodeAgent`) executing raw Python in sandbox vs nested JSON |
| **Aider** | [`paul-gauthier/aider`](https://github.com/paul-gauthier/aider) | Tree-sitter AST repo map and surgical SEARCH/REPLACE diff engine |
| **SWE-agent** | Princeton NLP `SWE-agent` | Observation windowing (head/tail 25 lines) to mitigate context rot |
| **FastMCP** | [`jlowin/fastmcp`](https://github.com/jlowin/fastmcp) | High-speed Model Context Protocol transport for tool discovery and RPC |
| **llama.cpp** | [`ggml-org/llama.cpp`](https://github.com/ggml-org/llama.cpp) | High-performance C++ inference engine with KV-cache slot persistence |
| **nvidia-ml-py** | Official NVIDIA NVML | Real-time GPU VRAM driver telemetry enforcing the <= 4,800 MiB ceiling |
| **FastEmbed** | `fastembed` (ONNX Runtime) | CPU-only dense vector embeddings (BGE-small / all-MiniLM) with zero VRAM impact |
| **Bubblewrap** | `bwrap` | Unprivileged Linux container sandboxing for untrusted code execution |

---

## 2. Master Native Plugins Roster (26 Active Plugins in `.hermes/plugins/`)

Hermes extends functionality through native Plugins v1 modules located in `~/.hermes/plugins/` (tracked via `dotfiles-hermes` Chezmoi).

| # | Plugin Name | Capabilities & Architectural Purpose |
|---|---|---|
| 1 | **`adk_orchestrator`** | Google ADK 2.8+ TaskDAG orchestration, subagent leasing, and Swarm handoffs |
| 2 | **`agent_os`** | Two-tier agent OS standards, structured plan decomposition, and specification generators |
| 3 | **`agentshield`** | ECC 4-layer defense: semantic intent classification, Shannon secret detection, AST blast radius, and Merkle SHA256 audit ledger |
| 4 | **`antigravity_bridge`** | Google AGY 2.0 Generative UI artifacts, Gemini thought signatures, progressive rule walker, Magentic-One ledgers, and A2A server |
| 5 | **`bpe_workspace`** | Belief-Progress-Experience state workspace preventing task drift across 30+ turns (EvoHarness-RL) |
| 6 | **`branch_swapper`** | Faraday 27B AI Director two-strike Tabu search and automatic git rollback on recurring error loops |
| 7 | **`cactus_uncertainty`** | Hybrid Shannon entropy and action gating engine for high-risk mutations |
| 8 | **`capability_guard`** | Role-based tool capability masks and permission isolation |
| 9 | **`cog_verifier`** | Dual-agent cognitive verifier and second-brain concept vault |
| 10 | **`context_budget_manager`** | 3-tier hybrid context router (32K HOT / 256K WARM / COLD) with output token budget guard |
| 11 | **`demo_validator`** | Generative UI HTML/CSS/JS validator powered by Biome and ast-grep |
| 12 | **`embedding_gemma`** | CPU-only FastEmbed runtime and CUDA offload prohibition guard |
| 13 | **`gepa_optimizer`** | Genetic-Pareto prompt and skill reflection optimizer hooked to session finalize |
| 14 | **`mcp_tools`** | FastMCP server providing Crawl4AI, ast-grep, Aider search-replace engine, and smolagents code actions |
| 15 | **`nemo_guardrails`** | NVIDIA NeMo Guardrails bridge enforcing formal Colang 2.0 input, output, dialog, and loop rails |
| 16 | **`observer_gate`** | Autonomous observer lifecycle monitor with 6-point AST pre-commit validation |
| 17 | **`openskills`** | Anthropic universal skills L0/L1/L2 progressive disclosure loader |
| 18 | **`quorum_audit`** | Cross-model audit gate hooked to pre-tool execution (`Author != Auditor`) |
| 19 | **`recirculation_adapter`** | System-2 prefill hook delivering reasoning lift via Lyapunov energy convergence |
| 20 | **`reflective_learner_adapter`**| TaskDAG trajectory recorder and SQLite WAL episodic memory learner hooked to session end |
| 21 | **`reward_scorer`** | Constitutional reward scorer and FrogNano [0.3, 0.7] learnability frontier filter |
| 22 | **`self_evolution`** | Spec-kit autonomous self-evolution engine and Meta-Harness outer loop |
| 23 | **`skill_intelligence`** | Thought signatures, superpowers registry, dynamic tool retrieval (DTDR), and A2A protocols |
| 24 | **`symbol_index`** | Codebase Memory AST indexer and Litho C4 architecture documentation generator |
| 25 | **`synergy_bus_adapter`** | Asynchronous reactive event bus bridging session lifecycle events to subscribers |
| 26 | **`trajectory_recorder`** | SQLite WAL trajectory recorder with SWE-agent observation windowing (50 lines max) |
