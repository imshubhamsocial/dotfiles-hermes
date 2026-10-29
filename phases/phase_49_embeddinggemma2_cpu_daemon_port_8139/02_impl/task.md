# Implementation Task Checklist: Phase 49

## 1. Concrete Symbol Targets
- `EmbeddingGemmaCPUClient` in `scripts/hermes_embedding_cpu_client.py`
- `TASK_INSTRUCTION_PREFIXES` in `scripts/hermes_embedding_cpu_client.py`
- `apply_matryoshka_truncation` in `scripts/hermes_embedding_cpu_client.py`
- `hermes-embedding-cpu.service` in `~/.config/systemd/user/hermes-embedding-cpu.service`
- `03_verify/contract.sh` in `phases/phase_49_embeddinggemma2_cpu_daemon_port_8139/03_verify/contract.sh`

## 2. Causal Hypotheses
- **H1 (Zero-VRAM Parallelism)**: Running EmbeddingGemma 2 strictly on CPU cores 6–11 with `-ngl 0` and `CUDA_VISIBLE_DEVICES=""` consumes exactly 0.0 MiB of GPU VRAM, leaving the entire 5,400 MiB ceiling available for the primary Gemma-4 model.
- **H2 (MRL Dimension Scaling)**: Truncating 768d vectors to 256d preserves >96% of code/retrieval search accuracy while reducing memory transfer overhead and storage footprint by 3x.
- **H3 (Task-Prefix Calibration)**: Formatting queries using the 7 canonical instruction prefixes aligns embeddings with the target task distribution (classification, code retrieval, QA, fact-checking).

## 3. Implementation Steps
- [x] Create systemd user unit `~/.config/systemd/user/hermes-embedding-cpu.service` pinned to cores 6–11 with 0 GPU VRAM.
- [x] Create `scripts/hermes_embedding_cpu_client.py` implementing `EmbeddingGemmaCPUClient` with MRL and 7 task prefixes.
- [x] Implement and execute `03_verify/contract.sh` validating unit service syntax, MRL normalization, cosine similarity, and zero VRAM impact.
