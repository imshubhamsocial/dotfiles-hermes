---
name: spec-driven-regen
description: Spec-driven regeneration from typed design documents.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec, design-doc, regeneration, typed-graphs, verification]
    category: software-development
---

# Spec-Driven Regeneration ("Design Docs Are All You Need")

Spec-Driven Regeneration grounds software construction in formal, typed specifications before emitting executable code. Code implementations are treated as ephemeral artifacts derived deterministically from the underlying design spec.

```
   [ 1. Literate Typed Spec ] (Contracts, Invariants, Type Graph)
                │
                ▼
   [ 2. Deterministic Derivation ] (Zero-wrapper code emission)
                │
                ▼
   [ 3. AST Drift Verification ] (ast-grep contract matching)
                │
                ▼
   [ 4. Spec-Driven Regen ] (Regenerate on drift, never patch blindly)
```

---

## 1. When to Use
Use Spec-Driven Regeneration when:
- Designing new subsystems, microservices, or complex state engines.
- Refactoring large codebases where implementation details frequently drift from architecture.
- Enforcing structural invariants that must be mathematically or logically verified before coding.

Do NOT use for one-line hotfixes, script typos, or exploratory throwaway prototypes.

---

## 2. Core Protocol: The Four Invariants

### Invariant 1: Typed Spec First (Literate Graph)
- Before writing implementation files, declare all types, data models, interfaces, and state transitions in a specification document or Python/TypeScript typed interface.
- Define pre-conditions, post-conditions, and failure modes explicitly.
- The spec is the authoritative source of truth; code is a derived projection.

### Invariant 2: Deterministic Derivation
- Generate code directly adhering to the typed contracts without inventing unverified helper abstractions or redundant custom wrappers.
- Use upstream packages or native platform plugins rather than reinventing glue logic.

### Invariant 3: AST Drift Detection
- Run structural AST checks (`ast-grep` or language parser) against the generated code to verify conformance to the spec.
- Check that exposed functions, return types, and argument signatures match the typed spec exactly.

### Invariant 4: Regeneration Over Blind Patching
- When architecture drifts or a breaking requirement emerges, update the design specification **first**.
- Regenerate the affected modules from the updated specification rather than accumulating ad-hoc patches on top of stale foundations.
- Run the full test suite to guarantee green regression status across the entire graph.
