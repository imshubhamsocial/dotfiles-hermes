# Invariant Rule: Declarative Attention Scoping & LoopCD Contrastive Decision Gate

## 1. Context & Motivation
Per Declarative Attention (arXiv:2609.02737) and Apple LoopCD (arXiv:2610.02185), lightweight 4.5B models require explicit attention segmentation to prevent token pollution and contrastive logprob scoring to avoid reflexive heuristics.

## 2. Mandatory Operational Invariants

### Invariant 1: Attention Framing in `<|channel>thought`
When engaging in multi-turn reasoning or debugging complex tasks:
- **MANDATORY**: Structure reasoning using declarative attention tags:
  - `<global>`: The objective and verification check.
  - `<focus id="...">`: The specific function, class, or failing assertion under examination.
  - `<local>`: Candidate hypotheses and scratchpad math.
- **PROHIBITED**: Free-form unsegmented rambling that re-attends to entire past tool outputs.

### Invariant 2: Contrastive LoopCD Gate on High Uncertainty
- When faced with two or more plausible but conflicting repair strategies (e.g. superficial catch vs root-cause logic fix):
  - **MANDATORY**: Use the native OpenJev gate (`jev_decide`) to contrast Hypothesis A vs Hypothesis B using Port 8138 logprobs before applying code changes.
  - Never guess or apply speculative trial-and-error diffs when logprob calibration can discriminate the superior hypothesis.

### Invariant 3: Zero KV Cache Invalidation
- Always maintain stable prompt prefixes to allow Port 8138 `llama-server` to leverage slot caching (`--slot-save-path`).
