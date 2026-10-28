# Implementation Task Checklist: Phase 38

- [ ] Execute `dream_rsi_workspace/compile_telemetry.py` to produce `lora_atropos_dpo.jsonl`.
- [ ] Run automated zero-contamination assertion check.
- [ ] Stop `llama-server` on Port 8138 (freeing 5,271.0 MiB VRAM).
- [ ] Train QLoRA adapter via Unsloth (`batch_size=1`, `grad_accum=4`, `max_seq_length=2048`).
- [ ] Merge adapter on CPU RAM and quantize to QAT q4_0 GGUF.
- [ ] Restart `llama-server` on Port 8138 and verify VRAM $\le 5,400.0\text{ MiB}$.
- [ ] Execute `phases/phase_38_offline_dream_rsi_dpo_distillation_and_merge/03_verify/contract.sh`.
