# Substrate Port Registry & Architecture Map

> Layer 3 Reference Contract: Canonical Port Definitions for Hermes Agent OS.
> Rule: File must remain strictly under 200 lines.

---

## Active Daemon Port Table

| Port | Service / Daemon | Process / Technology | Binding & Interface | Resource Allocation |
| :--- | :--- | :--- | :--- | :--- |
| **8138** | GPU Inference Engine | `llama-server` (Gemma 4 E4B QAT) | `http://127.0.0.1:8138/v1` | Discrete NVIDIA RTX 3050 Laptop GPU (<= 5,400.0 MiB VRAM), CPU threads 0–5 |
| **8139** | CPU Representation Daemon | `hermes-embedding-cpu.service` (`embeddinggemma-2-Q8_0`) | `http://127.0.0.1:8139/v1` | 0.0 MiB GPU VRAM (`CUDA_VISIBLE_DEVICES=""`), CPU threads 6–11 |
| **8642** | Hermes Gateway Server | `gateway.platforms.api_server` (`hermes gateway`) | `http://127.0.0.1:8642/v1` | Host Network (Localhost only), `API_SERVER_KEY` authentication |
| **1933** | Hierarchical Memory Server | `openviking-server` (`TrieHI` Architecture) | `http://127.0.0.1:1933` | Host Memory & Disk (`.openviking/data`), 0.0 MiB GPU VRAM |

---

## Decommissioned Ports & Proxies

* **Port 1934 (Decommissioned)**: Legacy `mcp_ephemeral_bridge.py` proxy is permanently retired. Benchmark and client requests route directly to Port 8642.
