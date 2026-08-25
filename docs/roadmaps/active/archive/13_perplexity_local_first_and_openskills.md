# 13. Perplexity Local-First On-Device Agent Harness & OpenSkills

> **Research Source Reference**: `https://www.perplexity.ai/hub/blog/a-local-first-agent-for-private-and-cost-effective-knowledge-work` & `https://github.com/numman-ali/openskills`  
> **Topic Category**: On-Device SLM Co-Design, Context Sieve, On-Demand Skills & OpenSkills Universal Loader  
> **Sequential Index**: `13 / 13`

---

## 1. Core Philosophy: Co-Designing Harness for On-Device SLMs

Perplexity's research validates the exact core thesis we established: **general-purpose frontier harnesses (like default Hermes or Pi) fail on local devices because they assume massive context windows and infinite cloud compute.**

On-device models (e.g. Gemma 4B, Qwen 27B) technically advertise large context windows, but **empirically degrade in reasoning and instruction following as context expands**.

Therefore, the harness must be co-designed around 3 non-negotiable principles:
1. **Succinct Minimal Core**: Ultra-compact system prompt + minimal core tool primitives (read/write/eval).
2. **On-Demand Skills Lifecycle**: Skills load and unload dynamically throughout the trajectory rather than living permanently in context.
3. **Active Context Compaction & Summarization**: Stale conversational history is continuously compacted so the model stays within its peak cognitive window.

---

## 2. OpenSkills (`numman-ali/openskills`) Universal Package Paradigm

`openskills` provides a universal, agent-agnostic package loader for modular skills:
* **Standardized Registry**: Skills are version-controlled and installable across multiple agents (Claude Code, Antigravity, Hermes).
* **Dynamic Syncing**: Syncs installed skill packages directly into `.hermes/skills/` or `.claude/skills/`.
* **Zero Boilerplate Execution**: Exposes skills as modular CLI-driven tool packages.

---

## 3. Integration Takeaways for Hermes OS

* **Replace Raw Ad-Hoc Scripts**: Convert loose Python helper scripts into standardized, portable `openskills`-compliant packages.
* **Context Compaction Gate**: Implement automated trajectory summarizing when token count approaches threshold.
* **Tight 4B Envelope**: Never allow baseline working memory to exceed $2,500\text{ tokens}$ prior to skill injection.
