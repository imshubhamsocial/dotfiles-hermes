---
id: "lora-adapter-manager"
title: "LoRA Adapter Manager & Dynamic Intent Routing Under 6GB VRAM Envelope"
category: ["peft", "lora", "vram", "routing"]
tags: ["lora", "qlora", "vram-envelope", "dynamic-routing", "adapters"]
source: "PEFT / HuggingFace / Awesome-Gemma"
era: "Era 3"
status: "active"
verified: true
---

# LoRA Adapter Manager & Dynamic Intent Routing

## Hardware Invariant: 6GB VRAM Envelope
On consumer hardware (e.g. NVIDIA RTX 3050 Laptop GPU with 6GB VRAM), running a 4B parameter model leaves approximately 800 MiB to 1.2 GiB of free VRAM. Attempting to load separate models for coding, math, and embeddings simultaneously causes immediate CUDA out-of-memory crashes.

## Solution: Low-Rank Adapter Swapping
- Base model weights (`gemma-4-E4B-it-Q4_K_M.gguf`) remain permanently resident in GPU VRAM.
- Specialized task capability is injected via lightweight low-rank adapter matrices ($r \le 16$, rank footprint < 50 MiB).
- Dynamic intent router inspects the user specification and selects the optimal adapter profile before initiating the prefill reasoning cycle.
