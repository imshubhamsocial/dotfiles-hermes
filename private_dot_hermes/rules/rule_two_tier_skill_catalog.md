## Two-Tier Skill Catalog Hydration Protocol

This rule outlines the architectural standard for skill catalog documentation within the Hermes agent framework, ensuring fast context injection and maintaining a clean user experience.

### Tier 1 (Catalog Index) Invariant:
The primary skill listing description must be highly concise, adhering to a **strict maximum length of 40 characters**. This ensures that the agent can quickly parse and inject the skill's purpose into the working context without overwhelming the user or the model's prompt window. This serves as the *fast context injection* layer.

### Tier 2 (Full Skill Body) Protocol:
The full, detailed skill logic and documentation reside within the complete `SKILL.md` body. This comprehensive content is designed to be loaded **on demand** (e.g., via `skill_view(name)`) only when the user or system explicitly requests deep context, preventing bloat in the initial agent prompt.

### Hydration Flow:
1. **Default Context:** Agent context relies only on the Tier 1 (<= 40 char) description.
2. **Deep Dive:** When necessary, the agent uses `skill_view(name)` which triggers the loading of the full, comprehensive `SKILL.md` content.

**Goal:** To balance immediate agent usability (fast, short descriptions) with deep, detailed capability documentation (full body content).

**Constraint:** All new skills must adhere to this two-tier model to ensure maintainable context length and performance.