# Phase 22 Invariant: Spec-Kit 2.0 Autonomous Failure Cluster Annealing

> **Authority**: Google DeepMind & MIT *SMART Design Docs: Regenerative Software Engineering via Agentic Scaffolding* (arXiv:2609.05364), Live-SWE-agent  
> **Status**: Certified Operational Invariant (Phase 22)  
> **Hardware Boundary**: 0 MiB CUDA VRAM Delta (CPU SymPy & @ast-grep/cli, Total VRAM <= 4,812 MiB Bound)

---

## 1. AST Failure Signature Clustering

1. **Anti-Patch Debt Principle**:
   - Incremental patching on recurring runtime or unit test failures induces compounding code entropy ("Karpathy Patch Debt").
   - When a module incurs $\ge 2$ consecutive test failures or $\ge 3$ cumulative churn edits without resolving root-cause divergence, direct inline edits must halt immediately.
2. **Structural AST Diff Extraction**:
   - Parse error stack traces, failing AST node spans, and git patch hunks using `@ast-grep/cli` strictly on CPU RAM.
   - Compute AST structural failure signatures $\sigma(f)$ based on normalized AST syntax trees (abstracting variable names to capture structural patterns).
   - Group failure traces into clusters $\mathcal{C}_k$ based on tokenized structural similarity:
     $$\text{Sim}(\sigma_a, \sigma_b) = \frac{|\sigma_a \cap \sigma_b|}{|\sigma_a \cup \sigma_b|} \ge 0.75$$

---

## 2. Directed Specification DAGs (`specs/<module>.md`)

1. **Formal Specification Contracts**:
   - For every clustered failure domain, construct or update a formal design document in `specs/<module>.md`.
   - The specification must define:
     * Invariant interface contracts (types, signatures, preconditions, postconditions).
     * Ground-truth worked input/output examples.
     * Subsystem dependency Directed Acyclic Graph ($\mathcal{G}_{\text{spec}} = (\mathcal{V}, \mathcal{E})$).
2. **CPU SymPy Mathematical Hardware Verification**:
   - Prior to code generation, execute a formal symbolic proof using `sympy` on CPU RAM to ensure that the regenerated module's memory footprint and KV-cache demands comply with Law 2:
     $$V_{\text{weights}} + V_{\text{KV}}(c_{\text{ctx}}) + \Delta_{\text{module}} \le 4,812\text{ MiB}$$
   - Any proposed architecture exceeding the hardware ceiling must be rejected before synthesis.

---

## 3. Clean-Slate Topological Module Regeneration

1. **Kahn's Topological Order Enforcement**:
   - Code synthesis must never emit components in arbitrary or alphabetical order.
   - Dependencies declared in $\mathcal{G}_{\text{spec}}$ must be ordered using Kahn's algorithm:
     $$L \leftarrow \text{TopologicalSort}(\mathcal{G}_{\text{spec}})$$
   - Leaf interfaces and core primitives must be synthesized and tested before dependent orchestration layers.
2. **Patch Debt Annealing Metric**:
   - Clean-slate generation replaces tangled patch sequences with minimal canonical implementations.
   - Achieved patch debt reduction must be $\ge 60.0\%$:
     $$\text{DebtReduction} = 1.0 - \frac{\text{Lines}_{\text{clean}}}{\text{Lines}_{\text{churn}}} \ge 0.60$$

---

## 4. Hardware Safety & Cryptographic Receipt Sealing

1. **Zero CUDA VRAM Delta**:
   - AST parsing via `@ast-grep/cli`, graph analysis, and SymPy symbolic calculus execute 100% on CPU RAM at 0 MiB CUDA VRAM delta.
2. **Epistemic Receipt Closure**:
   - Clean-slate regenerated code must execute the machine verification command (`verify:`), returning exit code 0 and sealing `/tmp/hermes_verified_receipt.json`.
