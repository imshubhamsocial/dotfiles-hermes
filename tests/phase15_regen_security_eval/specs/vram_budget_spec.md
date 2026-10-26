# Spec: VRAM Budget & Regenerative Architecture Scaffolding

## 1. Specification Overview
This specification formally models the VRAM allocation envelope on an NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB physical, 4,812 MiB maximum active allocation ceiling).

## 2. Symbolic SymPy Cost Expression

```python
import sympy as sp

# Symbolic Variables
vram_weights = sp.Symbol('vram_weights', positive=True)  # Model weights in MiB
vram_mtp = sp.Symbol('vram_mtp', positive=True)          # Speculative draft weights in MiB
n_layers = sp.Symbol('n_layers', integer=True, positive=True)
n_kv_heads = sp.Symbol('n_kv_heads', integer=True, positive=True)
d_head = sp.Symbol('d_head', integer=True, positive=True)
c_ctx = sp.Symbol('c_ctx', integer=True, positive=True)  # Tokens
b_quant = sp.Symbol('b_quant', positive=True)            # Bytes per KV element
delta_tool = sp.Symbol('delta_tool', nonnegative=True)   # GPU delta for toolchains

# Total VRAM Equation (in MiB)
kv_cache_bytes = 2 * n_layers * n_kv_heads * d_head * c_ctx * b_quant
kv_cache_mib = kv_cache_bytes / (1024 * 1024)
total_vram = vram_weights + vram_mtp + kv_cache_mib + delta_tool
```

## 3. Concrete Physical Constants (Gemma-4-E4B-it)
- `vram_weights = 2850.0` MiB (Q4_K_M)
- `vram_mtp = 420.0` MiB (Bartowski draft)
- `n_layers = 28`
- `n_kv_heads = 4`
- `d_head = 256`
- `b_quant = 0.5625` (Q4_0 KV cache)
- `c_ctx = 131072` (128K context)
- `delta_tool = 0.0` (FastEmbed & OpenViking 100% CPU isolated)
- Ceiling: `total_vram <= 4812.0` MiB

## 4. Security Invariant
All text ingested into memory or skills must be sanitized to block command execution (`$(...)`, backticks) and prompt injection overrides.
