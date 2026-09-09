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

### 3. Looped Transformers & Recurrent Depth (Sebastian Raschka on OpenAI Astra, Nanbeige 4.2, Mixture-of-Recursions)
- **Sources**:
  - X Post: https://x.com/rasbt/status/2095141254958858496
  - YouTube Video: https://www.youtube.com/watch?v=KT4n-z_4QJU
- **Author / Originator**: Sebastian Raschka (@rasbt)
- **Core Thesis & Background**:
  - Explores recurrent depth and looped transformer architectures in light of the Nanbeige 4.2 release and architectural discussions surrounding OpenAI Astra.
  - Investigates how weight-tied layer reuse provides parameter efficiency and dynamic compute scaling without expanding memory/VRAM requirements.

- **Key Principles & Architectural Insights**:
  1. **Looped Transformers & Layer Weight Reuse**:
     - Instead of stacking $N$ distinct physical transformer layers, a smaller stack of $L$ layers is reused across multiple sequential passes ($R$ loops) per token step (effective depth $= L \times R$).
     - Example: Nanbeige 4.2-3B builds a 22-layer physical stack and runs it twice ($R=2$), behaving with the expressive capacity of a 44-layer network while maintaining a 3B parameter footprint.
  2. **Memory Footprint vs. Compute Trade-offs**:
     - Parameter count, disk storage, and GPU VRAM footprint remain strictly fixed to the base layer count.
     - Token efficiency: A looped transformer achieves $\approx 75\%$ of the performance/token efficiency of a model trained with fully independent weights of equivalent depth.
     - FLOP cost: Inference FLOPs scale linearly with the loop count ($\approx 2\times$ compute for 2 passes), trading latency/compute for dramatic memory savings and edge/VRAM viability.
     - Diminishing returns: Reusing the stack more than twice ($R > 2$) yields steep diminishing returns and significantly slower training convergence.
  3. **Mixture-of-Recursions (Adaptive Token Compute)**:
     - Advanced architecture presented at NeurIPS adding a dynamic, learned router to looped transformers.
     - Rather than forcing all tokens through uniform recurrent passes, the model dynamically routes "easy" tokens after a single pass and loops "difficult" tokens through multiple passes.
     - Achieves variable per-token compute allocation in latent representation space.
  4. **Latent Representation vs. Chain-of-Thought (CoT) Reasoning**:
     - Recurrent depth adds internal latent compute before token emission.
     - While it does not eliminate the necessity of explicit chain-of-thought tokens for multi-step reasoning, latent recurrence allows deeper feature refinement per token, potentially shrinking the number of verbose reasoning tokens required to solve complex logic steps.

### 4. Google Fairwind Program & Autonomous Security Harness (Gemini 3.8 Flash Cyber & CodeMender)
- **Sources**:
  - X Post: https://x.com/sundarpichai/status/2095184464800526655
  - Google Blog: https://blog.google/innovation-and-ai/technology/safety-security/fairwind-program/
- **Author / Originator**: Sundar Pichai (@sundarpichai) / Four Flynn (VP Security & Privacy, Google)
- **Core Thesis & Defender Dilemma**:
  > *"Spotting weaknesses creates awareness and fear; autonomously finding and fixing vulnerabilities delivers security. The defender’s edge comes from shrinking the time between detecting a flaw and patching it."*
  
  Defenders historically faced an acute trade-off: deploy massive frontier models (prohibitively expensive, complex enterprise context governance) or small open-weight models (inadequate reasoning for deep exploit remediation, requiring custom harness engineering from scratch). Fairwind bridges this via specialized domain-tuned small models coupled with targeted agentic scaffolding.

- **System Architecture & Key Capabilities**:
  1. **Gemini 3.8 Flash Cyber**:
     - Specialized cybersecurity model tuned for vulnerability identification, verification, and code-level patch synthesis.
     - Benchmark performance: **86.2% on CyberGym**.
     - Real-world efficacy: **2.6× more effective** at producing correct patches for Chrome security vulnerabilities compared to larger commercial general-purpose models.
     - Operates at high inference speed and low cost profile characteristic of the Flash model tier.
  2. **CodeMender Agentic Harness**:
     - Pairs the model with an automated harness that executes the entire vulnerability lifecycle: finding flaws, validating root causes, drafting patches, and running regression tests to verify fixes before merging.
     - Operates directly inside an organization's secure cloud perimeter.
     - Compresses vulnerability remediation timelines from weeks of manual developer triage down to minutes of autonomous, verified patch generation.
  3. **Fairwind Gated Distribution Program**:
     - Restricted access program deployed across 650+ vetted global partners (national cyber authorities, critical infrastructure operators across energy/healthcare/finance, and core open-source foundation maintainers).
     - Mitigates dual-use weaponization risks by enforcing strict operational boundaries (restricted to incident response, pentest teams, MFA enforcement, and secure cloud runtime sandboxes).

### 5. Generative UI & Visual Artifact Architecture (Google Antigravity)
- **Source**: https://antigravity.google/blog/visualizing-with-the-help-of-antigravity
- **Author / Originator**: Google Antigravity Team
- **Core Thesis**:
  > *"While text interfaces are great for everyday development, they do not always convey complex architectural relationships or content in ways that are easily digestible. With Generative UI and visual tooling, agents can create, render, and iterate on rich visual components, dynamic dashboards, interactive artifacts, and design mockups in real time."*

- **Key Architectural Principles & Capabilities**:
  1. **Beyond Text / TUI Limitations**:
     - Text streams and terminal user interfaces (TUIs) struggle with high-density relational structures (e.g., dependency trees, AST layouts, multi-variable telemetry, spatial coordinate systems).
     - Generative visual artifacts bridge cognitive gaps, allowing users and agents to inspect and reason about multi-dimensional system states simultaneously.
  2. **Interactive Visual Artifacts**:
     - Agents emit fully functional, reactive components (HTML5, SVG, CSS, vanilla JS) rendered directly in the IDE/agent artifact preview panel.
     - Examples showcased:
       - **Interactive Quadtree Spatial Partitioning Explorer**: Real-time canvas demonstrating point insertion, adaptive quadrant subdivision (NW/NE/SW/SE) when threshold $k$ is exceeded, and query-area pruning to avoid $O(N)$ brute-force scans.
       - **Helios Solar Explorer**: Interactive Keplerian orbital mechanics simulation illustrating elliptical orbits, equal-area time sweeps, and orbital period vs. semi-major axis cubic relations ($T^2 \propto a^3$).
       - **AST & Dependency Graph Visualizers**: Parsing `package-lock.json` and module call graphs into navigable graph layouts.
  3. **Zero-Dependency & Offline Execution**:
     - Visualizations are generated self-contained without requiring external NPM/pip package dependencies or remote bundle resolution.
     - Run client-side in the sandbox, operate fully offline, and support export as portable standalone HTML files via the artifact viewer sidepanel.
  4. **Eliminating Context Switching**:
     - In-editor generative UI prevents external dashboard round-trips. Developers inspect runtime telemetry, performance benchmarks, and architecture graphs directly in the agent conversation loop.
     - Accessible natively via natural language intent or the `/generative_ui` slash command.

### 6. Declarative Attention: Language Models Can Control Their Own Attention
- **Source**:
  - X Post: https://x.com/omarsar0/status/2095612805496164801
  - Paper: arXiv:2609.02737 ("Language Models Can Control Their Own Attention")
- **Authors / Institutions**: Namgyu Ho, Huzama Ahmad, Woosung Koh, Se-Young Yun (KAIST AI) & Tal Schuster, Cicero Nogueira dos Santos (Google DeepMind) / Curated by Elvis Saravia (@omarsar0)
- **Core Thesis & Problem Definition**:
  > *"Standard autoregressive transformers waste immense memory bandwidth brute-force scanning the entire Key-Value (KV) cache for every single token step, even though attention weights are intrinsically sparse. Language models can intrinsically declare and govern their own attention scopes during reasoning."*

- **Mechanics & Protocol (Declarative Attention - DA)**:
  1. **Self-Directed Attention Scoping**:
     - Rather than relying on external heuristics, fixed sliding windows, or learned external retrieval routers, the LLM explicitly emits declarative tokens in its Chain-of-Thought (CoT) specifying its attention target before generating text.
  2. **Three Operational Attention Modes**:
     - **Global**: Full attention over all past context tokens (activated during initial context grounding, cross-document synthesis, or plan consolidation).
     - **Focus**: Targeted attention restricted to declared segments, named context spans, or specific tool outputs/code blocks.
     - **Local**: Sliding-window attention over immediate recent tokens for local syntactic formulation and intermediate deduction.
  3. **High-Performance Inference Engine Implementation**:
     - Integrated with **vLLM** and fully compatible with **FlashAttention**.
     - Employs **block-aligned, in-place KV cache masking**: unselected cache blocks are completely skipped at the GPU memory bus level, converting theoretical attention sparsity into real-world latency and memory bandwidth gains.
  4. **Empirical Benchmarks & Scaling Behavior**:
     - Evaluated across 15 long-context benchmark tasks in zero-shot settings:
       - **Gemma-4-31B**: Attended token count reduced by **52.0%** with a negligible **1.27 percentage point** accuracy delta.
       - **Qwen-3.6-27B**: Attended token count reduced by **31.1%** with a **2.75 percentage point** accuracy delta.
     - **Scaling Trend**: The accuracy gap between full attention and Declarative Attention strictly narrows as model scale increases, proving that larger models possess superior metacognitive ability to govern their own attention.

### 7. Declarative Attention (alphaXiv Research Briefing)
- **Sources**:
  - X Post: https://x.com/askalphaxiv/status/2095678236722098292
  - alphaXiv PDF: https://www.alphaxiv.org/pdf/2609.02737
- **Author / Originator**: alphaXiv (@askalphaxiv)
- **Core Summary & Key Insights**:
  - Focuses on the breakthrough *"Language Models Can Control Their Own Attention"*.
  - **Core Problem**: Long-context LLMs waste massive compute by scanning the entire Key-Value (KV) cache at every single decoding step, even when only a small region is semantically relevant to the next token.
  - **Declarative Attention Architecture**:
    - The model explicitly switches between three attention modes during reasoning:
      1. **Global Attention**: Broad context synthesis across all tokens.
      2. **Focused Attention**: Targeted retrieval on specific relevant chunks or memory slots.
      3. **Local Attention**: High-speed narrow context processing.
    - Allows modern inference engines (e.g., vLLM / FlashAttention) to physically skip reading irrelevant KV cache regions from memory bandwidth.
  - **Empirical Validation**:
    - Cuts attended tokens by **52% on Gemma-4-31B** with only $\approx 1.27\,\text{pp}$ accuracy drop.
    - Cuts attended tokens by **31% on Qwen-3.6-27B** with only $\approx 2.75\,\text{pp}$ accuracy drop.

### 8. Designing Proactive Thought Partners (Google DeepMind Study on Agent Proactivity)
- **Sources**:
  - X Post: https://x.com/omarsar0/status/2096780509540139364
  - Paper: arXiv:2609.01588 ("Designing Proactive Thought Partners for Writing")
- **Author / Originator**: Google DeepMind / Curated by Elvis Saravia (@omarsar0)
- **Core Thesis & Research Problem**:
  - Moves proactive AI assistance beyond low-level token autocompletion towards high-level cognitive thought partnership.
  - Investigates how autonomous agents can determine when, why, and how to intervene unprompted without disrupting user flow or inducing cognitive overload.

- **Key Insights & Interaction Architecture**:
  1. **Prospective Scaffolding vs. Reactive Interruption**:
     - Users configure support agents prospectively (setting roles, expectations, and proactivity thresholds before initiating complex workflows) rather than reacting to mid-flow popups.
  2. **Dual Function: Idea Generation & Self-Monitoring**:
     - Beyond content generation and brainstorming, users heavily utilized proactive agent outputs as self-monitoring and pacing anchors—a critical design consideration previously neglected in agent interfaces.
  3. **Presentation & Rhetorical Framing Governs Perceived Intrusiveness**:
     - Intrusiveness is dictated more by presentation ergonomics than intervention frequency.
     - Lightweight visual cues (ambient markers, non-blocking sidebars) combined with non-directive rhetorical phrasing (e.g., posing open questions rather than imperative commands or unsolicited text overwrites) drastically improved user acceptance.
  4. **Design Dimensions**:
     - Successful proactive agents balance four core vectors: **Customization** (user-defined agency), **Timing** (event-driven vs. idle-driven pauses), **Engagement** (opt-in review), and **Representation** (ambient vs. focal UI).

### 9. Normalized Low-Rank Adaptation (NoRA)
- **Sources**:
  - X Post: https://x.com/omarsar0/status/2096837122892485069
  - Paper: arXiv:2608.31036 ("Normalized Low-Rank Adaptation (NoRA)")
- **Author / Originator**: Curated by Elvis Saravia (@omarsar0)
- **Core Thesis**:
  > *"A one-line change to LoRA that costs nothing and improves convergence, stability, and forgetting."*

- **Mechanics & Mathematical Motivation**:
  1. **The LoRA Initialization Asymmetry**:
     - In standard LoRA, the up-projection matrix $B$ is initialized to zero, while the down-projection matrix $A$ is initialized randomly (e.g. Gaussian).
     - Consequently, early optimization dynamics and gradient updates are governed almost exclusively by the down-projection matrix $A$.
  2. **The NoRA Regularization Fix**:
     - NoRA normalizes the down-projection matrices during training.
     - **One-Shot Initialization Alternative**: The authors prove that simply normalizing matrix $A$ once at initialization yields substantial gains without needing dynamic normalization during training steps (the cheapest variant).
  3. **Zero-Cost Architectural Advantage**:
     - **0 Additional Trainable Parameters**: Uses the identical rank $r$ parameterization as standard LoRA.
     - **0 Inference Overhead**: Weights fold directly into base model weights via $W = W_0 + \Delta W$ at merge time.
  4. **Empirical Performance Across Workflows**:
     - Demonstrates universal improvements across Pretraining, Supervised Fine-Tuning (SFT), and Reinforcement Learning (RL).
     - Accelerates training convergence, yields superior final benchmark accuracy, enforces optimization stability, and significantly mitigates catastrophic forgetting.

### 10. Rethinking Skills and Prompts for Modern Frontier Models (Eric Provencher on GPT-6 Astra)
- **Source**:
  - X Article: https://x.com/pvncher/status/2095991462416490862 / https://x.com/i/article/2095989703967125509
- **Author / Originator**: Eric Provencher (@pvncher)
- **Core Thesis**:
  > *"What used to require a lot of handholding and scaffolding no longer does. If you’ve been using agents over the last year, you’ve likely accumulated bloated instructions. With frontier reasoning models like GPT-6 Astra, over-scaffolding actively degrades agent performance."*

- **Key Principles & Operational Guidelines**:
  1. **Skill System Hygiene & Anti-Patterns**:
     - **Context Squashing**: Each installed skill loads its name and description into the system prompt. When descriptions are verbose or skills are numerous, the agent environment (Codex/Agy) truncates them to fit context budgets, impairing the agent's ability to discriminate between skills.
     - **Eliminate "Pick-Me" Energy**: Skill descriptions must be minimal and strictly scoped to exact triggering conditions (e.g. "Run when executing database schema migrations" vs. broad "Run whenever database files are referenced").
     - **Progressive Disclosure as Router**: The root skill file (`SKILL.md`) should act strictly as a lightweight router pointing to auxiliary documentation and scripts, pulling in instructions JIT rather than bloating context upfront and hastening context window compaction.
     - **De-emphasize Rigid Recipes**: Overly granular, step-by-step itineraries constrain modern high-reasoning models. Models handle ambiguity gracefully; over-specified instructions create brittle failure modes.
  2. **AGENTS.md Context Discipline**:
     - Prune legacy instructions that mandate reading the entire repo map or documentation before performing trivial edits (e.g. fixing typos). This burns tokens and drastically increases latency.
     - Avoid redundant behavioral nudges (e.g., modern models naturally self-test; nagging prompts induce circular test loops).
  3. **Permission Scaffolding & Safe Autonomy**:
     - Frontier models exhibit heightened respect for decision boundaries. Guardrails written to restrain older, errant models cause modern models to freeze or ask for needless confirmation.
     - Provide explicit, scoped autonomy waivers for safe environments (e.g., local disposable test fixtures: *"Run tests, fix failures caused by the change, and rerun without asking for approval at each step"*).
  4. **Defining Completion & Persistence**:
     - Frontier models can be tentative regarding task termination, sometimes pausing after a first-pass draft.
     - Define completion up-front in the request (e.g. specify that completion requires building, testing, verifying, and fixing until green) rather than allowing implicit early stopping.

### 11. Eliminating Mannered Prose (Anthropic's Style Architecture for Claude Fable 5.1 & GPT-5.6 Sol)
- **Sources**:
  - X Post: https://x.com/omarsar0/status/2097059598960132110
  - DAIR.AI Resource Guide: https://academy.dair.ai/resources/write-better-with-claude-fable-5-1
  - Anthropic Documentation: *Prompting Claude Fable 5.1: Writing density*
- **Author / Originator**: Anthropic / Curated & Tested by Elvis Saravia (@omarsar0)
- **Core Problem Definition**:
  - Frontier language models (specifically Claude Fable 5.1 and GPT-5.6 Sol) often succumb to "mannered prose"—overloading sentences with decorative metaphors, performative flourishes, and indirect figurative language instead of clear, literal declarations.
  - Examples of mannered degradation:
    - *"a dial worth turning"* instead of *"a parameter worth varying"*
    - *"this point earns its keep"* instead of *"this point still matters"*
    - *"gives your budget a clearer runway, while manual entry remains a path you can continue to walk"* instead of *"saves you time. You can still enter every expense by hand if you prefer."*
  - **The Failure of "Be Concise"**: Generic imperatives like "Be concise" merely set an ambiguous goal without giving the model diagnostic criteria for identifying or pruning performative language.

- **The Canonical De-Mannering Prompt Contract**:
  > *"Mannered prose substitutes metaphor and flourish for direct statement. Instead of 'a parameter worth varying,' the mannered writer produces 'a dial worth turning.' Instead of 'this point still matters,' they write 'this point earns its keep.' The phrases exist to display the writer, not to convey the idea, and readers can tell. That is why mannered prose irritates: it makes the reader work harder so the writer can perform. It is also imprecise. Metaphors drag in connotations the writer did not choose and cannot control. The fix is to say what you mean. When a literal phrase is available, use it."*

- **Key Takeaways & Universal Applicability**:
  1. **Diagnostic Contrast Mechanism**: The prompt works because it defines the flaw, provides concrete before/after pairs, outlines the cognitive friction imposed on the reader, and supplies a clear operational test ("When a literal phrase is available, use it").
  2. **Zero-Latency Shorthand**: In compact workflows or system prompt constraints, Anthropic verified that the directive *"Please remove all mannered prose"* reliably triggers this exact behavior without requiring the full descriptive paragraph.
  3. **Cross-Architecture Generalization**: Evaluated across multiple frontier model families—delivering identical density, clarity, and precision improvements in GPT-5.6 Sol as in Claude Fable 5.1.

### 12. Harness Engineering: Definitive Paper Collection & Evolutionary Taxonomy (YC Paper Club & DAIR.AI)
- **Sources**:
  - X Post: https://x.com/omarsar0/status/2097449131648197024
  - Paper Collection: https://academy.dair.ai/papers/collections/harness-engineering
- **Curated By**: Elvis Saravia (@omarsar0) / YC Paper Club / DAIR.AI Academy
- **Core Thesis**:
  > *"Harness engineering is the single highest-leverage agent skill today. On identical model weights, performance scales from a 30% baseline to 95.5% on ARC-AGI-3 purely by optimizing the execution harness, verifiers, and recursive scaffolding."*

- **The Five Evolutionary Eras of Harness Engineering**:
  1. **Phase 1: The V0 Harness (The Bare In-Context Sampling Loop)**:
     - **Bare Loop** (*Radford et al., 2019*): `while-not-EOS` sampling loop with temperature/top-p. Zero external memory, zero tools, zero skills.
     - **In-Context Exemplars** (*Brown et al., 2020*): Appending solved input/output pairs into prompt context without altering the underlying loop.
     - **Chain-of-Thought (CoT)** (*Wei et al., 2022*): First output-space intervention—spreading latent computation over sequential explicit tokens instead of forcing single-step answers.
  2. **Phase 2: Static Harnesses (Expanding the External Action Space)**:
     - **WebGPT** (*Nakano et al., 2021*): Breaching context boundaries to browse the web with interactive human feedback.
     - **Toolformer** (*Schick et al., 2023*): Substituting in-weight calculations with emitted API tool-call tokens executed by the harness.
     - **ReAct** (*Yao et al., 2022*): Interleaving Thought $\rightarrow$ Action $\rightarrow$ Observation cycles—the core operational loop of modern autonomous agents.
     - **Self-Refine** (*Madaan et al., 2023*): In-context critic loop where the model evaluates and rewrites its own draft without external environment feedback.
     - **Reflexion** (*Shinn et al., 2023*): Verbal reinforcement learning—translating environmental failure signals into natural language episodic reflection stored in working memory.
     - **InterCode** (*Yang et al., 2023*): Interactive coding environment turning terminal execution feedback into a standard tool interface.
     - **Multi-Agent Collaboration** (*Talebirad & Nadiri, 2023*): Spawning persistent, role-specialized peer agents via tool invocations.
     - **Voyager** (*Wang et al., 2023*): The origin of agent skills—chaining tool sequences, verifying execution against environments (Minecraft), and saving proven routines into a persistent skill library.
     - **MemGPT** (*Packer et al., 2023*): LLMs as Operating Systems—giving agents explicit CRUD operations over distinct memory tiers (RAM/working context vs. disk/long-term archival memory).
     - **Recursive Language Models (RLM)** (*Zhang, Kraska, Khattab, 2025*): Embedding LLM calls inside an execution REPL that can spawn recursive LLM calls over large document partitions, eliminating static context limits.
  3. **Phase 3: Learning Harnesses (Self-Optimizing Scaffolding)**:
     - **DSPy** (*Khattab et al., 2023*): Compiling declarative LM pipelines by algorithmically searching over prompts and few-shot selectors against objective metrics.
     - **GEPA** (*Agrawal et al., 2025*): Reflective prompt evolution that inspects natural language traces of failed episodes and mutates prompts to outperform traditional RL.
     - **Darwin Gödel Machine** (*Zhang et al., 2025*): Open-ended evolutionary agents that sample from ancestor archives, rewrite their own scaffolding code, and benchmark themselves on code tasks.
     - **Meta-Harness** (*Lee et al., 2026*): A meta-system that writes, tests, and optimizes harnesses, retries, and verification gates end-to-end.
     - **Continual Harness** (*Karten et al., 2026*): Online adaptation that maintains and mutates history, memory cards, skills, prompts, and sub-agent topologies live during execution.
  4. **Phase 4: Frontier Deployed Harnesses (2026)**:
     - **Prime Agent** (*Karten et al., 2026*): Persistent IPython REPL with recursive, addressable sub-agents and verification suites—scaling ARC-AGI-3 scores to **95.5%**.
     - **OpenJarvis** (*Saad-Falcon et al., 2026*): On-device personal agent decomposing system capabilities into five atomic primitives orchestrated by cloud models while preserving local privacy.
     - **QM (YC Multiplayer Harness)**: YC's open-source multi-agent collaboration harness for autonomous co-development.
  5. **Phase 5: Evaluation Horizon Measurement**:
     - **Measuring AI Ability to Complete Long Software Tasks** (*Kwa et al., 2025*): Redefining agent capability measurement from single-turn snapshot evals to temporal and complexity horizons over extended multi-hour task trajectories.

### 13. Spec-Driven Regeneration & Literate Typed Graphs ("Design Docs Are All You Need" & x0k-folio)
- **Sources**:
  - X Post: https://x.com/omarsar0/status/2096983084956852537
  - Paper: arXiv:2609.05364 (*"Design Docs Are All You Need: An AI-Native Machine Learning Performance Tool"*)
  - GitHub Repository: https://github.com/0k-dot-computer/x0k-folio
- **Authors / Institutions**: Google DeepMind, MIT, et al. / Curated by Elvis Saravia (@omarsar0) / 0k.computer
- **Core Thesis & Paradigm Shift**:
  > *"When abstractions rot rapidly across hardware and model generations, maintaining code manually is an anti-pattern. The main branch contains almost no hand-written code—only a directed graph of natural language design docs. Coding sub-agents regenerate the entire library from design docs on every update."*

- **System Architecture & Key Innovations**:
  1. **"Design Docs Are All You Need" (DeepMind / MIT)**:
     - **Code-Free Repository**: The codebase is maintained purely as natural language architectural specs and step-by-step worked examples.
     - **Autonomous Sub-Agent Regeneration**: Coding sub-agents compile the design docs into complete runnable software implementations upon every release/version bump.
     - **Grounding Pillars for Reliability**:
       - *Step-by-Step Worked Examples*: Serve as in-context demonstrations that bound agent ambiguity and guide generation.
       - *Minimal Symbolic IR*: Anchored on a recursively defined operator Intermediate Representation (IR) with symbolic cost expressions in SymPy.
     - **Verifiable Precision**: Regenerated implementations match hand-audited reference performance models down to round-off error (e.g. serving DeepSeek-V3 across TPU pod slices).
  2. **x0k-folio: AI-Native Literate Programming & Typed Document Graphs**:
     - **Tangle & Weave for AI Agents**:
       - `tangle`: Extracts executable source code directly out of markdown design documents for compilers.
       - `weave`: Renders interactive, hyperlinked documentation where every code reference connects to its ontological definition.
     - **Typed Document Graph & Ontologies**: Uses RDF/Turtle (`x0k-ontology`) to declare concepts, classes, and affordances (e.g., specifying allowed actors `[human, ai_agent]` and software module dependencies).
     - **CI Verification**: Continuous integration verifies that committed source files strictly correspond to the code blocks in the design documents, ensuring prose and implementation never drift out of sync.
     - **Durable Reasoning Recovery**: Gives subsequent human engineers and autonomous agents complete context recovery regarding *why* an architectural decision was made before touching the implementation.

### 14. Agents, Loops, Graphs: The Unified Architecture Framework (Mahaximus)
- **Sources**:
  - Notion Document: https://app.notion.com/p/Agents-Loops-Graphs-Everything-You-Need-to-Know-in-One-Place-3b613313097a815a946fcb5d01feee42
  - X Guide & Video: https://x.com/mahaximus_/status/2085024744387092973 / https://x.com/Mahaximus_/status/2085725676145975422
- **Author / Originator**: Mahaximus (@mahaximus_)
- **Core Thesis**:
  > *"Most people use AI in a linear chat: ask, read, fix, ask again. That is the slowest possible way. Advanced agent architectures break down into three distinct structural components: Agents (autonomous execution), Loops (falsifiable self-correction), and Graphs (parallel multi-agent orchestration)."*

- **The Tripartite Architecture**:
  1. **Part 1 — Agents (The Anatomy of Autonomous Execution)**:
     - **Definition**: An agent is not a smarter model; it is a model surrounded by **Tools** (unsupervised search/read/write/run), **Memory** (retention of past decisions and attempts), and a **Loop** (persisting until goal completion rather than emitting a single conversational turn).
     - **Four Autonomy Levels**:
       - *Level 1 (Chat)*: Direct human driving.
       - *Level 2 (Tool-augmented)*: Model autonomously decides when to query tools before replying.
       - *Level 3 (Multi-step work)*: Model decomposes high-level goals, plans, executes, verifies, and hands off finished deliverables.
       - *Level 4 (Fully Autonomous)*: Event/schedule-triggered headless execution with zero in-the-loop intervention.
     - **Triad of Agent Invariants**:
       - *Research Agent*: Strict relevance filtering, mandatory citations per claim, explicit contradiction flagging.
       - *Data Agent*: Interpretation over description, outlier detection, single prescriptive decision sentence.
       - *Code Agent*: Working code over promising code, mandatory mental dry-run trace, single-sentence root-cause explanation for bug fixes.
     - **Structured Memory Checkpoint Protocol**:
       - *Mid-task Checkpoint*: <150 words capturing completed sub-tasks, architectural decisions with rationale, pending work, and new-session resumption tokens.
       - *Long-context Compression*: Re-grounding on original goal, empirical findings, and remaining tasks as a fresh starting point.
       - *Session Handoff*: Resuming from checkpoint state without repeating work.
  2. **Part 2 — Loops (Falsifiable Self-Correction & Quality Gates)**:
     - **The 5-Step Loop**: `PLAN` $\rightarrow$ `EXECUTE` $\rightarrow$ `CHECK` $\rightarrow$ `ITERATE` $\rightarrow$ `STOP`.
     - **Two Non-Negotiable Invariants**:
       - *Falsifiable Check*: The check must be capable of failing (a binary pass/fail test or harsh numerical threshold). Soft checks lead to models hallucinating completion.
       - *Hard Stop Limit*: Bounded iteration count (e.g. max 8 attempts) to prevent infinite loops and runaway compute spend.
     - **Viability Filter**: Only deploy a loop if (1) task is repeated, (2) output can grade itself objectively, (3) zero babysitting is required, and (4) "done" is a measurable fact rather than subjective taste.
     - **The Canonical One-Prompt Loop**:
       `DRAFT` $\rightarrow$ `SCORE` (rate 1–10 harshly against strict measurable criteria) $\rightarrow$ `GAPS` (isolate weakest point) $\rightarrow$ `CALL` (if all criteria $\ge 8$, mark `DONE` and stop; else `NEXT PASS` focusing exclusively on the lowest-scoring gap).
  3. **Part 3 — Graphs (Parallel Multi-Agent Workflows & The Diamond Pattern)**:
     - **Definitions**:
       - *Node*: Atomic job with strict JSON input/output schemas (rejecting and retrying non-conforming structures).
       - *Edge*: True data dependency (Node B only depends on Node A if B strictly consumes A's payload).
     - **The Fake Edge Test**: Audit workflow arrows to remove artificial sequential constraints, converting serialized bottlenecks into parallel pipelines.
     - **The Diamond Orchestration Pattern**:
       - *Fan Out*: Spawn parallel independent worker agents simultaneously across distinct task dimensions/angles.
       - *Deterministic Reduce*: Aggregate raw findings via plain code (deduplication/filtering) at zero token cost.
       - *Independent Skeptic Verification*: Fresh-context evaluator agents attempt to aggressively disprove each survivor (`keep` or `drop`).
       - *Convergence Synthesis*: Single synthesis agent compiles verified survivors into the final structured report.

### 15. Hermes + Gemini Notebook: Autonomous Multi-Modal Content Operating System (Julian Goldie)
- **Source**:
  - X Post & Video Breakdown: https://x.com/JulianGoldieSEO/status/2091963756699930769
- **Author / Originator**: Julian Goldie (@JulianGoldieSEO)
- **Core Thesis**:
  > *"Most people use NotebookLM for research, generate one thing, and abandon it. This architecture converts passive notebook research into an automated production loop and persistent memory engine: Research in $\rightarrow$ Content out $\rightarrow$ Memory saved $\rightarrow$ Next run gets smarter."*

- **Four-Tier Architecture & Flywheel Pipeline**:
  1. **Tier 1: Multi-Modal Research Brain (Gemini Notebook / NotebookLM)**:
     - Grounds reasoning in diverse source documents: technical PDFs, web pages, YouTube video transcripts, Google Drive files, Google Docs, and raw audio files.
     - Serves as the immutable factual substrate, preventing hallucinations.
  2. **Tier 2: Agentic Orchestration Layer (Hermes + MCP)**:
     - Hermes connects directly to Gemini Notebooks via the Model Context Protocol (MCP).
     - Autonomously executes structured queries, extracts evidence cards and citations, and expands a single research query into multi-channel production artifacts.
     - Concurrently outputs: Video scripts, long-form technical/LinkedIn posts, structured email sequence introductions, and short-form video clip scripts.
  3. **Tier 3: Programmatic Video & Audio Rendering Engine (Hyperframes)**:
     - Bridges written agent outputs into rendered multimedia deliverables.
     - Automates complete MP4 video generation: HTML/CSS programmatic canvas visuals, styled title cards, word-level synchronized subtitles/captions, and naturalistic TTS voice narration.
  4. **Tier 4: Durable Memory Vault (Obsidian Vault Integration)**:
     - Automatically logs every generated asset, source citation, content angle, and campaign context into a structured local Obsidian Markdown vault.
     - Eliminates the multi-session amnesia problem: before drafting new deliverables, Hermes audits previous vault entries to maintain stylistic continuity, brand voice, and avoid duplicate topic coverage.

---

## Hermes Current State Audit

> **Constraint**: Reduce custom Python files as low as possible. Prefer native Hermes config/skills/rules/plugins over bespoke scripts. Every change must be minimal delta.

### Architecture Overview

Hermes is a fully self-contained, chezmoi-managed personal AI agent harness running inside the `ws-hermes` Distrobox container. Core components:

| Layer | Path | Description |
|:------|:-----|:------------|
| **Inference** | `llama-server` at `:8138` | llama.cpp server, Gemma-4-4B, 65536 ctx |
| **Agent Engine** | `.hermes/hermes-agent/` | The upstream Hermes agent runtime (CLI, conversation loop, tools, plugins, TUI gateway, web server) |
| **Core Library** | `.hermes/src/hermes_core/` | ~60 Python modules: agent_os, GEPA, quorum, skill routing, embeddings, context sieve, task graph, trajectory, etc. |
| **Config** | `.hermes/config.yaml` | Model, terminal, browser, web backend, tool-loop guardrails, plugin registry |
| **System Prompt** | `.hermes/SOUL.md` | 19-rule behavioral constitution (the agent's character and operating law) |
| **Agent Instruction** | `.hermes_AGENTS.md` (root) & `AGENTS.md` | Constraint tables, 8 laws, 6-phase lifecycle, verification commands |
| **Skills** | `.hermes/private_skills/` | 91 SKILL.md files across: software-dev, research, creative, GitHub, productivity, MLOps, media, devops, email, smart-home, social-media |
| **Profiles** | `.hermes/profiles/` | architect, coder, debugger, tester, researcher + lever-compound, lever-mcp, lever-memory, frontier variants |
| **Plugins** | `.hermes/plugins/` | quorum_audit, gepa_optimizer, observer_gate, cog_verifier, agent_os, symbol_index, recirculation_adapter, reflective_learner_adapter, synergy_bus_adapter |
| **Rules** | `.hermes/rules/project.md` | Project-specific architectural constraints |
| **Memory** | `.hermes/memory/experiential.jsonl` | Episodic memory store |
| **Knowledge** | `.hermes/knowledge/` | blueprints, concepts, evals, evidence, signal_digest |
| **Bin Scripts** | `.hermes/bin/` | 15 Python utility scripts (observer_gate, skill_retriever, verify_harness_integrity, ingest_document, etc.) |
| **Tests** | `tests/` + `.hermes/tests/` | Black-box harness contracts + white-box component tests |
| **Chezmoi** | `.local/share/chezmoi/` | Dotfile manager syncing entire `.hermes/` to the container |

### What Already Exists (Do Not Rebuild)

| Item | Already Present As |
|:-----|:------------------|
| **Plan→Execute→Verify→Ship loop** (Item 1) | 6-Phase Protocol in AGENTS.md + `.hermes/plan.json` + tabu branch pruner |
| **Multi-session amnesia / durable handoffs** (Item 2) | `.hermes/memory/experiential.jsonl` + chezmoi-tracked state + session persistence in `hermes_core/session_persistence.py` |
| **Maker/Verifier separation** (Item 2) | `quorum_audit` plugin (edit→audit→agree→retro→commit) + separate `@tester`/`@coder` profiles |
| **Progressive disclosure for skills** (Items 2, 10) | 91 skills loaded JIT via `skill_router.py` + `skill_retriever.py` + Tier 1/2 system prompt sieve |
| **Spec-first planning** (Items 1, 13) | `.hermes/plan.json` contract + Phase 1 in SOUL.md + spec_first_planner.py |
| **Observer Gate** (Items 1, 12) | `observer_gate` plugin + `bin/observer_gate.py` (475 lines) — AST syntax, brace balance, oracle checks |
| **GEPA reflective evolution** (Item 12) | `gepa_optimizer` plugin + `hermes_core/gepa_optimizer.py` + `hermes_core/evolution.py` |
| **Quorum consensus / Maker≠Auditor** (Item 12) | `quorum_audit` plugin + `hermes_core/cog_verifier.py` |
| **Context sieve / token budget** (Items 2, 10) | `hermes_core/context_sieve.py` + `context_window_guard.py` + `token_engine.py` |
| **Grep over vectors** (Item 2) | AGENTS.md Law §9 + `symbol_graph.py` (Tree-Sitter AST search) — already preferring grep/glob |
| **Generative UI artifacts** (Item 5) | `software-development/generative-ui-artifact/SKILL.md` already exists |
| **Web grounding** (Items 2, 4) | `hermes_core/web_grounding.py` + `bin/web_grounding.py` + `ddgs` backend in config |
| **Task graph / dependency ordering** (Items 1, 14) | `hermes_core/task_graph.py` |
| **Experience / episodic memory** (Item 12) | `hermes_core/experience_store.py` + `memory/experiential.jsonl` |
| **Subagent delegation / multi-agent** (Items 2, 14) | SOUL.md §13 + `hermes_core/domain_fleet.py` + `swarm_engine.py` |
| **Chezmoi sync** (all items) | Full chezmoi pipeline already operational, 39 commits ahead |
| **Obsidian vault** (Item 15) | `private_skills/note-taking/obsidian/SKILL.md` |
| **ArXiv research** (Items 6, 7, 8, 9) | `private_skills/research/arxiv/SKILL.md` |
| **Harness integrity verification** (Item 12) | `bin/verify_harness_integrity.py` (761 lines) |

### What Can Be Replaced / Simplified

| Custom Python File | Current Role | Replace With |
|:-------------------|:-------------|:-------------|
| `bin/skill_router.py` (41 lines) | Keyword-based skill dispatch | Native Hermes skill description routing — config-only, no Python needed |
| `bin/skill_retriever.py` (144 lines) | FastEmbed cosine similarity skill lookup | Native `skills_catalog.py` already in `hermes_core`; deduplicate |
| `bin/web_grounding.py` (42 lines) | DuckDuckGo search wrapper | Native `web` tool in config (`web.backend: ddgs`) — this script is redundant |
| `bin/extract_web_content.py` (94 lines) | URL content extraction | Hermes native browser+web tools already handle this |
| `bin/extract_code_mode.py` (103 lines) | Code block extraction | `hermes_core/context_sieve.py` already does this |
| `bin/harness_architectural_evolution.py` (72 lines) | Ad-hoc evolution trigger | `gepa_optimizer` plugin's `on_session_end` hook replaces this |
| `bin/hub_cli.py` (152 lines) | Hub state management | `.hermes/hub/state.json` + native plugin state — can be config only |
| `bin/ingest_document.py` (144 lines) | Document ingestion | Hermes native file+browser tools; `index_docs.py` overlaps |
| `bin/container_cmd.py` (50 lines) | Distrobox command wrapper | Native `terminal` tool in config already handles this |

### What Can Be Added (New — Not Yet Present)

| Item | Capability | Hermes Addition Required |
|:-----|:-----------|:------------------------|
| **Item 2 — Dreaming logs** | Offline batch: session logs → memory cards | New `on_session_end` hook in `reflective_learner_adapter` plugin (config-only, ~20 lines) |
| **Item 8 — Proactive Thought Partners** | Agent-initiated ambient suggestions | New `proactive` rule in `rules/` + lightweight ambient skill (no Python) |
| **Item 10 — Skill description hygiene** | All 91 skill descriptions ≤60 chars, router-only | Audit pass on all `SKILL.md` frontmatter `description` fields |
| **Item 10 — Completion definition** | Explicit done-criteria in every SOUL.md task pattern | Edit SOUL.md §11 to add explicit completion contract |
| **Item 11 — Mannered prose elimination** | Anti-mannered-prose directive baked into SOUL.md | 3-line addition to SOUL.md: the Anthropic diagnostic contract |
| **Item 13 — Spec-Driven Regeneration** | Design-doc-first pattern: tangle code from docs | New skill `software-development/spec-driven-regen/SKILL.md` (no Python) |
| **Item 14 — Diamond orchestration pattern** | Explicit fan-out→reduce→verify→converge multi-agent template | New skill `software-development/diamond-orchestration/SKILL.md` |
| **Item 14 — Hard stop limit in loops** | Bounded iteration count enforcement | Edit `tool_loop_guardrails.hard_stop_enabled: true` in `config.yaml` |
| **Item 15 — NotebookLM MCP bridge** | MCP server connecting Hermes → Gemini Notebook | New MCP config entry (config-only, no Python) |

### What Can Be Removed

| File / Component | Reason |
|:-----------------|:-------|
| `bin/container_cmd.py` | Redundant — native terminal tool covers this |
| `bin/web_grounding.py` | Redundant — native `web.backend: ddgs` in config |
| `bin/harness_architectural_evolution.py` | Superseded by `gepa_optimizer` plugin hook |
| `bin/extract_web_content.py` | Redundant — native browser/web tools |
| `bin/skill_router.py` | Superseded by native skill routing + descriptions |
| `dot_hermes_AGENTS.md` (from `.hermes_AGENTS.md`) | Merge into AGENTS.md — two copies of agent instructions is a maintenance hazard |

---

## Implementation Roadmap

> **Order**: Dependencies first. Config/rule/skill changes before Python. Removals after replacements are confirmed working.

### Phase 0 — Foundation: Context Hygiene & Prompt Discipline
*Zero new code. Pure config + text edits. Immediate impact on every session.*

**0.1 — Enable Hard Stop on Tool Loop** *(Item 14)*
- Edit `config.yaml`: `tool_loop_guardrails.hard_stop_enabled: true`
- This enforces the falsifiable loop invariant from Mahaximus: bounded iterations, no infinite loops.
- **Delta**: 1-line config change.

**0.2 — Mannered Prose Elimination in SOUL.md** *(Item 11)*
- Prepend Anthropic's diagnostic contract to SOUL.md as Rule 0 (highest precedence).
- Shorthand fallback: `"Please remove all mannered prose"` as a terminal directive.
- **Delta**: ~8 lines in SOUL.md.

**0.3 — Skill Description Hygiene Audit** *(Item 10)*
- Audit all 91 `SKILL.md` frontmatter `description` fields.
- Enforce ≤60 chars, router-only, exact trigger condition language (no "Pick-Me" energy).
- **Delta**: Config/text edits only, no Python.

**0.4 — AGENTS.md Pruning** *(Item 10)*
- Remove legacy instructions that mandate reading entire repo maps for trivial tasks.
- Remove redundant behavioral nudges (self-testing nagging, over-specified step recipes).
- Merge `dot_hermes_AGENTS.md` into `AGENTS.md` — eliminate the duplicate.
- **Delta**: Text deletion only.

---

### Phase 1 — Loop Architecture: Finish-First & Falsifiable Verification
*Formalizes the 4-phase lifecycle already partially present.*

**1.1 — Explicit Completion Contract in SOUL.md** *(Items 1, 10)*
- Add to SOUL.md §11 (Session Lifecycle): explicit completion definition pattern.
- *"Completion requires: build → test → verify → fix until green. Never stop at first-pass draft."*
- **Delta**: ~5 lines in SOUL.md.

**1.2 — Evidence-Grounded Progress Audit Rule** *(Item 2)*
- Add to `rules/project.md`: the Anthropic evidence-audit contract.
- *"Before reporting progress, audit each claim against a tool result from this session."*
- **Delta**: ~6 lines in `rules/project.md`.

**1.3 — Diamond Orchestration Pattern Skill** *(Item 14)*
- Create `private_skills/software-development/diamond-orchestration/SKILL.md`.
- Contains: fan-out → deterministic-reduce → skeptic-verify → converge template.
- **Delta**: New SKILL.md, no Python.

---

### Phase 2 — Memory: Dreaming Logs & Durable Handoffs
*Converts session logs to persistent memory cards. Zero new Python.*

**2.1 — Dreaming Hook in reflective_learner_adapter** *(Item 2)*
- Edit `plugins/reflective_learner_adapter/plugin.yaml` to add `on_session_end` hook.
- Hook body: shell command that summarizes `.hermes/logs/` into `memory/experiential.jsonl` cards with one-line scannable summaries.
- Can be a shell script or tiny YAML template — no new standalone Python file.
- **Delta**: Edit existing plugin.yaml + tiny shell hook.

**2.2 — Session Handoff Checkpoint Skill** *(Items 2, 14)*
- Extend `private_skills/software-development/plan/SKILL.md` to include the <150-word checkpoint protocol.
- Covers: completed sub-tasks, decisions-with-rationale, pending work, resumption tokens.
- **Delta**: Edit existing SKILL.md.

**2.3 — Obsidian Vault Memory Integration** *(Item 15)*
- Edit `private_skills/note-taking/obsidian/SKILL.md` to add content-OS workflow: log every research artifact, source citation, content angle into vault before generating new content.
- **Delta**: Edit existing SKILL.md.

---

### Phase 3 — Skills & Routing: Progressive Disclosure + Proactive Partnership
*JIT skill loading cleanup and new thin skills for new patterns.*

**3.1 — Proactive Thought Partner Rule** *(Item 8)*
- Create `rules/proactive.md` defining prospective scaffolding behavior.
- Lightweight ambient suggestion protocol: non-directive, opt-in, sidebar framing.
- **Delta**: New rules file (~20 lines), no Python.

**3.2 — Spec-Driven Regeneration Skill** *(Item 13)*
- Create `private_skills/software-development/spec-driven-regen/SKILL.md`.
- Encodes the x0k-folio + DeepMind "Design Docs Are All You Need" pattern.
- Tangle workflow: natural-language design doc → sub-agent code generation → CI verification.
- **Delta**: New SKILL.md only.

**3.3 — Remove Redundant Bin Scripts** *(Items 10, 12)*
- Remove: `bin/container_cmd.py`, `bin/web_grounding.py`, `bin/harness_architectural_evolution.py`, `bin/extract_web_content.py`, `bin/skill_router.py`
- Verify each is either superseded by native tooling or covered by existing `hermes_core/` modules.
- **Delta**: Deletions. No new Python.

---

### Phase 4 — Multi-Agent: Maker/Verifier & External Integrations
*Solidifies separation of production vs. evaluation agents and adds new MCP bridges.*

**4.1 — Strengthen Maker/Verifier Separation** *(Items 1, 2, 12)*
- Review `quorum_audit` plugin hooks — ensure `Author != Auditor` is enforced on all write operations.
- Ensure `@tester` profile has no write tools; `@coder` profile cannot run its own post-commit audit.
- **Delta**: Plugin YAML and profile capability mask edits only.

**4.2 — NotebookLM / Gemini Notebook MCP Bridge** *(Item 15)*
- Add MCP server config entry to `config.yaml` or `.hermes/mcp/` for Gemini Notebook.
- Enables `hermes` to query notebook sources via MCP tool calls directly.
- **Delta**: Config entry only, no Python.

**4.3 — Conservative Multi-Agent Budget Rule** *(Item 2)*
- Add to SOUL.md: the token economics note (single-agent = 4×, multi-agent = 15×; only fan-out for genuinely parallelizable tasks).
- **Delta**: ~4 lines in SOUL.md.

---

### Phase 5 — Harness Learning: GEPA & Self-Optimization
*Activates the existing GEPA infrastructure for live prompt evolution.*

**5.1 — Activate GEPA on Session End** *(Items 12, 3)*
- Verify `gepa_optimizer` plugin `on_session_end` hook fires correctly.
- Configure GEPA to target: SOUL.md rules + skill descriptions + top-failure prompts.
- **Delta**: Plugin config verification + GEPA seed corpus in `knowledge/`.

**5.2 — Harness Engineering Signal Digest** *(Item 12)*
- Populate `knowledge/signal_digest.md` with the Phase 1–5 evolutionary taxonomy from Item 12.
- Used by GEPA as a reference corpus for prompt mutation direction.
- **Delta**: Edit existing markdown file.

**5.3 — Looped Transformer Config Note** *(Item 3)*
- Add to `knowledge/signal_digest.md`: note on Nanbeige 4.2 / Mixture-of-Recursions.
- Relevant for future model selection: when swapping local models, prefer weight-tied looped architectures (better VRAM/performance trade-off at small scale).
- **Delta**: Documentation only.

---

### Phase 6 — Advanced: Declarative Attention & NoRA Fine-Tuning
*Forward-looking — applies when upgrading local model infrastructure.*

**6.1 — Declarative Attention (vLLM upgrade path)** *(Items 6, 7)*
- When `llama-server` is next upgraded: evaluate vLLM with FlashAttention as alternative backend.
- Add a skill note in `private_skills/mlops/inference/serving-llms-vllm/SKILL.md` documenting the DA block-masking configuration.
- **Delta**: Skill documentation addition.

**6.2 — NoRA Fine-Tuning Guide** *(Item 9)*
- Add to `private_skills/mlops/models/gemma-trainer/SKILL.md`: NoRA normalization note.
- One-line change to LoRA init: normalize down-projection matrix A at initialization.
- **Delta**: Skill documentation addition.

**6.3 — CodeMender-Style Vulnerability Harness Pattern** *(Item 4)*
- Document the Fairwind/CodeMender pattern (find → validate → patch → regression-test) as a workflow in `private_skills/devops/sdlc-review/SKILL.md`.
- **Delta**: Skill documentation addition.

---

### Roadmap Summary Table

| Phase | Items | Approach | Python Files Added/Removed |
|:------|:------|:---------|:--------------------------|
| **0** — Foundation | 11, 10, 14 | config.yaml + SOUL.md + AGENTS.md edits | 0 added, 0 removed |
| **1** — Loop Architecture | 1, 10, 14 | SOUL.md + rules + 1 new SKILL.md | 0 added, 0 removed |
| **2** — Memory / Dreaming | 2, 14, 15 | plugin.yaml hook + SKILL.md edits | 0 added, 0 removed |
| **3** — Skills / Routing | 8, 13, 10 | new rules file + 1 new SKILL.md + deletions | 0 added, **5 removed** |
| **4** — Multi-Agent | 1, 2, 12, 15 | plugin YAML + config MCP entry + SOUL.md | 0 added, 0 removed |
| **5** — Harness Learning | 12, 3 | knowledge/ markdown + GEPA config | 0 added, 0 removed |
| **6** — Adv. Infra | 6, 7, 9, 4 | SKILL.md documentation additions | 0 added, 0 removed |
| **Total** | | | **0 new Python files**, **5 removed** |

---

## Deep Python File Audit: Every .hermes Module vs Upstream Packages

> **Goal**: For every custom `.py` file in `.hermes/src/hermes_core/` and `.hermes/bin/`, identify whether it wraps an upstream package that already exists, duplicates native Hermes capability, or is genuinely irreplaceable. Replace wrappers with direct upstream imports. Delete duplicates. Keep only what has no upstream equivalent.

### Audit Legend
- 🔴 **DELETE** — Pure redundant wrapper; upstream package does this natively. Zero custom logic worth keeping.
- 🟡 **THIN SHIM** — Keep but reduce to ≤30 lines that call upstream directly (no reimplementation).
- 🟢 **KEEP** — Genuinely custom logic with no upstream equivalent, or the glue that binds Hermes identity.
- 🔵 **REPLACE** — Custom reimplementation of something an upstream package does better; swap import.

---

### Category 1: Web Grounding & Document Extraction

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `bin/web_grounding.py` | 42 | DuckDuckGo search wrapper | `ddgs` via native `web.backend: ddgs` in config.yaml | 🔴 DELETE |
| `bin/extract_web_content.py` | 94 | URL → markdown extraction | **crawl4ai** `AsyncWebCrawler` — already installed | 🔴 DELETE |
| `hermes_core/web_grounding.py` | ~60 | DDGS search + content fetch | **crawl4ai** + native web tool | 🔴 DELETE |
| `hermes_core/fast_research.py` | ~80 | Token-budgeted web lookup | **crawl4ai** `word_count_threshold` param | 🔴 DELETE |
| `bin/ingest_document.py` | 144 | File → markdown ingest | **crawl4ai** `AsyncWebCrawler` for local files | 🔴 DELETE |
| `bin/index_docs.py` | 108 | Document → FastEmbed index | **crawl4ai** + **fastembed** + **graphiti** | 🔴 DELETE |

**Why**: `crawl4ai` (`pip install crawl4ai`) handles async extraction, JS rendering, LLM-ready markdown, BFS crawling. Every update to crawl4ai (adaptive crawling, better markdown, etc.) flows in for free.

---

### Category 2: Embeddings & Semantic Search

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/embeddings.py` | ~70 | FastEmbed TextEmbedding wrapper + cosine sim | **fastembed** `TextEmbedding` directly — `from fastembed import TextEmbedding` | 🔴 DELETE |

**Why**: `fastembed` is already installed. It returns numpy arrays. Cosine sim is `np.dot(a, b)`. No wrapper class needed.

---

### Category 3: Skill Management & Routing

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `bin/skill_router.py` | 41 | Keyword → SKILL.md dispatch | Native Hermes JIT skill loading | 🔴 DELETE |
| `bin/skill_retriever.py` | 144 | FastEmbed cosine skill lookup | Native `openskills_manager` + `fastembed` | 🔴 DELETE |
| `hermes_core/skill_router.py` | ~60 | Regex/keyword skill routing | Native Hermes profile + skill description system | 🔴 DELETE |
| `hermes_core/skills_catalog.py` | ~90 | SKILL.md YAML catalog builder | Already done by `openskills_manager.py` | 🔴 DELETE |
| `hermes_core/skills_registry.py` | ~80 | Skill registration + lookup | Already done by `openskills_manager.py` | 🔴 DELETE |
| `hermes_core/openskills_manager.py` | ~120 | SKILL.md L0/L1/L2 discovery | This IS the native Hermes skill system | 🟢 KEEP |
| `hermes_core/skill_evaluator.py` | ~150 | A/B trajectory lift evaluation | **dspy** `dspy.Evaluate` + `MIPROv2` | 🔵 REPLACE |
| `hermes_core/skill_evolution.py` | ~100 | Auto-draft + promote new skills | **dspy** `BootstrapFewShotWithRandomSearch` | 🔵 REPLACE |

---

### Category 4: Memory, Knowledge & Persistence

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/knowledge_graph.py` | ~100 | Python AST → CodeNode graph | **ast-grep-py** `SgRoot` polyglot | 🔵 REPLACE |
| `hermes_core/symbol_graph.py` | ~200 | Tree-Sitter polyglot symbol DB | **ast-grep-py** + graphify skill | 🔵 REPLACE |
| `hermes_core/symbol_indexer.py` | ~80 | Python/JS AST symbol extractor | **ast-grep-py** multi-language | 🔵 REPLACE |
| `hermes_core/graph_engine.py` | ~120 | DAG topology sort + JSON schema validate | **networkx** `DiGraph` + **jsonschema** | 🔵 REPLACE |
| `hermes_core/experience_store.py` | ~150 | Episodic memory JSONL + SQLModel | **sqlmodel** directly — 10-line schema | 🟡 THIN SHIM |
| `hermes_core/second_brain.py` | ~120 | Markdown knowledge vault CRUD | **python-frontmatter** + native filesystem | 🟡 THIN SHIM |
| `hermes_core/working_memory.py` | ~80 | RAM-backed context anchors | **graphiti** (`getzep/graphiti`) temporal episodic graph | 🔵 REPLACE |
| `hermes_core/session_persistence.py` | ~130 | Session state JSON/SQLite save | **sqlmodel** + native plan.json | 🟡 THIN SHIM |
| `hermes_core/database.py` | ~80 | SQLite WAL connection factory | **sqlmodel** `create_engine(url, connect_args={"check_same_thread": False})` | 🔴 DELETE |
| `hermes_core/cog_vault.py` | ~60 | Knowledge vault CRUD | **python-frontmatter** + native filesystem | 🔵 REPLACE |
| `hermes_core/opencode_mem.py` | ~60 | OpenCode memory engine | Duplicate of `working_memory` / graphiti | 🔴 DELETE |

**Why graphiti**: `getzep/graphiti` provides bi-temporal knowledge graphs, hybrid retrieval (BM25 + embeddings + graph traversal), incremental real-time updates, and an MCP server out of the box. Replaces 3 custom memory files with `from graphiti_core import Graphiti`.

---

### Category 5: Verification, Audit & Loop Control

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `bin/observer_gate.py` | 475 | HTML/JS syntax + brace balance + oracle | **ast-grep-py** for code; stdlib html.parser for HTML | 🟡 THIN SHIM (~50 lines) |
| `hermes_core/draft_detective.py` | ~150 | Adversarial fact-check + APS | ast-grep-py + stdlib ast | 🟡 THIN SHIM |
| `hermes_core/quorum_gate.py` | ~120 | Blast radius + audit receipt | Delegates AST work to ast-grep-py | 🟡 THIN SHIM |
| `hermes_core/cog_verifier.py` | ~150 | Worker/Verifier dual-agent loop | **nemoguardrails** dialog rails OR `quorum_audit` plugin | 🔵 REPLACE via plugin |
| `hermes_core/verification_matrix.py` | ~100 | Multi-tier pre-commit gate | `observer_gate` plugin hook already covers this | 🔴 DELETE |
| `hermes_core/loop_contracts.py` | ~80 | Max-iter + VRAM + tabu stop | `config.yaml` `tool_loop_guardrails` (already exists) | 🔴 DELETE |
| `hermes_core/branch_swapper.py` | ~150 | 2-strike tabu branch swap | `quorum_audit` plugin `pre_commit` hook config | 🔵 REPLACE via plugin |
| `hermes_core/hypothesis_tree.py` | ~100 | MCTS-style branching | Git branching + JSON state file | 🟡 THIN SHIM |
| `hermes_core/lineage.py` | ~130 | AVO lineage tree + supervisor | **gitpython** `Repo.git.log()` ancestry | 🔵 REPLACE with gitpython |
| `bin/verify_harness_integrity.py` | 761 | 30-point capability audit | Thin pytest runner wrapper | 🟡 THIN SHIM (~30 lines) |
| `bin/verify_skills_config.py` | 122 | Skill YAML frontmatter validation | **pydantic** schema + `openskills_manager` | 🔴 DELETE |
| `bin/verify_transcript.py` | 97 | JSONL hash-chain audit | **openlit** spans + stdlib JSONL | 🔴 DELETE |

---

### Category 6: GEPA, Evolution & Self-Optimization

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/gepa_optimizer.py` | ~100 | Reflective Pareto prompt evolution | **dspy** `MIPROv2` teleprompter | 🔵 REPLACE |
| `hermes_core/evolution.py` | ~90 | Genetic variation + Pareto frontier | **dspy** `BootstrapFewShotWithRandomSearch` | 🔵 REPLACE |
| `hermes_core/harness_evolution.py` | ~72 | Full harness self-mutation | **dspy** + git branching | 🔵 REPLACE |
| `hermes_core/reflective_learner.py` | ~100 | Correction event → memory card | `reflective_learner_adapter` plugin hook + **graphiti** | 🔵 REPLACE via plugin |
| `hermes_core/recirculation.py` | ~80 | Session log → memory recirculation | `reflective_learner_adapter` plugin `on_session_end` hook | 🔵 REPLACE via plugin |
| `bin/harness_architectural_evolution.py` | 72 | Ad-hoc evolution trigger | `gepa_optimizer` plugin hook | 🔴 DELETE |

**Why DSPy**: `stanfordnlp/dspy` provides `MIPROv2` (same Pareto multi-objective optimization as GEPA), `BootstrapFewShotWithRandomSearch` (same A/B lift evaluation), and it improves with every Stanford/MLCommons release. GEPA custom code becomes a ~20-line DSPy config.

---

### Category 7: MCP, Tooling & Formatting

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/fastmcp.py` | ~80 | FastMCP server wrapper | **fastmcp** upstream `pip install fastmcp` — `from fastmcp import FastMCP` | 🔴 DELETE |
| `hermes_core/formatter_pipeline.py` | ~60 | ruff/biome/rustfmt/gofmt dispatch | Shell commands via `subprocess.run(["ruff", "format", ...])` — no class | 🔴 DELETE |
| `hermes_core/tools.py` | ~100 | Tool schema definitions | **fastmcp** `@mcp.tool` auto-generates JSON schemas | 🔴 DELETE |
| `hermes_core/middleware.py` | ~60 | Prompt sanitization layer | **nemoguardrails** Colang input rails | 🔵 REPLACE |
| `hermes_core/hook_router.py` | ~50 | Plugin hook dispatch | Native Hermes `plugin_loader.py` | 🔴 DELETE |
| `hermes_core/hooks.py` | ~60 | Hook registration + fire | Native Hermes plugin system | 🔴 DELETE |
| `bin/hub_cli.py` | 152 | Hub state JSON management | `.hermes/hub/state.json` + native config | 🔴 DELETE |
| `bin/cache_ui_assets.py` | 54 | UI asset caching | Native terminal tool + shell | 🔴 DELETE |
| `bin/container_cmd.py` | 50 | Distrobox wrapper | Native `terminal` tool in config | 🔴 DELETE |
| `hermes_core/codebase_memory_mcp.py` | ~60 | Codebase MCP server | **fastmcp** `@mcp.tool` + ast-grep-py | 🔵 REPLACE |

---

### Category 8: Agent Orchestration & Multi-Agent

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/adk_custom_agent.py` | ~80 | Google ADK BaseAgent bridge | **google-adk** upstream — this IS the thin bridge | 🟢 KEEP |
| `hermes_core/google_agentic_substrate.py` | ~200 | Tool schema registry (deprecated) | File says "Superseded by adk_custom_agent" | 🔴 DELETE |
| `hermes_core/domain_fleet.py` | ~100 | Domain fleet manager | **google-adk** `Runner` + config | 🟡 THIN SHIM |
| `hermes_core/swarm_engine.py` | ~150 | HermesOrchestrator multi-bot | **google-adk** orchestration | 🟡 THIN SHIM |
| `hermes_core/swarm_system.py` | ~100 | Role capability masks | **google-adk** agent capabilities config | 🟡 THIN SHIM |
| `hermes_core/multi_bot_delegation.py` | ~80 | Multi-bot task dispatch | **google-adk** `Runner` + `SessionService` | 🔴 DELETE |
| `hermes_core/task_graph.py` | ~150 | TaskDAG + dependency ordering | **networkx** `DiGraph` + `topological_sort` | 🔵 REPLACE |
| `hermes_core/intent_router.py` | ~80 | Prompt → bot profile routing | Native Hermes profile system + YAML | 🔴 DELETE |
| `hermes_core/agent_os.py` | ~120 | AgentOSDaemon lifecycle | **google-adk** `Runner` + native plan.json | 🟡 THIN SHIM |
| `hermes_core/agent_os_standards.py` | ~80 | Two-tier rules loader | Native `rules/` directory + `plugin_loader.py` | 🔴 DELETE |
| `hermes_core/antigravity_skills.py` | ~60 | AGY skill definitions | Native AGY skill system | 🔴 DELETE |
| `hermes_core/capability_masks.py` | ~60 | Role capability tables | **google-adk** agent config YAML | 🔴 DELETE |

---

### Category 9: Guardrails & Safety

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/nemo_guardrails_bridge.py` | ~80 | NeMo Guardrails wrapper | **nemoguardrails** `LLMRails(config, llm=...)` directly | 🟡 THIN SHIM (≤15 lines) |
| `hermes_core/sandbox.py` | ~80 | Bubblewrap bwrap subprocess | `bwrap` CLI via `subprocess.run(["bwrap", ...])` — no class | 🔴 DELETE |
| `hermes_core/hitl_gateway.py` | ~150 | HITL risk gate + diff display | **nemoguardrails** dialog rails + Colang | 🔵 REPLACE via NeMo |
| `hermes_core/security_ctf.py` | ~100 | ELF binary analysis + capstone | **capstone** + **pwntools** + native objdump CLI | 🔴 DELETE |

---

### Category 10: Inference & Performance

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/speculative_executor.py` | ~100 | Speculative decoding orchestration | llama-server `--speculative` + `--draft-model` flags | 🔴 DELETE |
| `hermes_core/prime_kernel.py` | ~80 | IPython REPL + sub-agent kernel | **ipykernel** + native subprocess | 🔵 REPLACE |
| `hermes_core/cactus.py` | ~70 | Uncertainty estimation (CACTUS) | MC dropout via **transformers** or conformal prediction | 🔵 REPLACE |
| `hermes_core/test_time_sampler.py` | ~60 | Test-time compute sampling | llama-server `temperature`/`top_k` params | 🔴 DELETE |
| `hermes_core/qwen_mm_core.py` | ~50 | Qwen multimodal core | Handled by llama-server GGUF natively | 🔴 DELETE |
| `hermes_core/prefix_cache.py` | ~80 | KV prefix cache alignment | llama-server `--cache-reuse` + static SOUL.md ordering | 🔴 DELETE |
| `hermes_core/token_engine.py` | ~80 | Token counting + context pruning | **tiktoken** (`len(enc.encode(text))`) | 🔵 REPLACE |
| `hermes_core/flatbuffers_state.py` | ~60 | FlatBuffers binary state serialization | **flatbuffers** (`pip install flatbuffers`) directly | 🔴 DELETE |
| `hermes_core/ring_buffer.py` | ~60 | Ring buffer abstract base class | `collections.deque(maxlen=N)` stdlib | 🔴 DELETE |
| `hermes_core/thread_safe_ringbuffer.py` | ~30 | Thread-safe ring buffer | `collections.deque` + `threading.Lock()` — 5 lines inline | 🔴 DELETE |

---

### Category 11: Observability & Trajectory

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/trajectory.py` | ~120 | Hash-chained event log + OpenLIT | **openlit** `openlit.init()` one line + stdlib JSONL append | 🟡 THIN SHIM (~20 lines) |

**Why**: The hash-chain logic in `trajectory.py` reinvents OpenTelemetry trace IDs. `openlit.init()` provides GPU health, LLM latency, token usage, hallucination eval — all for free with one line.

---

### Category 12: Code Utilities & Misc

| File | Lines | What It Does | Upstream Replacement | Verdict |
|:-----|:------|:-------------|:---------------------|:--------|
| `hermes_core/extract_code_mode.py` | 103 | Markdown fence stripper | stdlib `re` — 5 lines inline, or native Hermes parsing | 🔴 DELETE |
| `hermes_core/humanizer.py` | ~70 | Robotic filler stripper | SOUL.md Rule 0 (mannered prose) — no Python needed | 🔴 DELETE |
| `hermes_core/schema_anchors.py` | ~50 | Pydantic schema definitions | **pydantic** `BaseModel` directly | 🔴 DELETE |
| `hermes_core/ide_substrate.py` | ~60 | IDE event bridge | Native desktop plugin system | 🔴 DELETE |
| `hermes_core/lsp_bridge.py` | ~80 | LSP client bridge | **pylsp** / **pyright** via CLI subprocess | 🔴 DELETE |
| `hermes_core/openviking_vfs.py` | ~60 | OpenViking VFS layer | Native filesystem + chezmoi | 🔴 DELETE |
| `hermes_core/vfs.py` | ~60 | Virtual filesystem abstraction | Native filesystem | 🔴 DELETE |
| `hermes_core/repo_onboard.py` | ~80 | GitHub repo ingestion + stack detect | **ast-grep-py** + native `git clone` + shell | 🔵 REPLACE |
| `hermes_core/spec_first_planner.py` | ~100 | plan.json management | Native plan.json + **pydantic** schema | 🟡 THIN SHIM |
| `hermes_core/prompt_slotting.py` | ~100 | 4-slot system prompt builder | SOUL.md already defines slots in text; no Python needed | 🔴 DELETE |
| `hermes_core/process_guard.py` | ~60 | POSIX process group teardown | `subprocess.Popen(start_new_session=True)` + `os.killpg` — 10 lines inline | 🔴 DELETE |
| `hermes_core/plugin_manifest.py` | ~50 | Plugin YAML schema | `pydantic` + `yaml.safe_load` | 🟡 THIN SHIM |
| `hermes_core/plugin_loader.py` | ~50 | Plugin discovery + JIT load | This IS the native Hermes system | 🟢 KEEP |
| `hermes_core/presets.py` | ~40 | Token estimate + prompt presets | **tiktoken** | 🔴 DELETE |
| `hermes_core/lora_adapter.py` | ~80 | LoRA weight loading | **peft** `PeftModel.from_pretrained()` | 🔴 DELETE |
| `hermes_core/lora_adapter_manager.py` | ~80 | Multi-adapter hot-swap | **peft** `model.add_adapter()` + `model.set_adapter()` | 🔴 DELETE |
| `hermes_core/runner.py` | ~80 | Hermes CLI subprocess SDK | Native terminal tool + stdlib subprocess | 🔴 DELETE |
| `hermes_core/sdk.py` | ~60 | 5-method code mode SDK | Native Hermes terminal tool + shell commands | 🔴 DELETE |
| `hermes_core/visual_arbiter.py` | ~80 | Playwright headless HTML checker | **playwright** `async_playwright()` directly (2 lines) | 🔴 DELETE |
| `hermes_core/codebase_memory_mcp.py` | ~60 | Codebase MCP server | **fastmcp** `@mcp.tool` + **ast-grep-py** | 🔵 REPLACE |
| `types/templates/playwright_tdd_spec.py` | template | Playwright TDD boilerplate | Static template — not logic | 🟢 KEEP as template |
| `types/templates/posix_worker_pool.py` | template | Worker pool boilerplate | Static template | 🟢 KEEP as template |

---

### Upstream Package → Hermes Plugin Map

Every upstream package becomes a thin **FastMCP tool** or **Hermes plugin** — not a custom wrapper class.

| Upstream Package | GitHub | pip install | Replaces Custom Files |
|:-----------------|:-------|:------------|:----------------------|
| **fastmcp** | `jlowin/fastmcp` | `fastmcp` | `fastmcp.py`, `tools.py`, `hook_router.py`, `hooks.py`, `codebase_memory_mcp.py` |
| **crawl4ai** | `unclecode/crawl4ai` | `crawl4ai` | `web_grounding.py` (×2), `fast_research.py`, `extract_web_content.py`, `ingest_document.py`, `index_docs.py` |
| **fastembed** | `qdrant/fastembed` | `fastembed` | `embeddings.py`, `skill_retriever.py` |
| **dspy** | `stanfordnlp/dspy` | `dspy` | `gepa_optimizer.py`, `evolution.py`, `harness_evolution.py`, `skill_evaluator.py`, `skill_evolution.py`, `reflective_learner.py` |
| **ast-grep-py** | `ast-grep/ast-grep` | `ast-grep-py` | `symbol_graph.py`, `symbol_indexer.py`, `knowledge_graph.py`, `repo_onboard.py`, observer_gate AST portion |
| **graphiti-core** | `getzep/graphiti` | `graphiti-core` | `working_memory.py`, `experience_store.py` (semantic), `second_brain.py`, `cog_vault.py` |
| **openlit** | `openlit/openlit` | `openlit` | `trajectory.py` (full), `verify_transcript.py` |
| **nemoguardrails** | `NVIDIA/NeMo-Guardrails` | `nemoguardrails` | `nemo_guardrails_bridge.py`, `hitl_gateway.py`, `middleware.py`, `cog_verifier.py` |
| **sqlmodel** | `tiangolo/sqlmodel` | `sqlmodel` | `database.py`, `session_persistence.py`, experience_store SQL layer |
| **networkx** | `networkx/networkx` | `networkx` | `task_graph.py`, `graph_engine.py` |
| **tiktoken** | `openai/tiktoken` | `tiktoken` | `token_engine.py`, `presets.py` |
| **peft** | `huggingface/peft` | `peft` | `lora_adapter.py`, `lora_adapter_manager.py` |
| **gitpython** | `gitpython-developers/GitPython` | `gitpython` | `lineage.py` |
| **python-frontmatter** | `eyeseast/python-frontmatter` | `python-frontmatter` | `second_brain.py`, `cog_vault.py` |
| **google-adk** | `google/adk-python` | `google-adk` | `agent_os.py`, `domain_fleet.py`, `swarm_engine.py`, `multi_bot_delegation.py`, `google_agentic_substrate.py` |
| **playwright** | `microsoft/playwright-python` | `playwright` | `visual_arbiter.py` |

---

### Final Python File Count

| Layer | Before | After | Net Delta |
|:------|:-------|:------|:----------|
| `hermes_core/` modules | ~68 files | ~12 genuine shims | **–56** |
| `bin/` scripts | 15 files | 2 (observer_gate + verify_harness thinned) | **–13** |
| **Total custom Python** | **~83** | **~14** | **–69 files** |

### The 14 Surviving Python Files (Irreplaceable)

| File | Why It Stays |
|:-----|:-------------|
| `hermes_core/openskills_manager.py` | SKILL.md L0/L1/L2 loader — IS the Hermes skill engine |
| `hermes_core/adk_custom_agent.py` | ADK `BaseAgent` bridge — thin shim ~40 lines |
| `hermes_core/domain_fleet.py` | Domain fleet thin shim ~30 lines |
| `hermes_core/swarm_engine.py` | HermesOrchestrator thin shim ~30 lines |
| `hermes_core/plugin_loader.py` | Plugin JIT discovery — IS the native system |
| `hermes_core/plugin_manifest.py` | Plugin YAML schema — thin shim ~20 lines |
| `hermes_core/agent_os.py` | AgentOS lifecycle thin shim ~20 lines |
| `hermes_core/spec_first_planner.py` | plan.json manager thin shim ~30 lines |
| `hermes_core/nemo_guardrails_bridge.py` | NeMo init thin shim ~15 lines |
| `hermes_core/hypothesis_tree.py` | MCTS node tracker thin shim ~40 lines |
| `hermes_core/trajectory.py` | `openlit.init()` + JSONL append ~20 lines |
| `hermes_core/experience_store.py` | SQLModel episode schema ~30 lines |
| `bin/observer_gate.py` | Pre-commit gate runner ~50 lines (calls ast-grep-py) |
| `bin/verify_harness_integrity.py` | Pytest capability runner ~30 lines (calls pytest) |

---

### Phase 7: Upstream Migration Steps

> Run after Phases 0–6. Each step is a git commit. No new Python files created.

**7.1 — Install Upstream Packages**
```bash
pip install fastmcp crawl4ai fastembed "dspy-ai" ast-grep-py graphiti-core openlit \
            nemoguardrails sqlmodel networkx tiktoken peft gitpython \
            python-frontmatter google-adk playwright
```

**7.2 — Delete Pure Wrapper Files (~55 files)**
- All 🔴 DELETE files from the audit above.
- Before each delete: `grep -r "from hermes_core.<name>" .hermes/` to confirm no imports remain.

**7.3 — Thin-Shim Replacements (~13 files, each ≤30 lines)**
- Strip all custom logic from 🟡 THIN SHIM files.
- Replace with direct upstream `import` + single function call.

**7.4 — Single FastMCP Tool Server**
Create `.hermes/plugins/mcp_tools/__init__.py` (~60 lines total):
```python
from fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler
from ast_grep_py import SgRoot

mcp = FastMCP("hermes-tools")

@mcp.tool
async def web_extract(url: str, word_limit: int = 500) -> str:
    async with AsyncWebCrawler() as c:
        r = await c.arun(url=url, word_count_threshold=word_limit)
        return r.markdown

@mcp.tool
def ast_search(pattern: str, code: str, lang: str = "python") -> list[dict]:
    root = SgRoot(code, lang)
    return [{"text": n.text(), "range": str(n.range())} for n in root.root().find_all(pattern)]
```
This single file replaces `web_grounding.py`, `fast_research.py`, `extract_web_content.py`, `tools.py`, `fastmcp.py`.

**7.5 — Wire DSPy to GEPA Plugin**
Edit `plugins/gepa_optimizer/hooks/on_session_end.py` (~25 lines):
```python
import dspy
from dspy.teleprompt import MIPROv2
# Load failed episodes as training set, SOUL.md as program
# MIPROv2 auto-optimizes → writes improved rules back to SOUL.md
```

**7.6 — Wire Graphiti for Working Memory**
Edit `plugins/reflective_learner_adapter/hooks/on_session_end.py` (~20 lines):
```python
from graphiti_core import Graphiti
# g.add_episode(name=session_id, episode_body=summary, ...)
```

**7.7 — Wire OpenLIT**
Reduce `hermes_core/trajectory.py` to ~20 lines:
```python
import openlit
openlit.init(otlp_endpoint="http://localhost:4318", application_name="hermes")
```

**7.8 — Commit + Chezmoi Sync**
```bash
chezmoi add .hermes/src/hermes_core/ .hermes/bin/ .hermes/plugins/
chezmoi git -- add -A
chezmoi git -- commit -m "refactor(hermes-core): upstream migration — 69 files deleted, 13 thinned, 0 new"
```

---

## Deep Audit: `.hermes/src` Structure, Types, Templates & Packaging

> **Goal**: Audit the non-core assets inside `.hermes/src/` (types, templates, egg-info, packaging metadata) and eliminate custom file sprawl by leveraging standard package conventions and plugin asset loading.

### 1. Structure of `.hermes/src`
```
.hermes/src/
├── hermes_core/               # ~68 custom Python modules (audited above)
│   ├── types/
│   │   ├── nodejs/nodejs_types.types          # Static TypeScript/Node.js definitions
│   │   ├── posix/posix_types.types            # Static POSIX C/Rust type definitions
│   │   ├── threejs/threejs_types.types        # Static Three.js WebGL definitions
│   │   └── templates/
│   │       ├── playwright_tdd_spec.py         # Static Playwright test template
│   │       ├── posix_worker_pool.py           # Static POSIX multiprocessing template
│   │       └── webgl_canvas_boilerplate.html  # Static WebGL canvas HTML template
│   └── templates/                             # Empty directory
└── hermes_harness.egg-info/                   # Setuptools metadata generated by editable pip install
```

### 2. Audit Findings for `.hermes/src` Assets

| Asset / Directory | Type | What It Does | Upstream / Native Replacement | Verdict |
|:------------------|:-----|:-------------|:------------------------------|:--------|
| `types/nodejs/nodejs_types.types` | Static text | Static Node.js type definitions injected into model prompts | Move to skill: `private_skills/software-development/node-inspect-debugger/` as a resource | 🔄 **RELOCATE TO SKILL** |
| `types/posix/posix_types.types` | Static text | Static POSIX type definitions | Move to skill: `private_skills/devops/` as a resource | 🔄 **RELOCATE TO SKILL** |
| `types/threejs/threejs_types.types` | Static text | Static Three.js WebGL type definitions | Move to skill: `private_skills/software-development/generative-ui-artifact/` | 🔄 **RELOCATE TO SKILL** |
| `types/templates/playwright_tdd_spec.py` | Python template | Boilerplate fixture for Playwright TDD runs | Move to `private_skills/software-development/test-driven-development/resources/` | 🔄 **RELOCATE TO SKILL** |
| `types/templates/posix_worker_pool.py` | Python template | Boilerplate code for multiprocessing pools | Move to `private_skills/devops/` | 🔄 **RELOCATE TO SKILL** |
| `types/templates/webgl_canvas_boilerplate.html` | HTML template | HTML5 WebGL canvas boilerplate | Move to `private_skills/software-development/generative-ui-artifact/resources/` | 🔄 **RELOCATE TO SKILL** |
| `hermes_core/templates/` | Directory | Empty directory leftover from legacy template loader | Remove empty directory | 🔴 **DELETE** |
| `hermes_harness.egg-info/` | Package build | Build artifacts generated by `pip install -e .` | Add to `.gitignore`, do not track in chezmoi | 🔴 **UNTRACK** |
| `pyproject.toml` | Build config | Defines harness dependencies (`google-adk`, `nemoguardrails`, `fastmcp`, `crawl4ai`, `openlit`, `sqlmodel`, etc.) | **KEEP & CLEAN**: pyproject.toml already declares the upstream packages. Update entry points and remove stale package globs (`hermes_sdk*`) | 🟢 **KEEP & CLEAN** |

**Key Architectural Principle**: Code templates and type-definition lookup files are **skill resources**, not Python package source code. Moving them into their respective `SKILL.md/resources/` folders eliminates the artificial `types/` sub-tree inside `src/` and lets them be loaded JIT via OpenSkills progressive disclosure rather than baking them into the Python runtime.

---

## Deep Audit: `.hermes/tests/` (All 25 Files, 4,722 Lines)

> **Core Problem**: `.hermes/tests/` contains 25 white-box unit test files with 4,722 lines of code. Virtually all of them test **our custom reimplementations of things that upstream packages already do**. For example, 637 lines test a bespoke Tree-Sitter SQLite indexer; 526 lines test a bespoke DAG topological sort; 325 lines test bubblewrap CLI construction.
>
> When we replace custom modules with battle-tested upstream libraries (`ast-grep-py`, `networkx`, `crawl4ai`, `dspy`, `fastmcp`, `openlit`), we should **not** write unit tests for the upstream library itself. Instead, tests should verify **behavioral invariants and plugin contracts**.

### Audit Legend
- 🔴 **DELETE TEST** — Tests a deleted/redundant custom implementation. The upstream package has its own extensive test suite. Zero value in keeping bespoke tests.
- 🟡 **REFOUND AS CONTRACT TEST** — Rewrite into a thin (≤25 lines) test verifying the integration contract between Hermes and the upstream package/plugin.
- 🟢 **KEEP AS INVARIANT TEST** — Tests a critical local hardware/safety invariant (e.g. VRAM ceiling, zero-sorry output, token budget bounds).

---

### Category 1: Agent & Orchestration Tests (`tests/agent/` — 5 files, 1,242 lines)

| Test File | Lines | What It Currently Tests | Underlying Module | Upstream Replacement | Verdict & Action |
|:----------|:------|:------------------------|:------------------|:---------------------|:-----------------|
| `tests/agent/test_task_graph.py` | 526 | Custom DAG resolution, cycle detection, self-loops, diamond dependencies, task retry counts, SQLite WAL state | `hermes_core/task_graph.py` | **networkx** (`DiGraph`, `simple_cycles`, `topological_sort`) | 🟡 **REFOUND** (~30 lines): Test that task lists convert to `networkx.DiGraph` and reject cycles. Delete 496 lines of custom DAG traversal tests. |
| `tests/agent/test_branch_swapper.py` | 292 | Custom SQLite branch swap logic, 2-strike consecutive failure counters, tabu pattern injection | `hermes_core/branch_swapper.py` | `quorum_audit` plugin `pre_commit` hook | 🟡 **REFOUND** (~25 lines): Test that plugin pre-commit hook aborts turn on 2 consecutive test failures. Delete custom DB tests. |
| `tests/agent/test_adk_orchestrator.py` | 273 | ADK CustomAgent bridge, Event streaming, transfer_to_agent transitions, InMemorySessionService | `hermes_core/adk_custom_agent.py` | **google-adk** upstream | 🟢 **KEEP AS INVARIANT** (~60 lines): Verify `HermesADKCustomAgent` satisfies ADK `BaseAgent` protocol and preserves tool state across transfers. |
| `tests/agent/test_domain_fleet_adk.py` | 83 | DomainFleetManager team dictionary, sub-agent spawning, pipeline composition | `hermes_core/domain_fleet.py` | **google-adk** `Runner` | 🟡 **REFOUND** (~20 lines): Verify fleet registry produces valid ADK agent configurations. |
| `tests/agent/test_agent_os.py` | 68 | AgentOSDaemon lifecycle, SQLite queue table, daemon background loops | `hermes_core/agent_os.py` | **google-adk** + plan.json | 🔴 **DELETE**: AgentOS daemon loop is replaced by ADK runner; no custom daemon process. |

---

### Category 2: Core Subsystem Tests (`tests/core/` — 11 files, 1,607 lines)

| Test File | Lines | What It Currently Tests | Underlying Module | Upstream Replacement | Verdict & Action |
|:----------|:------|:------------------------|:------------------|:---------------------|:-----------------|
| `tests/core/test_cli.py` | 357 | Custom CLI flags, capability selectors (plan/execute/verify phases), progress reporting, token savings | `hermes_core/cli.py` | Upstream Hermes CLI + Click/Typer | 🟡 **REFOUND** (~40 lines): Test Hermes CLI invokes correct profile and respects `--yolo` / `--in`. |
| `tests/core/test_cactus_uncertainty.py` | 180 | Verbal hedging regex, action risk scoring, streak weighting, autonomous halt | `hermes_core/cactus.py` + `loop_contracts.py` | `config.yaml` guardrails + NeMo dialog rails | 🔴 **DELETE**: Replaced by config-level guardrails (`tool_loop_guardrails.hard_stop_enabled`) and NeMo rails. |
| `tests/core/test_lora_adapter_manager.py` | 164 | Custom LoRA manager, VRAM rejection limits, single active adapter hot-swapping | `hermes_core/lora_adapter_manager.py` | **peft** (`add_adapter`, `set_adapter`) | 🟡 **REFOUND** (~25 lines): Verify `peft` adapter switching doesn't exceed VRAM limits. |
| `tests/core/test_graphify_bridge.py` | 137 | Knowledge card Markdown frontmatter persistence, SecondBrain vault CRUD, graphify skill discovery | `hermes_core/second_brain.py` + `skill_router.py` | **python-frontmatter** + graphify skill | 🟡 **REFOUND** (~20 lines): Verify graphify Markdown cards have valid YAML frontmatter. |
| `tests/core/test_vision_token_budget.py` | 137 | Image downsampling math, Gemma vision token formula, optimal patch grid calculation | `hermes_core/visual_arbiter.py` | Pillow `Image.resize` directly | 🟢 **KEEP AS INVARIANT** (~40 lines): Enforce local vision token budget formula (max 1024 tokens/image on 6GB GPU). |
| `tests/core/test_draft_detective_aps.py` | 128 | Gemma-APS proposition segmentation, AST verification of claims, hallucination detection in summaries | `hermes_core/draft_detective.py` | **ast-grep-py** AST matching | 🟡 **REFOUND** (~30 lines): Verify AST verification catches non-existent function calls in generated patches. |
| `tests/core/test_quorum_and_gepa.py` | 120 | Quorum audit gate separation, blast radius calculation, GEPALiteOptimizer Pareto candidates | `hermes_core/quorum_gate.py` + `gepa_optimizer.py` | **dspy** `MIPROv2` + `quorum_audit` plugin | 🟡 **REFOUND** (~25 lines): Verify quorum audit gate returns REJECT when blast radius exceeds threshold. |
| `tests/core/test_gemma_skills.py` | 109 | SKILL.md L0 discovery tokens (<50 tok), L1 dynamic loading, L2 eviction, asset syntax | `hermes_core/openskills_manager.py` | `openskills_manager.py` (kept) | 🟢 **KEEP AS INVARIANT** (109 lines): Enforces critical token budget invariant (<50 tokens/skill discovery line). |
| `tests/core/test_experience_store.py` | 99 | Episodic memory JSONL + SQLModel saving, compute waste detection, negative constraint generation | `hermes_core/experience_store.py` | **sqlmodel** directly | 🟡 **REFOUND** (~20 lines): Verify SQLModel episode insertion and query. |
| `tests/core/test_persistence.py` | 86 | SQLite connection factory WAL mode pragmas, FlatBuffers binary serialization speed (<100μs) | `hermes_core/database.py` + `flatbuffers_state.py` | **sqlmodel** + stdlib | 🔴 **DELETE**: SQLModel handles connections; FlatBuffers custom serialization is eliminated. |
| `tests/core/test_security_delegation.py` | 62 | Trinity isolation, read-only capability masks, HITL risk assessment, test-time compute scoring | `hermes_core/capability_masks.py` | ADK agent capability config | 🟡 **REFOUND** (~20 lines): Verify read-only agent roles cannot call file-write tools. |

---

### Category 3: Monitoring & Safety Tests (`tests/monitoring/` & `tests/safety/` — 5 files, 965 lines)

| Test File | Lines | What It Currently Tests | Underlying Module | Upstream Replacement | Verdict & Action |
|:----------|:------|:------------------------|:------------------|:---------------------|:-----------------|
| `tests/safety/test_sandbox.py` | 325 | Bubblewrap CLI flag assembly, read-only `/usr` binds, writable `/dev/shm`, setsid process groups | `hermes_core/sandbox.py` + `process_guard.py` | Direct `bwrap` execution | 🟢 **KEEP AS INVARIANT** (~40 lines): Verify untrusted command execution cannot write outside designated workspace. |
| `tests/monitoring/test_trajectory_openlit.py` | 216 | OpenTelemetry custom span creation, hash-chain immutability, gate rejection span error status | `hermes_core/trajectory.py` | **openlit** (`openlit.init()`) | 🟡 **REFOUND** (~30 lines): Verify `openlit` emits spans to local collector on LLM turn. Delete bespoke hash-chain tests. |
| `tests/safety/test_nemo_guardrails.py` | 200 | NeMo Colang 1.0 config discovery, input rails blocking `rm -rf`, output rails redacting API keys | `hermes_core/nemo_guardrails_bridge.py` | **nemoguardrails** directly | 🟢 **KEEP AS INVARIANT** (~50 lines): Verify destructive command patterns and secret leak patterns are blocked. |
| `tests/safety/test_security_ctf.py` | 126 | ELF binary header parsing, mitigation checks (NX, PIE, Canary), ASCII/Unicode string extraction | `hermes_core/security_ctf.py` | **pwntools** / **capstone** | 🔴 **DELETE**: Custom ELF parser is deleted in favor of CLI tools; no custom Python to test. |
| `tests/safety/test_hitl_gateway.py` | 98 | Risk classification (LOW..CRITICAL), visual DAG ASCII dashboard, auto-approval vs interactive block | `hermes_core/hitl_gateway.py` | NeMo dialog rails + `--yolo` flag | 🔴 **DELETE**: Custom ASCII dashboard and gateway are replaced by NeMo rails + native CLI. |

---

### Category 4: Tools & Transports Tests (`tests/tools/` — 3 files, 908 lines)

| Test File | Lines | What It Currently Tests | Underlying Module | Upstream Replacement | Verdict & Action |
|:----------|:------|:------------------------|:------------------|:---------------------|:-----------------|
| `tests/tools/test_symbol_graph.py` | 637 | Custom polyglot Tree-Sitter symbol extraction, call hierarchy, reverse callers, incremental mtime cache, SQLite WAL tables | `hermes_core/symbol_graph.py` | **ast-grep-py** (`SgRoot`) + **graphify** | 🔴 **DELETE** (637 lines!): Testing our bespoke Tree-Sitter AST extractor is completely obsolete when using `ast-grep-py` / `graphify`. Replace with a 15-line test in contracts. |
| `tests/tools/test_fast_research.py` | 195 | Custom regex HTML cleaner, malformed HTML handling, token bounding (<400 tok), query deduplication | `hermes_core/fast_research.py` | **crawl4ai** `AsyncWebCrawler` | 🔴 **DELETE**: Crawl4AI handles HTML→Markdown, deduplication, and word thresholds natively with its own test suite. |
| `tests/tools/test_fastmcp_transport.py` | 96 | In-memory FastMCP tool dispatch latency (<5ms), multi-hop proxying, schema generation | `hermes_core/fastmcp.py` | **fastmcp** upstream | 🟡 **REFOUND** (~20 lines): Verify FastMCP server exposes registered tools and dispatches calls correctly. |

---

### Test Suite Comparison: Before vs After

| Test Directory | Current Files | Current Lines | Post-Refactor Files | Target Lines | Net Reduction |
|:---------------|:--------------|:--------------|:-------------------|:-------------|:--------------|
| `tests/agent/` | 5 | 1,242 | 3 | ~135 | **–1,107 lines (–89%)** |
| `tests/core/` | 11 | 1,607 | 7 | ~220 | **–1,387 lines (–86%)** |
| `tests/monitoring/` | 1 | 216 | 1 | ~30 | **–186 lines (–86%)** |
| `tests/safety/` | 4 | 749 | 2 | ~90 | **–659 lines (–88%)** |
| `tests/tools/` | 3 | 908 | 1 | ~20 | **–888 lines (–98%)** |
| `conftest.py` | 1 | 8 | 1 | 8 | 0 |
| **Total `.hermes/tests/`** | **25 files** | **4,722 lines** | **15 files** | **~503 lines** | **–4,219 lines (–89%)** |

### What Replaces the 4,219 Lines of Deleted Tests?
1. **Upstream Package CI**: `ast-grep`, `networkx`, `crawl4ai`, `dspy`, `fastmcp`, `nemoguardrails`, `sqlmodel`, and `openlit` maintain thousands of unit tests upstream. We stop maintaining duplicate unit tests for their functionality.
2. **Lean Contract Tests**: The ~503 lines that remain focus exclusively on **Hermes integration invariants**:
   - Hardware constraints: VRAM budget ≤ 4,812 MiB, image vision tokens ≤ 1,024
   - Safety constraints: Bubblewrap isolation, NeMo prompt injection / destructive command blocks
   - Agent standards: SKILL.md discovery budget ≤ 50 tokens/skill, ADK agent transfer integrity
   - Plugin verification: Quorum gate pre-commit rejection on high blast radius

---

## Phase 8: Test Suite Modernization & Harmonization

> **Run concurrently with Phase 7 upstream package adoption.**

**8.1 — Relocate Skill Resources from `src/hermes_core/types/`**
- Move `.types` and boilerplate files to their respective `private_skills/*/resources/` directories.
- Delete `types/` sub-tree from `src/hermes_core/`.

**8.2 — Purge Obsolete White-Box Tests (6 files, 1,777 lines)**
```bash
rm .hermes/tests/tools/test_symbol_graph.py       # 637L: custom Tree-Sitter SQLite indexer
rm .hermes/tests/tools/test_fast_research.py      # 195L: custom HTML cleaner
rm .hermes/tests/core/test_persistence.py         # 86L: custom FlatBuffers & DB factory
rm .hermes/tests/core/test_cactus_uncertainty.py  # 180L: custom hedging regex
rm .hermes/tests/safety/test_security_ctf.py      # 126L: custom ELF parser
rm .hermes/tests/safety/test_hitl_gateway.py      # 98L: custom ASCII DAG dashboard
rm .hermes/tests/agent/test_agent_os.py           # 68L: custom daemon loops
```

**8.3 — Refactor Remaining 15 Test Files to Upstream Contracts**
- Update imports to use direct upstream packages (`networkx`, `fastmcp`, `openlit`, `sqlmodel`, `dspy`, `nemoguardrails`).
- Replace mock assertion boilerplate with simple input/output contract checks.

**8.4 — Harmonize with Root `tests/harness_contracts/`**
- Ensure `pytest .hermes/tests` and `pytest tests/harness_contracts` both execute cleanly under `make test-contracts`.
- Configure `pyproject.toml` `[tool.pytest.ini_options]` to discover both suites uniformly.

**8.5 — Commit + Chezmoi Sync**
```bash
chezmoi add .hermes/tests/ .hermes/src/
chezmoi git -- add -A
chezmoi git -- commit -m "test(hermes): harmonize test suite — purge 4.2k lines obsolete mock tests, refactor to upstream contracts"
```
