# Cognitive Invariant Rule: Skill Authoring Standards
# File: .hermes/rules/rule_skill_authoring_invariants.md

This rule enforces specific structural constraints on all cognitive skills developed within the Hermes Agent OS. Adherence to these standards ensures maximum agent efficiency, reduced cognitive overhead, and maintainable documentation.

## ⚙️ Enforced Standards
### 1. Frontmatter Constraint (Ultra-Short Trigger)
The `description` field in the skill's YAML frontmatter must be an ultra-short trigger phrase, strictly under 40 characters.
- **Purpose**: Allows rapid recognition of the skill's intent during agent deliberation and avoids token bloat in the system prompt.
- **Example**: `description: 'Defend against SQL injection with parameters.'`
- **Constraint**: Must be concise and actionable, not descriptive.

### 2. Content Structure (Body vs. Frontmatter)
The full, detailed explanation, detailed instructions, prerequisites, and usage examples must reside exclusively in the markdown body of the `SKILL.md` file.
- **Frontmatter**: Reserved for meta-data (category, name, author, version, description).
- **Body**: Reserved for implementation logic, theory, and usage guidance.

### 3. Separation of Concerns (Rules vs. Skills)
Critical coding invariants, architectural rules, and system-level constraints that apply broadly across the codebase (e.g., VRAM limits, path invariants, zero-root pollution) must be defined and maintained in the `.hermes/rules/` directory. These should not be codified as "skills" unless they directly map to an executable task.
- **Why**: Rules define *how* the system works; skills define *what* the system can execute. This separation maintains cognitive clarity.