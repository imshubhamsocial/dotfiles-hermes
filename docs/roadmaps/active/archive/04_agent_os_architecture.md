# 04. Agent OS: Spec-Driven Coding & Standards Substrate

> **Research Source Reference**: `https://github.com/buildermethods/agent-os`  
> **Topic Category**: Standards Injection & Spec-Driven Development  
> **Sequential Index**: `04 / 11`

---

## 1. What the Reference Means

`Agent-OS` (by Builder Methods) is an open-source system designed to capture, maintain, and deploy strict coding standards and formal product specifications across AI-assisted development workflows.

---

## 2. Core Architectural Mechanisms

1. **Two-Tier Standards Directory (`~/.agent-os/` & `.agent-os/`)**:
   * Global Developer Standards: User preferences, universal idioms, and workflow requirements.
   * Project-Level Standards: Specific architectural patterns, test assertions, lint rules, and stack constraints.
2. **Spec-Driven Pre-Implementation Phase**:
   * Enforces that formal design specifications (data shapes, UI layouts, and API interfaces) are agreed upon before an autonomous coding agent touches code.
3. **Explicit Standards Injection (`/inject-standards`)**:
   * Uses targeted command triggers to inject relevant standards into the agent's working memory at key lifecycle moments.

---

## 3. Key Takeaways for Agent OS Design

* **Formal Pre-Execution Specification**: Never allow an autonomous agent to generate complex multi-file code without first generating and validating a `.hermes/plan.json` interface specification.
* **Separation of Global vs Project Rules**: Maintain distinct rule layers for universal developer habits vs repository-specific architectures.
