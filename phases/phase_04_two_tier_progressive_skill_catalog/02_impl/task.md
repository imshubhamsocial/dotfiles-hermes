# Phase 04: Two-Tier Progressive Skill Catalog — Implementation Checklist

> **Phase Directory**: `phase_04_two_tier_progressive_skill_catalog`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `.hermes/skills/karpathy-surgical-diff/SKILL.md`: shorten YAML `description` to <= 40 chars
  - `.hermes/skills/phase13-stair-navigation/SKILL.md`: shorten YAML `description` to <= 40 chars
  - `.hermes/skills/speckit-annealing/SKILL.md`: shorten YAML `description` to <= 40 chars
- Module Stems:
  - Skill YAML Frontmatter Validator
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. Descriptions exceeding 40 characters in `.hermes/skills/*/SKILL.md` violate the Van Clief Layer 3 strict YAML frontmatter invariant (`description <= 40 chars`, total frontmatter <= 200 bytes), leading to `skill_evaluator.py` dead ends and wasting L0 index tokens in Port 8138 KV cache.
2. Surgically shortening the descriptions of `karpathy-surgical-diff`, `phase13-stair-navigation`, and `speckit-annealing` to concise phrases under 40 characters ensures all 168 skills pass frontmatter validation with 0 dead ends while maintaining 0.0 MiB CUDA delta.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` / frontmatter checks and run `skill_evaluator.py` exit 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
