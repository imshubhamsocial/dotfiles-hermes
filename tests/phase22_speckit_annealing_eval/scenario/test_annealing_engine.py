"""Unit tests for Spec-Kit 2.0 Autonomous Failure Cluster Annealer."""

import pytest
from annealing_engine import (
    ASTFailureClusterer,
    FailureTrace,
    SpecKitAnnealer,
    SymPyHardwareVerifier,
)


def test_ast_failure_clustering():
    """Asserts that failure traces are clustered by AST structural similarity."""
    clusterer = ASTFailureClusterer(similarity_threshold=0.75)

    traces = [
        FailureTrace(
            trace_id="t1",
            exception_type="KeyError",
            failing_file="services/parser.py",
            ast_pattern="subscript_expression[base='record'][index='event_id']",
        ),
        FailureTrace(
            trace_id="t2",
            exception_type="KeyError",
            failing_file="services/parser.py",
            ast_pattern="subscript_expression[base='data'][index='event_id']",
        ),
        FailureTrace(
            trace_id="t3",
            exception_type="KeyError",
            failing_file="services/parser.py",
            ast_pattern="subscript_expression[base='payload'][index='event_id']",
        ),
        FailureTrace(
            trace_id="t4",
            exception_type="ZeroDivisionError",
            failing_file="services/aggregator.py",
            ast_pattern="binary_expression[operator='/'][right='count']",
        ),
        FailureTrace(
            trace_id="t5",
            exception_type="ZeroDivisionError",
            failing_file="services/aggregator.py",
            ast_pattern="binary_expression[operator='/'][right='total_samples']",
        ),
    ]

    clusters = clusterer.cluster_traces(traces)
    assert len(clusters) == 2, f"Expected 2 clusters, got {len(clusters)}"

    # Cluster 1: KeyErrors on subscript_expression
    keyerror_cluster = next(c for c in clusters if "keyerror" in c.cluster_id)
    assert len(keyerror_cluster.traces) == 3

    # Cluster 2: ZeroDivisionErrors on binary_expression
    zerodiv_cluster = next(c for c in clusters if "zerodivisionerror" in c.cluster_id)
    assert len(zerodiv_cluster.traces) == 2


def test_sympy_vram_bounds_proof():
    """Asserts CPU SymPy symbolic proof satisfies <= 4,812 MiB VRAM ceiling."""
    verifier = SymPyHardwareVerifier(vram_ceiling_mib=4812.0)
    passed, total_vram, statement = verifier.verify_vram_bounds(
        weights_mib=4000.0,
        kv_cache_mib=280.0,
        module_delta_mib=21.625,
    )
    assert passed is True
    assert total_vram == 4301.625
    assert total_vram <= 4812.0
    assert "Margin: +510.375 MiB" in statement


def test_sympy_vram_exceeded_rejection():
    """Asserts CPU SymPy proof rejects architectures exceeding the 4,812 MiB limit."""
    verifier = SymPyHardwareVerifier(vram_ceiling_mib=4812.0)
    passed, total_vram, _statement = verifier.verify_vram_bounds(
        weights_mib=4500.0,
        kv_cache_mib=500.0,
        module_delta_mib=50.0,
    )
    assert passed is False
    assert total_vram == 5050.0
    assert total_vram > 4812.0


def test_spec_dag_parsing():
    """Asserts parsing of component dependencies from specification markdown."""
    spec_md = """
    # Spec DAG
    - `SchemaValidator`: []
    - `RecordParser`: [`SchemaValidator`]
    - `MetricsAggregator`: [`SchemaValidator`]
    - `PipelineOrchestrator`: [`RecordParser`, `MetricsAggregator`]
    """
    annealer = SpecKitAnnealer()
    dag = annealer.parse_spec_dag(spec_md)

    assert "SchemaValidator" in dag
    assert dag["SchemaValidator"] == []
    assert dag["RecordParser"] == ["SchemaValidator"]
    assert "PipelineOrchestrator" in dag
    assert "RecordParser" in dag["PipelineOrchestrator"]


def test_topological_schedule_kahn():
    """Asserts Kahn's algorithm resolves prerequisites before dependent components."""
    annealer = SpecKitAnnealer()
    graph = {
        "PipelineOrchestrator": ["RecordParser", "MetricsAggregator"],
        "RecordParser": ["SchemaValidator"],
        "MetricsAggregator": ["SchemaValidator"],
        "SchemaValidator": [],
    }

    ordered = annealer.topological_schedule_kahn(graph)
    assert len(ordered) == 4

    # Prerequisite SchemaValidator must appear before consumers
    idx_schema = ordered.index("SchemaValidator")
    idx_parser = ordered.index("RecordParser")
    idx_agg = ordered.index("MetricsAggregator")
    idx_orch = ordered.index("PipelineOrchestrator")

    assert idx_schema < idx_parser
    assert idx_schema < idx_agg
    assert idx_parser < idx_orch
    assert idx_agg < idx_orch


def test_topological_schedule_cycle_detection():
    """Asserts that circular dependencies in the spec DAG raise ValueError."""
    annealer = SpecKitAnnealer()
    cyclic_graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
    }
    with pytest.raises(ValueError, match="Cycle or unresolved dependencies"):
        annealer.topological_schedule_kahn(cyclic_graph)


def test_clean_slate_synthesis_and_debt_reduction():
    """Asserts clean-slate code generation and >= 60.0% patch debt reduction."""
    annealer = SpecKitAnnealer()
    dag = {
        "SchemaValidator": [],
        "RecordParser": ["SchemaValidator"],
        "MetricsAggregator": ["SchemaValidator"],
        "PipelineOrchestrator": ["RecordParser", "MetricsAggregator"],
    }
    ordered = annealer.topological_schedule_kahn(dag)
    code = annealer.synthesize_clean_module(ordered)

    assert "class SchemaValidator" in code
    assert "class RecordParser" in code
    assert "class MetricsAggregator" in code
    assert "class PipelineOrchestrator" in code

    # Test patch debt reduction calculation: 180 lines of messy churn vs 45 clean lines
    clean_lines = len(code.splitlines())
    churn_lines = 185
    reduction = annealer.calculate_patch_debt_reduction(churn_lines=churn_lines, clean_lines=clean_lines)

    assert reduction >= 60.0
    assert reduction > 0.0
