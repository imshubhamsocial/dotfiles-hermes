# Phase 43 Implementation Task

1. Write `dream_rsi_workspace/compile_gdr24_dpo_pairs.py`.  
2. Execute compiler with `CUDA_VISIBLE_DEVICES=""` to generate sanitized `dream_rsi_workspace/lora_atropos_dpo.jsonl`.  
3. Verify zero benchmark literal leakage, valid JSONL schema, and physical VRAM <= 5,400.0 MiB.
