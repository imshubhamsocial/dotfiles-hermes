# Phase 49 Specification: EmbeddingGemma 2 Autonomous CPU Engine on Port 8139 (Cores 6-11, 0 MiB VRAM)

* **ICM Layer**: Orchestration & Dual-Model Parallelism (30% Tier)
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)
* **Input State**: 
  - Primary Gemma-4 model utilizes discrete NVIDIA RTX 3050 GPU (Port 8138, VRAM capped <= 5,400 MiB).
  - AMD Ryzen 5 7430U CPU logical cores 6–11 are idle during inference.
  - Context routing, classification, and RAG re-ranking require low-latency embeddings without competing for GPU VRAM.
* **Process**:
  1. Provision `hermes-embedding-cpu.service` in `~/.config/systemd/user/`:
     - Mask GPU devices: `CUDA_VISIBLE_DEVICES=""`, `GGML_CUDA_DISABLE=1`.
     - Bind CPU affinity: `CPUAffinity=6-11`, `Nice=5`.
     - Parameters: `--n-gpu-layers 0`, `--embeddings`, `--pooling mean`, `--port 8139`, `--threads 6`, `--threads-batch 6`, `-c 4096 -b 4096 -ub 4096`.
  2. Implement `scripts/hermes_embedding_cpu_client.py`:
     - 7 Task Instruction Prefixes (Classification, QuestionAnswering, CodeRetrieval, SearchQuery, FactChecking, SemanticSimilarity, Clustering).
     - Matryoshka Representation Learning (MRL) dimension truncation (768d -> 512d, 256d, 128d) with L2 re-normalization.
     - Standalone fallback evaluator ensuring zero-VRAM determinism.
* **Output Artifacts**:
  - `~/.config/systemd/user/hermes-embedding-cpu.service`
  - `scripts/hermes_embedding_cpu_client.py`
  - `/var/home/imshubhamsocial/.hermes/models/embeddinggemma-2-Q8_0.gguf` (stub/descriptor)
