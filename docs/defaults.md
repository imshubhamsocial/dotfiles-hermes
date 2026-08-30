# Default Settings, Flags, & Enforced Invariants

This document lists all hardcoded invariants, default flags, timeouts, and hardware budgets enforced across the Hermes ecosystem.

---

## 1. Hardware & VRAM Limits (NVIDIA RTX 3050 6GB)

| Parameter | Enforced Default | Description | Enforcing File |
|---|---|---|---|
| **Hard VRAM Ceiling** | `4,812 MiB` | Absolute maximum VRAM footprint permitted | `context_window_guard.py` |
| **Safety Headroom Margin** | `150 MiB` | Unallocated buffer before triggering tier reduction | `context_window_guard.py` |
| **Model Weights Budget** | `2,540 MiB` | Fixed allocation for Gemma-4-E4B Q4_K_M GGUF | `context_window_guard.py` |
| **Context Slot Tier A** | `131,072 tokens` | Target context length (requires FlashAttention) | `context_window_guard.py` |
| **Context Slot Tier B** | `98,304 tokens` | Fallback tier if VRAM spikes | `context_window_guard.py` |
| **Context Slot Tier C** | `65,536 tokens` | Safe baseline operating tier (current active) | `config.yaml` |

---

## 2. Server Daemon Flags (`llama-server`)

| Flag | Enforced Value | Rationale |
|---|---|---|
| `--port` | `8138` | Dedicated port for local Hermes inference |
| `-np` | `2` | 2 parallel slots for dual-agent concurrent reasoning |
| `--cache-type-k` | `q4_0` | 4-bit quantized Key cache for 50% memory saving |
| `--cache-type-v` | `q4_0` | 4-bit quantized Value cache for 50% memory saving |
| `--flash-attn` | `on` | Enables flash attention kernels for long context |
| `--repeat-penalty`| `1.05` | Mild anti-loop penalty without corrupting code syntax |
| `--temp` | `1.0` | Balanced exploration for reasoning SLMs |
| `--top-p` | `0.95` | Nucleus sampling threshold |
| `--top-k` | `64` | Top-K candidate pool |

---

## 3. Tool Execution & Loop Timeouts

| Subsystem | Enforced Limit | Rationale |
|---|---|---|
| **Process Guard Timeout** | `300 seconds` | Maximum subprocess execution time |
| **Process Inactivity Timeout** | `45 seconds` | Triggers warning if a command produces no stdout/stderr |
| **Verification Timeout** | `120 seconds` | Maximum duration for full AST & test verification |
| **Max Tool Calls Per Turn**| `50` | Circuit breaker preventing runaway execution loops |
| **Tabu Rule (2-Strike)** | `2 consecutive failures`| Triggers Git commit rollback and branch pruning |
| **Loop Ceiling (3-Turn)** | `3 identical states` | Triggers Human-In-The-Loop (HiTL) escalation |

---

## 4. Token & Discovery Budgets

| Item | Enforced Budget | Rationale |
|---|---|---|
| **Tier-1 Plugin Summary Block** | $\le 150\text{ tokens}$ | Max context used for passive plugin discovery |
| **Single Plugin Summary Line** | $\le 20\text{ tokens}$ | Truncated one-line description per plugin |
| **Minimal System Prompt** | $\le 350\text{ tokens}$ | Lean bootstrap prompt for code-mode workers |
| **Karpathy Laws Block** | $\le 60\text{ tokens}$ | Invariant rules injected only for `@coder` subagent |
| **Single Skill Match** | $\le 200\text{ tokens}$ | Maximum tokens injected for L2/L3 skill instructions |
