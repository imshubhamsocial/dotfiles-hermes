# Phase 35 Specification: Domain DB Tool Precedence Skill Deployment

## 1. Objective
Deploy the 100% domain-general skill `domain_db_tool_precedence/SKILL.md` into `~/.hermes/skills/` to codify the Exhaustion Invariant and eliminate the Escalation Attractor without benchmark overfitting.

## 2. Invariants
- Skill must follow the agentskills.io format (YAML frontmatter + Markdown specification).
- Skill must specify the parameter resolution hierarchy: Tier 1 (User ID) -> Tier 2 (Email) -> Tier 3 (Name + ZIP) -> Tier 4 (Order ID) -> Tier 5 (Escalation).
- Zero benchmark-specific literals (e.g., "Ivan", "Isabella", "32286", "W4284542") are permitted.
- Contamination assertion regex must return 0 matches.
