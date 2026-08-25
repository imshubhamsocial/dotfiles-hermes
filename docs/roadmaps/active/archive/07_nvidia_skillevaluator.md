# 07. NVIDIA SkillEvaluator: Multi-Tier Skill Lift Benchmarking

> **Research Source Reference**: `https://github.com/NVIDIA/SkillEvaluator`  
> **Topic Category**: Empirical Skill Lift Evaluation & A/B Trajectory Benchmarking  
> **Sequential Index**: `07 / 11`

---

## 1. What the Reference Means

`NVIDIA SkillEvaluator` is a 3-tier evaluation framework from the NVIDIA Verified Skills team designed to systematically measure whether an agent skill actually improves performance on real-world coding and planning tasks.

---

## 2. Core Architectural Mechanisms

1. **Tier 1 (Validation)**: Deterministic static analysis (schema compliance, security boundaries, linter checks, and PII inspection).
2. **Tier 2 (Deduplication)**: Embedding-based semantic similarity analysis to detect duplicate or conflicting guidance across the catalog.
3. **Tier 3 (Live A/B Trajectory Evaluation)**: Evaluates **Skill Lift** by executing identical synthetic coding tasks with and without the skill loaded, comparing completion rates, token consumption, and error rates.

---

## 3. Key Takeaways for Agent OS Design

* **Skill Lift Metric**: Never accept a new skill into the core catalog based on theory alone; measure empirical A/B lift against a clean baseline.
* **Trajectory Normalization**: Capture standardized execution trajectories for replay and deterministic grading.
