# Hermes Documentation Index

This directory organizes all architectural roadmaps, research specifications, operational manuals, and knowledge bases for Hermes Agent OS.

---

## Directory Organization

```
docs/
├── roadmaps/             # Architectural roadmaps organized by lifecycle state
│   ├── active/           # 🟢 CURRENT WORK: Roadmap 4 (U45–U60)
│   │   └── roadmap4_frontier_cognitive_os.md
│   ├── completed/        # 🔒 CERTIFIED & CLOSED: Roadmaps 1, 2, and 3
│   │   ├── roadmap1_master_test_plan.md
│   │   ├── roadmap2_agent_os_substrate.md
│   │   └── roadmap3_production_graduation.md
│   └── README.md         # Roadmaps index & state overview
│
├── operations/           # Practical manuals for running, monitoring, and debugging
│   ├── agent_environment_context.md
│   ├── agent_operations_guide.md
│   └── agent_milestones_and_gaps.md
│
├── research/             # Technical deep dives, failure mode analyses, and benchmark specs
│   ├── single_binary_tool_calling.md
│   ├── prompt_decomposition_and_dag.md
│   ├── failure_modes_and_edge_cases.md
│   ├── benchmark_parity_specification.md
│   └── hardware_calibrated_test_runners.md
│
├── knowledge/            # Cognitive codebooks, reference guides, and archives
│   ├── cognitive_process_codebook.md
│   ├── process_knowledge_base.md
│   ├── research_index.md
│   └── archive/          # Historical orchestration logs & raw transcripts
│       └── orchestrator_ledger.md
│
├── migration/            # Container migration records & history
│   └── archive/
│       └── migration_history.md
│
└── prompts/              # System prompts and baseline persona definitions
    └── codex_system_prompt.md
```

---

## Quick State Navigation for AI Agents

* **Active Engineering Focus**:
  * 🟢 **[Roadmap 4: Frontier Cognitive OS (U45–U60)](./roadmaps/active/roadmap4_frontier_cognitive_os.md)**

* **Completed & Certified Baselines (Reference Only)**:
  * 🔒 **[Roadmap 1: Master Test Plan (U1–U20)](./roadmaps/completed/roadmap1_master_test_plan.md)**
  * 🔒 **[Roadmap 2: Agent OS Substrate (U21–U35)](./roadmaps/completed/roadmap2_agent_os_substrate.md)**
  * 🔒 **[Roadmap 3: Production Graduation (U36–U44)](./roadmaps/completed/roadmap3_production_graduation.md)**

* **Operations & Runtime Manuals**:
  * 📘 **[Environment Context](./operations/agent_environment_context.md)**
  * 📘 **[Operations Guide](./operations/agent_operations_guide.md)**
  * 📘 **[Milestones & Gaps](./operations/agent_milestones_and_gaps.md)**
