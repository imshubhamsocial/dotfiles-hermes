---
id: sparse_attention
title: "MoBA Block-Sparse Attention Kernel Specification"
version: 1
prerequisites: ["core_architecture"]
target_artifact: "generated/sparse_attention.py"
---

# MoBA Block-Sparse Attention Specification

## Overview
Durable specification for Mixture-of-Block-Attention (MoBA) dynamic routing and KV cache compression.

### Worked Example: Tensor Shape Transformation
- Input Q, K, V tensor shapes: [B, S, H] = [1, 8192, 16]
- Block decomposition: block_size = 256, total_blocks = 32
- Active top-k blocks: k = 4 active blocks
- Output compressed tensor shape: [1, 1024, 16]
- Compression ratio = 8192 / 1024 = 8.0x

### Reconciliation Anchors
ANCHOR: expr="(N * N) / (N * k * B)" vars={"N": 8192, "k": 4, "B": 256} expected=8.0
ANCHOR: expr="(active_blocks / total_blocks) * 100.0" vars={"active_blocks": 4, "total_blocks": 32} expected=12.5
