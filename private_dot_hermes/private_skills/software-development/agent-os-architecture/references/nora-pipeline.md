---
id: "nora-pipeline"
title: "Normalized Low-Rank Adaptation (NoRA) Online Adaptation Pipeline"
category: ["peft", "lora", "nora", "continuous-learning"]
tags: ["peft", "nora", "adaptation", "weights"]
created_at: "2026-09-10T22:45:00.000000+00:00"
updated_at: "2026-09-10T22:45:00.000000+00:00"
status: "partial"
verified: true
---

# Normalized Low-Rank Adaptation (NoRA) Online Pipeline

## Overview
Normalized Low-Rank Adaptation (NoRA) addresses weight explosion and catastrophic forgetting in continuous on-device learning by applying Frobenius norm normalization across low-rank adaptation matrices:

$$W = W_0 + \gamma \cdot \frac{B A}{\|B A\|_F}$$

Where:
- $W_0$ is the frozen base model weights (`gemma-4-E4B-it-Q4_K_M.gguf`).
- $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$ are low-rank matrices ($r=16$).
- $\|BA\|_F$ is the Frobenius norm ensuring stable gradient scaling.
- $\gamma$ is a learnable scalar temperature.

## Four-Stage Online Pipeline

1. **Stage 1: Trajectory Signal Capture (ACTIVE)**
   - Wires `reflective_learner_adapter` via `on_session_end` hook.
   - Captures completed turns, AST-verified code modifications, and passing test outcomes.
   - Stores verifiable trajectories in `.hermes/training_buffer/samples.jsonl`.

2. **Stage 2: Gradient Accumulation (PLANNED)**
   - Accumulates loss on positive task milestones while pruning failed branches.

3. **Stage 3: Normalized Matrix Update (PLANNED)**
   - Computes low-rank delta with normalized update constraint to preserve base reasoning.

4. **Stage 4: Zero-Downtime Adapter Hot-Swap (BLOCKED)**
   - Currently blocked on llama.cpp dynamic LoRA reload API.
   - Requires dynamic adapter hot-reload without restarting `llama-server`.
