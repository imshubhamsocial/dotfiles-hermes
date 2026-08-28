"""
Hermes Living Agent Harness (100% Universal Ground-Up Architecture)
===================================================================
Incorporating:
  - OpenAI Swarm Dynamic Functional Handoffs & Context Variables
  - Claude Code Ephemeral Scratchpads & Non-Regression Invariant Gates
  - DeepSeek Deterministic AST Extraction & Sliced Non-Destructive Patching
"""

from .agent import Agent, Response, Result, AgentFunction
from .swarm_engine import HermesOrchestrator
from .middleware import FableMiddleware, MythosCognitiveGovernor
from .hypothesis_tree import HypothesisTree, HypothesisNode
from .working_memory import WorkingMemoryAnchor, FastASTPreCommitGate
from .skills_registry import PluggableSkillRegistry, ProjectGrader
from .symbol_indexer import SymbolIndexer
from .symbol_graph import (
    SymbolGraph,
    create_ramdisk_graph,
    create_persistent_graph,
    create_memory_graph
)
from .knowledge_graph import KnowledgeGraphIndexer, CodebaseKnowledgeGraph, CodeNode
from .task_graph import (
    TaskGraph, SubTask, HardwareBudgets,
    TaskDAG, TaskStatus, CycleDetectedError,
    create_persistent_dag, create_ephemeral_dag, create_memory_dag
)
from .session_persistence import DurableSessionState, NodeReceipt, ArtifactReceipt
from .fast_research import FastWebResearchEngine, create_fast_research_engine
from .security_ctf import SecurityCTFToolsuite, parse_elf_header, extract_strings
from .embeddings import CPUNeuralEmbeddingEngine, create_cpu_embedding_engine
from .skills_catalog import SkillsCatalogManager, create_skills_catalog_manager
from .hitl_gateway import HITLSupervisoryGateway, create_hitl_gateway, RiskLevel, ApprovalVerdict
from .repo_onboard import RepoOnboarder, create_repo_onboarder
from .lsp_bridge import LiveLSPBridge, create_lsp_bridge, DiagnosticSeverity
from .harness_evolution import HarnessEvolutionEngine, ExecutionPolicy, create_harness_evolution_engine
from .skill_evaluator import SkillEvaluator, create_skill_evaluator
from .experience_store import ExperienceStore, create_experience_store
from .agent_os import AgentOSDaemon, create_agent_os_daemon
from .prime_kernel import PrimePythonKernel, create_prime_kernel
from .continual_refine import ContinualRefineLoop, create_continual_refine_loop
from .tools import (
    read_file, write_file, patch_file, execute_command, 
    run_test_suite, search_web, get_symbol_map, 
    get_workspace_tree, get_task_status, update_task_progress,
    query_knowledge_graph, grep_codebase, refactor_symbol
)

__all__ = [
    "Agent", "Response", "Result", "AgentFunction",
    "HermesOrchestrator", "FableMiddleware", "MythosCognitiveGovernor",
    "HypothesisTree", "HypothesisNode",
    "WorkingMemoryAnchor", "FastASTPreCommitGate",
    "PluggableSkillRegistry", "ProjectGrader",
    "SymbolIndexer", "SymbolGraph",
    "create_ramdisk_graph", "create_persistent_graph", "create_memory_graph",
    "KnowledgeGraphIndexer", "CodebaseKnowledgeGraph", "CodeNode", 
    "TaskGraph", "SubTask", "HardwareBudgets",
    "TaskDAG", "TaskStatus", "CycleDetectedError",
    "create_persistent_dag", "create_ephemeral_dag", "create_memory_dag",
    "DurableSessionState", "NodeReceipt", "ArtifactReceipt",
    "FastWebResearchEngine", "create_fast_research_engine",
    "SecurityCTFToolsuite", "parse_elf_header", "extract_strings",
    "CPUNeuralEmbeddingEngine", "create_cpu_embedding_engine",
    "SkillsCatalogManager", "create_skills_catalog_manager",
    "HITLSupervisoryGateway", "create_hitl_gateway", "RiskLevel", "ApprovalVerdict",
    "RepoOnboarder", "create_repo_onboarder",
    "LiveLSPBridge", "create_lsp_bridge", "DiagnosticSeverity",
    "HarnessEvolutionEngine", "ExecutionPolicy", "create_harness_evolution_engine",
    "SkillEvaluator", "create_skill_evaluator",
    "ExperienceStore", "create_experience_store",
    "AgentOSDaemon", "create_agent_os_daemon",
    "PrimePythonKernel", "create_prime_kernel",
    "ContinualRefineLoop", "create_continual_refine_loop",
    "read_file", "write_file", "patch_file", "execute_command", 
    "run_test_suite", "search_web", "get_symbol_map", 
    "get_workspace_tree", "get_task_status", "update_task_progress",
    "query_knowledge_graph", "grep_codebase", "refactor_symbol"
]

# U36: Context Sieve
from .context_sieve import ContextSieve, create_ramdisk_sieve

# U37: CLI
from .cli import HermesCLI, main

# U38: Branch Swapper
from .branch_swapper import BranchSwapper, create_branch_swapper, RepairTurn, TabuPattern, NegativeConstraint, SwapTrigger

# U39: Visual Arbiter
from .visual_arbiter import VisualArbiter, create_visual_arbiter, run_visual_check, VisualReport, KinematicResult, PLAYWRIGHT_AVAILABLE, RAMDISK_BASE
