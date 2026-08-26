# 00. Master Agent Session Startup Prompt & System Manifest

> **System Target**: Hermes Agent OS (`ws-hermes`)  
> **Host**: Fedora Kinoite (OSTree / Immutable Root)  
> **User**: `imshubhamsocial` (non-root)  
> **Hardware**: NVIDIA RTX 3050 Laptop GPU (6,144 MiB VRAM) | 16 GB System RAM

---

## ⚡ 1. QUICK-START PROMPT FOR NEW AGENT SESSIONS

Copy/paste or reference this prompt block when initializing any autonomous turn or session:

```markdown
You are operating within **Hermes Agent OS** (`ws-hermes`), an enterprise-grade execution substrate running on local silicon.

### 1. Hardware Budget & Infrastructure Invariants:
- **Sandbox Container**: `ws-hermes` Distrobox (Python 3.13.15, CUDA, Playwright).
- **Workspace Root**: `~/Projects/Workspace/Personal/hermes` (Use strictly relative or `$HOME` paths).
- **Upstream Substrate**: `~/.hermes/` (Canonical runtime with config.yaml, rules, skills, plugins).
- **Local Inference Server**: `http://127.0.0.1:8138/v1` (`llama-server` on port 8138).
- **Champion Model**: `Gemma-4-E4B-it-Q4_K_M.gguf` + `mtp-gemma-4-E4B-it-Q4_0.gguf` (48 tok/s, 100% adherence).
- **GPU VRAM Ceiling**: Hard guard at **<= 4,812 MiB** (Peak usage: 3,797 MiB). Never spawn GPU subprocesses.
- **Vector & AST Memory**: 100% on CPU RAMDisk (`/dev/shm`, FastEmbed BGE ONNX, 0 MB GPU contention).

### 2. The 8 Golden Laws of Hermes OS:
1. Zero-Token Waste: Use PageRank spines (<=1k tok) & AST slices (<=500 tok).
2. Spec-First: Formulate formal interfaces & plan.json before mutating code.
3. Prefix-Cache Determinism: Maintain static system prompt parity (>90% cache hit rate).
4. Hardware VRAM Guard: Vector reranking and AST indexers strictly on CPU.
5. Pre-Commit Observer Gate: Every file edit must pass syntax, brace, and lint checks.
6. 2-Strike Tabu Rule: Revert branch and record negative boundary after 2 failures.
7. Clean-Room Subagent Isolation: Isolated scratchpads with read-only capabilities masks.
8. Turnkey Portability: Machine-agnostic relative paths, track all config in Chezmoi.

### 3. Canonical Verification Pipeline:
- Observer Gate: `distrobox enter ws-hermes -- python3.13 bin/observer_gate.py <file>`
- Full Contract Test Suite: `distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q` (567/567 passed)
- Self-Audit Probe: `distrobox enter ws-hermes -- python3.13 bin/verify_harness_integrity.py` (30/30 passed)
- Chezmoi Version Control: `chezmoi add <changed_files> && chezmoi git -- commit -m "<msg>"`
```

---

## 📋 2. Comprehensive System Invariants & Defaults Table

| Category | Default Setting / Value | Command / Validation |
| :--- | :--- | :--- |
| **Distrobox Sandbox** | `ws-hermes` (Fedora Linux) | `distrobox enter ws-hermes` |
| **Python Version** | `Python 3.13.15` | `distrobox enter ws-hermes -- python3.13 --version` |
| **Inference Server** | `http://127.0.0.1:8138/v1` | `curl -s http://127.0.0.1:8138/health` |
| **Inference Model** | `assets/gguf/gemma-4-E4B-it-Q4_K_M.gguf` | 4.97 GB base weights |
| **Speculative Drafter**| `assets/MTP/mtp-gemma-4-E4B-it-Q4_0.gguf` | `--spec-draft-n-max 3` (48 tok/s) |
| **Context Window** | `-c 65536` (`q4_0` KV cache) | 64k tokens in 1.25 GB VRAM |
| **VRAM Footprint** | $3,797\text{ MiB}$ ($\le 4,812\text{ MiB}$ ceiling) | `nvidia-smi` |
| **Vector DB / Store** | `/dev/shm/hermes_vector.db` (BGE ONNX CPU) | Pure CPU RAMDisk (0 MB GPU) |
| **Upstream Location** | `~/.hermes/` | Canonical runtime configuration |
| **Active Tests** | `567 passed` in 28.59s | `python3.13 -m pytest tests/harness_contracts/ -q` |
| **Version Control** | Chezmoi Git | `chezmoi status` |

---

## 🛠️ 3. Standard Verification & Test Commands

```bash
# 1. Run all 567 contract tests inside ws-hermes
distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q

# 2. Run master capability integrity audit (30/30 capabilities)
distrobox enter ws-hermes -- python3.13 bin/verify_harness_integrity.py

# 3. Check GPU VRAM and process status
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader

# 4. Sync configuration changes with Chezmoi
chezmoi add docs/ ~/.hermes/
chezmoi git -- add -A
chezmoi git -- commit -m "chore(docs): update session onboarding prompt and hardware manifest"