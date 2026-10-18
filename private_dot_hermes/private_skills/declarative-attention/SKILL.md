---
name: declarative-attention
description: "Declarative attention & LoopCD gate"
---

# Declarative Attention & LoopCD Decision Gate

This skill implements Declarative Attention (KAIST / Google DeepMind, arXiv:2609.02737) and LoopCD Contrastive Decoding (Apple, arXiv:2610.02185) natively inside Hermes Agent OS.

## 1. Declarative Attention (DA) Framing
In complex debugging or multi-turn reasoning, open-weight models suffer from attention drift across old tool outputs. 
Declarative Attention explicitly sections internal thought into 3 operational scopes:

1. `<global>`: Unchanging mission boundaries, verification command, and architectural invariants.
2. `<focus id="target_symbol">`: The exact AST symbol, file, or active failure being debugged right now. Ignores all unrelated files.
3. `<local>`: Scratchpad evaluation, candidate diffs, or ephemeral checks.

Example in `<|channel>thought`:
```text
<global>
Goal: Fix rate limiter race condition.
Verify: pytest tests/test_rate_limiter.py -q
</global>
<focus id="SlidingWindowLimiter.acquire">
Inspecting sliding window token calculation on lines 45-60.
</focus>
<local>
Evaluating Hypothesis A vs Hypothesis B.
</local>
```

## 2. LoopCD Contrastive Decision Gate (`jev_decide`)
When facing an ambiguous problem with multiple competing hypotheses (e.g. superficial catch vs true mathematical refactor), do not guess reflexively.

Invoke the OpenJev decision gate on Port 8138:
```python
jev_decide(
    premise="Test failure: SlidingWindowLimiter drops tokens under concurrent bursts.",
    hypothesis_a="Add a sleep(0.01) retry loop around acquire.",
    hypothesis_b="Update the atomic window timestamp boundary to use monotonic time and sliding bucket aggregation."
)
```
OpenJev performs a sub-50ms greedy logprob evaluation on local Port 8138, returning the calibrated winner (`prob > 0.50`).

## 3. KV Cache Slot Reuse
Ensure the stable system prompt prefix is preserved:
- Never alter system prompt headers or inject dynamic random seeds.
- Stable prefix reuse reaches $\ge 90\%$ KV cache hit rate in `llama-server`.
