# Hermes Documentation Index

This directory organizes all specifications, conventions, research papers, and roadmaps for Hermes Agent OS in a streamlined, 3-folder architecture.

---

## Directory Organization

```
docs/
├── conventions/           # Authoritative rules, hardware defaults, and operational invariants
│   ├── master_operating_standard.md  # Unified cognitive agent operating standard & lifecycle
│   ├── defaults_and_hardware.md      # Physical hardware bounds, VRAM limits & paths
│   └── rules_and_conventions.md      # Non-negotiable architectural rules & 4-step lifecycle
│
├── research/              # Consolidated technical deep dives, research briefs & knowledge bases
│   ├── 01_anthropic_system_prompts.md ... 13_perplexity_local_first_and_openskills.md
│   ├── single_binary_tool_calling.md
│   ├── prompt_decomposition_and_dag.md
│   ├── failure_modes_and_edge_cases.md
│   ├── benchmark_parity_specification.md
│   ├── hardware_calibrated_test_runners.md
│   ├── cognitive_process_codebook.md
│   ├── process_knowledge_base.md
│   └── research_index.md
│
└── roadmaps/              # Architectural roadmaps (Roadmaps 1–5 complete & certified)
    ├── roadmap1_master_test_plan.md
    ├── roadmap2_agent_os_substrate.md
    ├── roadmap3_production_graduation.md
    ├── roadmap4_frontier_cognitive_os.md
    └── roadmap5_frontier_multiagent_web_intelligence.md
```

---

## Quick Navigation for AI Agents

* **Master Agent Operating Standard**:
  * 📘 **[AGENTS.md](../AGENTS.md)** (Root authoritative prompt & single-source-of-truth for all agents)
* **Conventions & System Defaults**:
  * 📋 **[Rules & Conventions](./conventions/rules_and_conventions.md)**
  * 🖥️ **[Defaults & Hardware Bounds](./conventions/defaults_and_hardware.md)**
  * 📜 **[Master Operating Standard](./conventions/master_operating_standard.md)**
* **Architectural Roadmaps**:
  * 🗺️ **[Roadmap 5: Multi-Agent Web Intelligence (U61–U80)](./roadmaps/roadmap5_frontier_multiagent_web_intelligence.md)**
  * 🗺️ **[Roadmap 4: Frontier Cognitive OS (U45–U60)](./roadmaps/roadmap4_frontier_cognitive_os.md)**
  * 🗺️ **[Roadmap 3: Production Graduation (U36–U44)](./roadmaps/roadmap3_production_graduation.md)**
  * 🗺️ **[Roadmap 2: Agent OS Substrate (U21–U35)](./roadmaps/roadmap2_agent_os_substrate.md)**
  * 🗺️ **[Roadmap 1: Master Test Plan (U1–U20)](./roadmaps/roadmap1_master_test_plan.md)**
* **Technical Research**:
  * 🔬 **[Research Directory](./research/)**
