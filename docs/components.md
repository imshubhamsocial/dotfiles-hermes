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

## 2. Core First-Party Subsystems (`hermes_core`)

| Module | Purpose |
|---|---|
| **`quorum_gate.py`** | Implements Quorum cross-model consensus, blast radius calculation, and fitness gates |
| **`gepa_optimizer.py`** | Implements Pareto multi-objective optimization and reflective prompt mutation |
| **`context_window_guard.py`** | Enforces the 4,812 MiB VRAM ceiling using NVML bindings and selects safe context tiers |
| **`cog_verifier.py`** | Dual-agent verifier generating cryptographic verification receipts before pre-commit |
| **`draft_detective.py`** | Adversarial fact-checker auditing claimed filesystem paths, symbol references, and AST braces |
| **`vfs.py`** | High-speed in-memory POSIX Virtual File System with SHA-256 state snapshots |
| **`fastmcp.py`** | FastMCP server dispatcher with multi-hop JSON-RPC proxying and automatic unwrapping |
| **`database.py`** | SQLite connection factory enforcing WAL mode, schema migrations, and concurrency locks |
| **`process_guard.py`** | Non-blocking streaming process execution with CPU timeout and inactivity monitors |
| **`sandbox.py`** | Bubblewrap (`bwrap`) OS namespace jail for untrusted code execution |
| **`branch_swapper.py`** | 2-Strike Tabu search and Git commit auto-rollback on agent error loops |
