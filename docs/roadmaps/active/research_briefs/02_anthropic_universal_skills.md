# 02. Anthropic Universal Skills Catalog & Specification

> **Research Source Reference**: `https://github.com/anthropics/skills` (`agentskills.io`)  
> **Topic Category**: Agent Skills Architecture & Progressive Disclosure  
> **Sequential Index**: `02 / 11`

---

## 1. What the Reference Means

The `anthropics/skills` repository formalizes an open, standardized specification for packaging specialized procedural knowledge and executable tools into modular directory structures that AI agents can load dynamically on demand.

---

## 2. Core Architectural Mechanisms

1. **Standardized Directory Structure**:
   * `SKILL.md`: Mandatory entrypoint containing YAML frontmatter (`name`, `description`) and comprehensive markdown instructions.
   * `scripts/`: Deterministic executable code (Python, Bash) for executing actions.
   * `references/`: On-demand detailed documentation and knowledge bases.
   * `assets/` & `templates/`: Boilerplates, configuration snippets, and static resources.

2. **Progressive Disclosure Principle**:
   * Token economy is preserved by loading only the `name` and `description` into the agent's active system prompt at startup.
   * The full `SKILL.md` body and supporting reference documents are only fetched into context when the agent autonomously decides the skill is relevant.

---

## 3. Key Takeaways for Agent OS Design

* **Zero Context Window Bloat**: Keep the agent's baseline prompt lightweight by indexing skills declaratively.
* **Portable Skill Schema**: Adhere to the `name + description` YAML frontmatter open standard so skills are interchangeable across agent runtimes.
