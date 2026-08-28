# Hermes Documentation Index

This directory organizes all architectural roadmaps, research specifications, operational manuals, and knowledge bases for Hermes Agent OS.

---

## Directory Organization

```
docs/
├── roadmaps/             # Architectural roadmaps organized by lifecycle state
│   ├── active/           # 🟢 Ready for Roadmap 6+
│   ├── completed/        # 🔒 CERTIFIED & CLOSED: Roadmaps 1–5 & Research Briefs
│   │   ├── roadmap1_master_test_plan.md
│   │   ├── roadmap2_agent_os_substrate.md
│   │   ├── roadmap3_production_graduation.md
│   │   ├── roadmap4_frontier_cognitive_os.md
│   │   ├── roadmap5_frontier_multiagent_web_intelligence.md
│   │   └── 01_anthropic_system_prompts.md ... (13 research briefs)
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
└── prompts/              # System prompts and operational guides
    ├── 00_master_session_startup_prompt.md
    ├── 01_environment_and_hardware.md
    ├── 02_rules_conventions_and_standards.md
    └── completed/        # Completed milestone execution prompts (U60 Capstone)
```

---

## Quick State Navigation for AI Agents

* **Active Engineering Focus**:
  * 🟢 **[Roadmaps Workspace](./roadmaps/README.md)** (Roadmaps 1–5 complete; ready for Roadmap 6+)

* **Completed & Certified Baselines (Reference Only)**:
  * 🔒 **[Roadmap 5: Multi-Agent Web Intelligence (U61–U80)](./roadmaps/completed/roadmap5_frontier_multiagent_web_intelligence.md)**
  * 🔒 **[Roadmap 4: Frontier Cognitive OS (U45–U60)](./roadmaps/completed/roadmap4_frontier_cognitive_os.md)**
  * 🔒 **[Roadmap 3: Production Graduation (U36–U44)](./roadmaps/completed/roadmap3_production_graduation.md)**
  * 🔒 **[Roadmap 2: Agent OS Substrate (U21–U35)](./roadmaps/completed/roadmap2_agent_os_substrate.md)**
  * 🔒 **[Roadmap 1: Master Test Plan (U1–U20)](./roadmaps/completed/roadmap1_master_test_plan.md)**

* **Operations & Runtime Manuals**:
  * 📘 **[Environment Context](./operations/agent_environment_context.md)**
  * 📘 **[Operations Guide](./operations/agent_operations_guide.md)**
  * 📘 **[Milestones & Gaps](./operations/agent_milestones_and_gaps.md)**
