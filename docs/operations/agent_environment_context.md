# Agent Context — Part 1 of 3: Environment & Migration State

> **Read order**: You are reading file **1/3**.
> Next → [`AGENT_OPERATIONS.md`](./AGENT_OPERATIONS.md) (how to run hermes)
> Then → [`AGENT_MILESTONES.md`](./AGENT_MILESTONES.md) (gaps & next steps)

This context was prepared by **Antigravity** (the host AI agent) after completing the Hermes migration. Read all three files before starting any work.

---

## 1. Environment Architecture

| Item | Value |
|------|-------|
| **Host OS** | Fedora Silverblue (immutable) |
| **Hermes container** | `ws-hermes` (Distrobox, `registry.fedoraproject.org/fedora-toolbox:latest`) |
| **Container home** | `/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes` |
| **GPU** | NVIDIA RTX 3050 6GB Laptop (CUDA available via `--nvidia` flag) |
| **Python** | `python3.13` (3.13.15) — use this, NOT system python3 |
| **Hermes version** | `v0.20.4` (2026.8.18) |
| **llama-server** | Running on port `8138` (CUDA-accelerated) |
| **Active model** | `gemma-4-4b` (default in all profiles) |

---

## 2. What Was Migrated (by Antigravity)

The entire Hermes runtime was decoupled from the legacy `ws-ai` container and the old `LLMs/Cluster` directory into `ws-hermes`. The new container has:

### ✅ DNF System Packages (all installed)
`gcc`, `gcc-c++`, `make`, `cmake`, `clang`, `ripgrep`, `fd-find`, `fzf`, `tree`, `htop`, `nvtop`, `python3.13`, `python3.13-devel`, `openssl-devel`, `libffi-devel`, `git`, `git-lfs`, `chezmoi`, `jq`, `curl`, `wget`

### ✅ Python Packages (271 packages via `python3.13 -m pip`)
- **Hermes**: `hermes-agent==0.20.4` (editable install from `~/.hermes/hermes-agent`)
- **LLM SDKs**: `anthropic==0.125.0`, `openai==2.24.0`, `ollama==0.6.2`
- **ML Stack**: `torch==2.13.0`, `transformers==5.15.1`, `accelerate`, `sentence-transformers==6.0.0`, `peft`, `safetensors`, `tokenizers`, `tiktoken`
- **Vector/Embeddings**: `faiss-cpu==1.15.0`, `fastembed==0.8.0`, `chromadb==1.5.9`, `qdrant-client==1.19.0`
- **MCP**: `mcp==1.29.1`, `fastmcp==3.4.7`, `mcp-agent-gate==0.1.1`, `mnemory==1.12`
- **CUDA runtime** (Python wheels): `nvidia-cuda-runtime`, `nvidia-cublas`, `nvidia-cuda-nvrtc`, `nvidia-nccl-cu13`
- **Web/API**: `fastapi`, `uvicorn`, `starlette`, `aiohttp`, `websockets`, `httpx`, `requests`
- **Tools**: `uv`, `psutil`, `pillow`, `pathspec`, `pydantic`, `ruamel.yaml`, `rich`, `typer`, `click`, `croniter`

### ✅ Binaries in `~/.local/bin/`
- `hermes` — upstream production launcher (`exec python3.13 -m hermes_cli.main "$@"`)
- `llama-server` — patched wrapper with dynamic CUDA/cuBLAS/NVRTC/NCCL LD_LIBRARY_PATH binding
- `llama-server.bin` — actual compiled binary (12KB, GNU 16.1.1 for Linux x86_64)

### ✅ Hermes Config (`~/.hermes/config.yaml`)
```yaml
database:
  journal_mode: wal
model:
  default: gemma-4-4b
  provider: custom
  base_url: http://127.0.0.1:8138/v1
  context_length: 65536
auxiliary:
  compression:
    context_length: 65536
terminal:
  backend: local
  cwd: .
  timeout: 180
  home_mode: auto
```

### ✅ Chezmoi Tracking (git repo at `~/.local/share/chezmoi`)
```
4852a7f Update tracked config.yaml with context_length and local model endpoints
d18a8eb Add patched llama-server wrapper with dynamic CUDA/cuBLAS/NVRTC/NCCL runtime bindings
d0c5f8e Sync normalized SOUL.md with isolated home path semantics
ef73626 Initial commit: Hermes core configurations, profiles, and launcher
```
Tracked: `~/.hermes/config.yaml`, `~/.hermes/SOUL.md`, `~/.hermes/desktop-plugins/`, `~/.hermes/hooks/`, `~/.hermes/plugins/`, `~/.local/bin/hermes`, `~/.local/bin/llama-server`

### ✅ Skills (at `~/.hermes/skills/`)
`apple`, `autonomous-ai-agents`, `creative`, `devops`, `email`, `github`, `media`, `mlops`, `note-taking`, `productivity`, `research`, `smart-home`, `social-media`, `software-development`

---

## 4. Reproducibility

Full manifests live alongside this file in the hermes project root:

| File | Purpose |
|------|---------|
| `packages.json` | DNF + Python dependency manifest |
| `setup.sh` | 1:1 automated setup script |
| `MIGRATION.md` | Full migration record |

---

> **Next** → [`AGENT_OPERATIONS.md`](./AGENT_OPERATIONS.md)
