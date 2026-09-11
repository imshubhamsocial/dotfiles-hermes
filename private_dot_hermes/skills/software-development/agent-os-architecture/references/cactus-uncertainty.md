---
id: "cactus-uncertainty"
title: "Cactus Hybrid Uncertainty Detection & Autonomous Clarification Gate"
category: ["uncertainty", "safety", "logprobs", "hitl"]
tags: ["cactus", "shannon-entropy", "logprobs", "clarification", "hitl"]
source: "Academic NLP / Gemma Uncertainty Calibration"
era: "Era 3 & Era 5"
status: "active"
verified: true
---

# Cactus Hybrid Uncertainty Detection & Clarification Gate

## Problem: Overconfident Small Model Hallucinations
Small language models (4B) often execute irreversible, destructive mutations (such as deleting files or resetting repositories) even when highly uncertain about the actual user intent or environment state.

## Three-Signal Hybrid Calibration
Cactus synthesizes three complementary uncertainty vectors:
1. **Model Token Logprob Entropy**: Directly extracts top-$k$ logprobs from `llama-server` `/completion` endpoint and calculates Shannon entropy $H = -\sum p_i \ln p_i$.
2. **Linguistic Hedging**: Scans model thought chains and user queries for verbal uncertainty markers (`unsure`, `speculative`, `might break`) balanced against affirmative anchors (`verified`, `deterministic`).
3. **Action Blast Radius**: Assesses mutating tool severity and dangerous shell command patterns (`rm -rf`, `mkfs`, `kill -9`).

## Clarification Trigger
When the hybrid uncertainty metric exceeds 0.65, execution halts and the agent autonomously solicits targeted clarification from the user rather than guessing.
