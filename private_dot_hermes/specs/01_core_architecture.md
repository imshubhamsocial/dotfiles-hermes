---
id: core_architecture
title: "Hermes Agent OS Core Substrate Specification"
version: 1
prerequisites: []
target_artifact: "generated/core_architecture.py"
---

# Core Architecture Specification

## Overview
Durable specification defining root Agent OS primitives, state initialization, and hardware boundary invariants.

### Worked Example: State Vector Normalization
- Given an unnormalized state vector v of dimension 64
- Step 1: Compute Euclidean norm ||v||_2 = sqrt(sum(v_i^2))
- Step 2: Scale vector v_norm = v / ||v||_2
- Step 3: Assert ||v_norm||_2 == 1.0 within numerical epsilon

### Reconciliation Anchors
ANCHOR: expr="(x**2 + y**2)**0.5" vars={"x": 3.0, "y": 4.0} expected=5.0
ANCHOR: expr="vram_limit - allocated" vars={"vram_limit": 4812.0, "allocated": 1024.0} expected=3788.0
