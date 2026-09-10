---
id: "declarative-attention"
title: "Declarative Attention & Attention Mask Control (KAIST/DeepMind)"
category: ["attention", "transformer", "context-compaction"]
tags: ["attention-mask", "context-rot", "kaist", "deepmind"]
created_at: "2026-09-10T22:45:00.000000+00:00"
updated_at: "2026-09-10T22:45:00.000000+00:00"
status: "partial"
verified: true
---

# Declarative Attention & Attention Mask Control

## Concept
Declarative Attention (KAIST / Google DeepMind 2026) empowers the language model to explicitly declare and manipulate its self-attention mask across conversational history. Rather than allowing past reasoning tokens, failed tool logs, or conversational debris to continuously distract the attention heads, the agent can programmatically isolate scratchpads and mask out obsolete tokens.

## Implementation & Architectural Ceiling

### Ideal Architecture
- Direct programmatic control over the attention matrix $A_{i,j} \in \{0, 1\}$ or bias matrix $B_{i,j} \in [-\infty, 0]$.
- Requires native PyTorch, TensorRT-LLM, or vLLM custom kernel integration with direct attention mask injection.

### Current Hermes Implementation
- Because Hermes runs on a 100% local `llama-server` (GGUF quantization via `llama.cpp`), internal attention layer matrices are not exposed via HTTP REST endpoints.
- Hermes emulates declarative attention through:
  1. **Slot Compaction**: Structured 5-slot context pruning in `recirculation_adapter`.
  2. **Two-Tier Specification Injection**: `agent_os` injects fresh engineering specifications into slot 3 while dropping noisy intermediate retries.
  3. **Demotion Rules**: Context rot demotion factor (0.85) to purge dead turn memories.

### Upgrade Path
- If `llama.cpp` upstream introduces token-level attention bias masks via `/completion` or `/chat/completions`, Hermes can activate true declarative attention without model fine-tuning.
