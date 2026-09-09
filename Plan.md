# Master Plan & Architecture Ingestion Register

## Ingested References

### 1. Mythos-Harness & "Finish-First" Agent Loop
- **Sources**:
  - X Post: https://x.com/DanKornas/status/2096055546403012908
  - GitHub Repository: https://github.com/Magma1321/mythos-agent-pipe
- **Author / Originator**: Dan Kornas (@DanKornas) / Magma1321
- **Overview & Core Thesis**:
  > *"Agent workflows don’t fail at the prompt. They fail in the gap between execution and verification."*
  
  Mythos-Harness presents a four-phase "finish-first" agent loop optimized for high-reasoning models (Claude Opus 4.7). It structures the software lifecycle into an assembly line where the agent plans, executes, verifies against strict constraints, and ships finished artifacts autonomously without babysitting or manual intervention.

- **Four-Phase "Finish-First" Lifecycle**:
  1. **Plan Phase**:
     - Decomposes high-level natural language objectives into modular, actionable sub-tasks.
     - Maps explicit input/output formats, dependencies, and strict pass/fail success criteria per task.
  2. **Execute Phase**:
     - Executes tasks in dependency order with full session context retention.
     - Captures operational metrics, timestamps, filesystem mutations, and API calls.
  3. **Verify Phase & Remediation Loop (Verification Grid)**:
     - Automated validation including:
       - **Structure Check**: File and folder layout validation against required blueprints.
       - **Syntax Lint**: Language-specific static analysis and syntax validation.
       - **Type Coherence**: Variable types and function signatures matched against declarations.
       - **Test Execution**: Unit test execution and pass/fail gate checks.
       - **Performance Thresholds**: Execution time and memory profiling to detect outliers.
     - **Remediation Loop**: On test or constraint failure, detailed error diagnostics are routed into an automated re-execution fix cycle up to a defined retry limit.
  4. **Ship Phase**:
     - Bundles verified outputs into deliverables: Git commits, zip archives, staging deployments, webhooks, or notification channels.

- **System Architecture**:
  - **Orchestrator**: Coordinates phases, handles state progression, and drives error recovery.
  - **Context Engine**: Maintains persistent working memory across sessions (local filesystem, Redis, PostgreSQL) to allow seamless resumption of interrupted workflows without re-planning.
  - **Verification Grid**: Modular, extensible plugin architecture (`VerificationModule` subclasses) for domain-specific contract testing.
  - **Pipeline Adapter**: Adapts completed artifacts into external delivery formats (Git, S3, webhooks).

### 2. Anthropic's Agent Engineering Playbook (Full Breakdown by CyrilXBT)
- **Source**: https://x.com/cyrilXBT/status/2096253035563426134
- **Author / Originator**: CyrilXBT (@cyrilXBT) tracing Anthropic's internal engineering blog, Claude Agent SDK, and prompting documentation.
- **Core Thesis**:
  > *"Build the structure that makes an agent's behavior verifiable and its progress durable, rather than trusting a smarter model to compensate for the absence of that structure. The harness, the verification discipline, the memory system, matter more as models get more capable and more autonomous, not less."*

- **Key Principles & Architectural Patterns**:
  1. **Solving Multi-Session Amnesia via Durable Handoffs**:
     - Multi-session agents have no memory by default ("engineers on separate shifts who remember nothing from the shift before").
     - **Anthropic SDK Two-Role Pattern**: An *Initializer Agent* sets up the environment and plans once; a *Coding Agent* makes incremental progress per session and leaves behind clear, durable artifacts (notes, file states, execution logs of what was tried and what happened) so the next session resumes seamlessly without rediscovering context.
  2. **Separate The Brain From The Hands**:
     - Reasoning happens in one place; tool execution occurs inside an isolated sandbox.
     - Delivers faster time-to-first-token (TTFT) and clear fault isolation (distinguishing cognitive reasoning errors from execution sandbox failures).
  3. **Server-Side Execution & Fine-Grained Step Logging**:
     - Decouple agent processes from local laptop terminal sessions.
     - Log every single action and state transition in real-time. Enables crash recovery by replaying context from the log rather than re-running from zero.
  4. **Make Failure Cheap**:
     - Treat failures as normal, expected events to recover from at minimal cost, rather than exceptions to prevent at all costs.
     - Retry dead sandboxes cheaply; replay lost state from execution logs.
  5. **Turn Yesterday's Logs Into Tomorrow's Memory ("Dreaming")**:
     - Offline/off-peak batch pass processes accumulated session logs into new skills and permanent memory cards.
     - Memory files must include a scannable one-line summary at the top so future sessions can judge relevance instantly without ingesting full files into context.
  6. **Maker vs. Verifier Separation ("Never Let It Grade Its Own Work")**:
     - The cognitive perspective that produced a solution has structural blind spots and skews falsely positive.
     - Architectural separation: Separate the agent producing work from the agent evaluating it.
     - The evaluator must have access to independent ground-truth evidence that the maker didn't generate (raw test outputs, requirement specs, external verification checks).
  7. **Conservative Multi-Agent Scaling**:
     - Token economics: Single agent consumes $\approx 4\times$ normal chat tokens; multi-agent systems consume $\approx 15\times$.
     - Multi-agent outperforms single agents (e.g., $+90.2\%$ on internal research evaluations) *only* when the task structurally fans out into independent, parallel inquiries.
     - Sequential tasks get zero benefit from multi-agent setups—it only multiplies cost. Rule: Start with a single agent by default.
  8. **Disciplined Root Instructions (CLAUDE.md / System Instructions)**:
     - Mental model: "A brilliant new employee with amnesia."
     - Target length: Under 200 lines (disciplined teams $\approx 60$ lines). Include only universal instructions relevant to nearly every session.
     - Reserve explicit emphasis markers (`IMPORTANT`, `YOU MUST`) strictly for rare non-negotiables to avoid signal dilution.
  9. **The Grep Decision (Simplicity over Complexity)**:
     - Claude Code team tested vector search/embeddings vs. plain `grep` and `glob` for codebase navigation: plain grep/glob "outperformed everything. By a lot."
     - Exact syntax, symbol names, and import paths require literal matching; semantic vector search surfaces plausible but misleading distractor files.
  10. **Evidence-Grounded Progress Audit**:
      - Solves the documented failure mode where agents prematurely claim steps are finished.
      - Tested prompt contract:
        > *"Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for. If something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output. If a step was skipped, state that. When something is done and verified, state it plainly without hedging."*
      - The specific word **"audit"** statistically triggers stricter self-checking than soft requests like "be careful" or "double check".
  11. **Progressive Disclosure for Skills**:
      - Prevent root context bloat by packaging situational procedures, domain procedures, and specific tool protocols into modular skills.
      - Load deep context JIT (just-in-time) only when task keywords or AST file touches explicitly require it.
