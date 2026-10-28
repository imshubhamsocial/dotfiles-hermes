# Phase 38 Specification: Offline dreamRSI DPO Distillation & CPU GGUF Merge

## 1. Objective
Execute the offline 4-stage dreamRSI compiler to transform failure traces into de-identified DPO preference triples, train a QLoRA adapter using Unsloth ($\le 5,340.0\text{ MiB}$ VRAM), merge weights in 64 GB host system RAM ($0.0\text{ MiB}$ VRAM overhead), and quantize to `gemma-4-E4B-it-dpo-q4_0.gguf`.

## 2. Invariants
- Training must execute under the $\le 5,400.0\text{ MiB}$ VRAM ceiling. `llama-server` is stopped during training.
- Zero benchmark contamination: regex filter asserts 0 literal matches for benchmark identities.
- Negative policy anchors (Sample 57) must be included to maintain 100% compliance on prohibited actions.
- Production inference resumes on Port 8138 at exactly $5,271.0\text{ MiB}$ VRAM.
