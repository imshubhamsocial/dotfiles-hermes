#!/usr/bin/env python3
"""
Verification Script for Phase 1: MRP Planning & Ponytail YAGNI Ladder
=====================================================================
Executes in-process contract verification against:
  1. PonytailLadder 7-Rung Classification
  2. PonytailDiffPruner AST Over-Engineering Detection
  3. TaskDependencyGraph Topological Sorting (Kahn's Algorithm)
  4. Circular Dependency Detection (CycleDetectedError)
  5. Parallel Wave Partitioning
  6. End-to-End MRP Planning Pipeline & Mermaid Generation
"""

import json
import os
import sys
from pathlib import Path

# Resolve hermes-agent path dynamically
_hermes_dir = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parents[1]))
for p in [
    _hermes_dir / "hermes-agent",
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.ponytail_ladder import (
    YAGNIRung,
    PonytailLadder,
    audit_code_simplicity,
)
from agent.core.mrp_planner import (
    CycleDetectedError,
    TaskDependencyGraph,
    TaskNode,
    create_mrp_plan,
)


def verify_ponytail_ladder() -> None:
    print("[1/6] Verifying Ponytail 7-Rung Ladder classification...")
    
    # Rung 1: Speculative gold-plating
    r1, note1 = PonytailLadder.evaluate_intent("Build a speculative wrapper just in case we need it later")
    assert r1 == YAGNIRung.RUNG_1_YAGNI, f"Expected Rung 1, got {r1}"
    assert "Do not build" in note1

    # Rung 2: Codebase reuse
    r2, note2 = PonytailLadder.evaluate_intent(
        "Compute hash using symbol_indexer",
        existing_symbols=["symbol_indexer", "moba_context_router"]
    )
    assert r2 == YAGNIRung.RUNG_2_CODEBASE_REUSE, f"Expected Rung 2, got {r2}"
    assert "symbol_indexer" in note2

    # Rung 3: Standard library
    r3, note3 = PonytailLadder.evaluate_intent("Read file content from disk using pathlib")
    assert r3 == YAGNIRung.RUNG_3_STDLIB, f"Expected Rung 3, got {r3}"

    # Rung 4: Native OS
    r4, note4 = PonytailLadder.evaluate_intent("Execute grep and diff on target directory")
    assert r4 == YAGNIRung.RUNG_4_NATIVE_OS, f"Expected Rung 4, got {r4}"

    # Rung 5: Installed dependency
    r5, note5 = PonytailLadder.evaluate_intent("Validate schema with pydantic", installed_packages=["pydantic", "rich"])
    assert r5 == YAGNIRung.RUNG_5_DEPENDENCY, f"Expected Rung 5, got {r5}"

    # Rung 6: Single line
    r6, note6 = PonytailLadder.evaluate_intent("Filter active users from list")
    assert r6 == YAGNIRung.RUNG_6_ONE_LINE, f"Expected Rung 6, got {r6}"

    # Rung 7: Minimal code
    r7, note7 = PonytailLadder.evaluate_intent("Design novel token scheduling algorithm for distributed cluster")
    assert r7 == YAGNIRung.RUNG_7_MINIMAL_CODE, f"Expected Rung 7, got {r7}"

    print("  ✓ All 7 rungs correctly classified.")


def verify_ast_diff_pruner() -> None:
    print("[2/6] Verifying AST Diff Pruner against over-engineered code...")

    # Over-engineered snippet: Single-method class and trivial builtin wrapper
    bloated_code = """
class FileReaderHelper:
    def __init__(self, filepath):
        self.filepath = filepath
    def read(self):
        return open(self.filepath).read()

def get_length(item):
    return len(item)
"""
    report_bloated = audit_code_simplicity(bloated_code, strict=True)
    assert not report_bloated.passed, "Bloated code should fail strict simplicity check"
    assert len(report_bloated.violations) >= 2, f"Expected >= 2 violations, found {len(report_bloated.violations)}"
    rules = [v.rule for v in report_bloated.violations]
    assert "single_method_class" in rules or "reinventing_pathlib" in rules
    assert "trivial_builtin_wrapper" in rules

    # Lean, idiomatic snippet
    lean_code = """
from pathlib import Path

def read_config(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")
"""
    report_lean = audit_code_simplicity(lean_code, strict=True)
    assert report_lean.passed, f"Lean code should pass simplicity check: {report_lean.remediation_notes}"
    assert report_lean.simplicity_score >= 0.85

    print(f"  ✓ Bloat caught (score: {report_bloated.simplicity_score}); lean code passed (score: {report_lean.simplicity_score}).")


def verify_topological_sort() -> None:
    print("[3/6] Verifying Kahn's topological sort on task DAG...")

    dag = TaskDependencyGraph("TestDAG")
    dag.add_node(TaskNode(task_id="t1", title="Initialize Database", description="Set up SQLite schemas"))
    dag.add_node(TaskNode(task_id="t2", title="Seed Core Rules", description="Write rules to disk", depends_on=["t1"]))
    dag.add_node(TaskNode(task_id="t3", title="Load Models", description="Load local GGUF weights", depends_on=["t1"]))
    dag.add_node(TaskNode(task_id="t4", title="Start Inference Server", description="Bind port 8138", depends_on=["t2", "t3"]))
    dag.add_node(TaskNode(task_id="t5", title="Health Check", description="Verify status endpoint", depends_on=["t4"]))

    sorted_tasks = dag.topological_sort()
    order = [t.task_id for t in sorted_tasks]

    assert order[0] == "t1", f"t1 must be first, got {order}"
    assert order.index("t1") < order.index("t2")
    assert order.index("t1") < order.index("t3")
    assert order.index("t2") < order.index("t4")
    assert order.index("t3") < order.index("t4")
    assert order[-1] == "t5", f"t5 must be last, got {order}"

    print(f"  ✓ Topological order validated: {' -> '.join(order)}")


def verify_cycle_detection() -> None:
    print("[4/6] Verifying circular dependency detection...")

    cyclic_dag = TaskDependencyGraph("CyclicDAG")
    cyclic_dag.add_node(TaskNode(task_id="cA", title="Task A", description="", depends_on=["cC"]))
    cyclic_dag.add_node(TaskNode(task_id="cB", title="Task B", description="", depends_on=["cA"]))
    cyclic_dag.add_node(TaskNode(task_id="cC", title="Task C", description="", depends_on=["cB"]))

    caught = False
    try:
        cyclic_dag.topological_sort()
    except CycleDetectedError as e:
        caught = True
        assert len(e.cycle_nodes) == 3

    assert caught, "Expected CycleDetectedError for circular dependency cA -> cB -> cC -> cA"
    print("  ✓ CycleDetectedError correctly raised on circular graph.")


def verify_parallel_waves() -> None:
    print("[5/6] Verifying parallel execution wave partitioning...")

    dag = TaskDependencyGraph("WaveDAG")
    dag.add_node(TaskNode(task_id="init", title="Setup Environment", description=""))
    dag.add_node(TaskNode(task_id="download_a", title="Download Gemma", description="", depends_on=["init"]))
    dag.add_node(TaskNode(task_id="download_b", title="Download SmolVLM", description="", depends_on=["init"]))
    dag.add_node(TaskNode(task_id="server", title="Launch Daemon", description="", depends_on=["download_a", "download_b"]))

    waves = dag.get_parallel_execution_waves()
    assert len(waves) == 3, f"Expected 3 waves, got {len(waves)}"
    assert [n.task_id for n in waves[0]] == ["init"]
    assert set(n.task_id for n in waves[1]) == {"download_a", "download_b"}
    assert [n.task_id for n in waves[2]] == ["server"]

    print(f"  ✓ Parallel waves verified: {[[n.task_id for n in w] for w in waves]}")


def verify_end_to_end_mrp_planner() -> None:
    print("[6/6] Verifying end-to-end Arkon MRP Planner (Map -> Reduce -> Plan-Review)...")

    tasks = [
        {
            "id": "setup_db",
            "title": "Configure SQLite triples database",
            "description": "Initialize persistent semantic graph schema",
            "depends_on": [],
            "inputs": ["schema.sql"],
            "outputs": ["semantic_triples.db"],
            "verification": "sqlite3 semantic_triples.db '.tables'",
        },
        {
            "id": "build_speculative_cache",
            "title": "Build a speculative cache wrapper just in case",
            "description": "Gold-plated cache layer for future horizons",
            "depends_on": ["setup_db"],
            "inputs": [],
            "outputs": [],
            "verification": "",
        },
        {
            "id": "ingest_sources",
            "title": "Ingest documentation and code symbols",
            "description": "Extract entities and relations",
            "depends_on": ["setup_db"],
            "inputs": ["README.md", "research.md"],
            "outputs": ["knowledge_index.json"],
            "verification": "python3 -c 'import json; json.load(open(\"knowledge_index.json\"))'",
        },
        {
            "id": "verify_graph",
            "title": "Verify knowledge graph queries",
            "description": "Ensure traversal returns valid triples",
            "depends_on": ["ingest_sources"],
            "inputs": ["knowledge_index.json"],
            "outputs": ["verification_report.json"],
            "verification": "python3 -c 'print(\"Graph verified\")'",
        },
    ]

    plan = create_mrp_plan(
        goal="Construct Arkon MRP Knowledge Pipeline",
        tasks=tasks,
        existing_symbols=["sqlite3", "pathlib"],
        context_sources=["Plan.md", "research.md"]
    )

    assert plan.plan_id.startswith("mrp-")
    assert "build_speculative_cache" in plan.pruned_tasks, "Speculative task must be pruned by Rung 1"
    assert len(plan.execution_waves) == 3, f"Expected 3 waves after pruning, got {len(plan.execution_waves)}"

    # Check Mermaid generation
    mermaid_str = plan.graph.to_mermaid()
    assert "flowchart TD" in mermaid_str
    assert "setup_db" in mermaid_str
    assert "ingest_sources" in mermaid_str

    # Save to disk and verify round-trip
    out_path = Path("/tmp/test_mrp_plan.json")
    plan.save_to_file(out_path)
    assert out_path.exists()
    saved_data = json.loads(out_path.read_text())
    assert saved_data["plan_id"] == plan.plan_id
    assert len(saved_data["pruned_tasks"]) == 1
    out_path.unlink()

    print(f"  ✓ MRP Plan synthesized successfully: {plan.plan_id} (1 task pruned by YAGNI ladder).")


def main() -> None:
    print("==================================================================")
    print("  PHASE 1 IN-PROCESS VERIFICATION: MRP PLANNER & PONYTAIL LADDER   ")
    print("==================================================================")
    verify_ponytail_ladder()
    verify_ast_diff_pruner()
    verify_topological_sort()
    verify_cycle_detection()
    verify_parallel_waves()
    verify_end_to_end_mrp_planner()
    print("==================================================================")
    print("  ✅ PHASE 1 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN     ")
    print("==================================================================")


if __name__ == "__main__":
    main()
