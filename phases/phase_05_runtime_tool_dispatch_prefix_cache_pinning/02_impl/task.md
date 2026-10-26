# Phase 05: Runtime Tool Dispatch & Prefix Cache Pinning — Implementation Checklist

> **Phase Directory**: `phase_05_runtime_tool_dispatch_prefix_cache_pinning`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `.local/bin/llama-server`: verification and configuration flags for `llama-server` on Port 8138 (`--keep 4096`, `-c 131072`, `-ctk q4_0`, `-ctv q4_0`, `-kvu`, `-np 1`, `--spec-type draft-mtp,ngram-map-k`, `--spec-draft-p-min 0.72`, `--slot-save-path ~/.hermes/cache/slots`).
  - `.config/systemd/user/hermes-llama-server.service`: systemd user daemon configuration.
- Module Stems:
  - Port 8138 llama-server inference daemon
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. llama-server running on Port 8138 with `--keep 4096`, `-c 131072`, `-ctk q4_0 -ctv q4_0 -kvu -np 1` pins the Layer 1 SOUL.md and AGENTS.md prompt prefix into the KV cache, preventing low-confidence BPE draft jitter and achieving deterministic execution within the <= 5,400.0 MiB VRAM envelope.
2. Managing the llama-server process via the systemd user service `hermes-llama-server.service` guarantees resilient process lifecycle, automatic restart, and systemd journal tracking while exposing the required `/health` endpoint on port 8138.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Deploy and enable `hermes-llama-server.service` user unit.
- [x] Step 4: Verify `curl -sf http://127.0.0.1:8138/health` responds with `{"status":"ok"}`.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
