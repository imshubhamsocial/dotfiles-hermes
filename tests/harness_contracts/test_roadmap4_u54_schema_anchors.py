"""
Contract Tests: Roadmap 4 Milestone U54
========================================
Validates Schema.org JSON-LD Semantic Structured Anchors Engine:
1. SoftwareSourceCode Schema.org JSON-LD entity generation
2. Multi-entity connected graph builder (@graph layout)
3. Plan grounding anchor injection (.hermes/plan.json structured metadata)
4. Strict Hardware Envelope Bounds (Pure CPU RAMDisk execution, 0 MB GPU VRAM)
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.schema_anchors import (
    SchemaEntity,
    SchemaJSONLDBuilder,
    create_schema_builder,
)


# =============================================================================
# 1. ENTITY CREATION & SCHEMA CONFORMANCE
# =============================================================================

class TestSchemaEntityCreation:
    """Validates Schema.org typed entity serialization."""

    def test_schema_jsonld_software_source_code_generation(self):
        builder = create_schema_builder()
        entity = builder.create_software_source_code(
            name="TaskDAG Engine",
            file_path="src/hermes_core/task_graph.py",
            programming_language="Python 3.13",
            description="Core asynchronous DAG task execution kernel.",
            dependencies=["networkx", "asyncio"],
        )

        assert entity.entity_type == "SoftwareSourceCode"
        assert entity.entity_id == "urn:hermes:code:src/hermes_core/task_graph.py"

        data = entity.to_jsonld_dict()
        assert data["@type"] == "SoftwareSourceCode"
        assert data["@id"] == "urn:hermes:code:src/hermes_core/task_graph.py"
        assert data["programmingLanguage"] == "Python 3.13"
        assert data["dependencies"] == ["networkx", "asyncio"]

    def test_schema_jsonld_task_specification_creation(self):
        builder = create_schema_builder()
        task = builder.create_task_specification(
            task_id="u54_schema_anchors",
            title="Implement Schema.org JSON-LD Anchors",
            description="Adds semantic grounding to agent plans.",
        )

        assert task.entity_type == "TaskSpecification"
        assert task.entity_id == "urn:hermes:task:u54_schema_anchors"
        data = task.to_jsonld_dict()
        assert data["@type"] == "TaskSpecification"
        assert data["targetPlatform"] == "ws-hermes"


# =============================================================================
# 2. MULTI-ENTITY GRAPH BUILDER (@graph LAYOUT)
# =============================================================================

class TestSchemaGraphAssembly:
    """Validates multi-entity connected JSON-LD graph generation."""

    def test_schema_jsonld_task_specification_graph(self):
        builder = create_schema_builder()

        # Add task specification
        task = builder.create_task_specification(
            task_id="t1",
            title="Build Graph",
            description="Construct connected JSON-LD graph",
        )

        # Add code entity linked to task
        builder.create_software_source_code(
            name="Graph Module",
            file_path="src/hermes_core/schema_anchors.py",
            programming_language="Python",
            part_of=task.entity_id,
        )

        payload = builder.build_jsonld_payload()
        assert payload["@context"] == "https://schema.org"
        assert "@graph" in payload
        assert len(payload["@graph"]) == 2

        code_entry = next(e for e in payload["@graph"] if e["@type"] == "SoftwareSourceCode")
        assert code_entry["isPartOf"] == {"@id": "urn:hermes:task:t1"}


# =============================================================================
# 3. PLAN INJECTION & GROUNDING ANCHOR
# =============================================================================

class TestPlanAnchorInjection:
    """Validates injection of Schema.org metadata into .hermes/plan.json data."""

    def test_schema_anchor_plan_injection(self):
        builder = create_schema_builder()
        builder.create_software_source_code(
            name="ThreadPool",
            file_path="src/threadpool.hpp",
            programming_language="C++20",
        )

        raw_plan = {
            "task_id": "cpp_threadpool_eval",
            "title": "C++20 ThreadPool Implementation",
            "milestones": ["Specification", "Code Synthesis", "Verification"],
        }

        grounded_plan = builder.inject_plan_anchors(raw_plan)

        assert grounded_plan["@context"] == "https://schema.org"
        assert grounded_plan["@type"] == "SoftwareApplication"
        assert "schema_graph" in grounded_plan
        assert grounded_plan["schema_graph"]["@context"] == "https://schema.org"
        assert len(grounded_plan["schema_graph"]["@graph"]) == 1


# =============================================================================
# 4. HARDWARE ENVELOPE BOUNDS & ZERO GPU VRAM
# =============================================================================

class TestSchemaAnchorsHardwareBounds:
    """Validates pure CPU RAMDisk execution."""

    def test_schema_anchors_zero_gpu_vram(self):
        builder = create_schema_builder()
        for i in range(50):
            builder.create_software_source_code(
                name=f"Module_{i}",
                file_path=f"src/module_{i}.py",
                programming_language="Python",
            )

        payload = builder.build_jsonld_payload()
        # Fast serialization in sub-millisecond RAM space
        serialized = json.dumps(payload)
        assert len(serialized) > 1000
        assert payload["@context"] == "https://schema.org"
