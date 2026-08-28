"""
Milestone U54: Schema.org JSON-LD Semantic Structured Anchors Engine
====================================================================
Implements Schema.org JSON-LD structured data grounding:
  - Deterministic Entity Grounding for SoftwareSourceCode, SoftwareApplication,
    HowTo, TaskSpecification, and CodeRepository
  - Multi-Entity Connected Graph Builder (@graph layout)
  - Plan Injection & Grounding Anchor Generator for .hermes/plan.json
  - Pure CPU RAMDisk execution (0 MB GPU VRAM)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union


@dataclass
class SchemaEntity:
    """Represents a Schema.org typed entity."""
    entity_type: str                  # e.g., 'SoftwareSourceCode', 'TaskSpecification'
    entity_id: str                    # e.g., 'urn:hermes:entity:task_graph'
    name: str                         # Human-readable entity name
    description: str = ""
    programming_language: Optional[str] = None
    target_platform: Optional[str] = None
    code_repository: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    part_of: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_jsonld_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "@type": self.entity_type,
            "@id": self.entity_id,
            "name": self.name,
        }
        if self.description:
            data["description"] = self.description
        if self.programming_language:
            data["programmingLanguage"] = self.programming_language
        if self.target_platform:
            data["targetPlatform"] = self.target_platform
        if self.code_repository:
            data["codeRepository"] = self.code_repository
        if self.dependencies:
            data["dependencies"] = self.dependencies
        if self.part_of:
            data["isPartOf"] = {"@id": self.part_of}

        # Merge custom properties
        for k, v in self.properties.items():
            data[k] = v

        return data


class SchemaJSONLDBuilder:
    """
    Constructs Schema.org JSON-LD compliant entity graphs
    and generates grounding anchors for agent plans and code artifacts.
    """

    SCHEMA_CONTEXT = "https://schema.org"

    def __init__(self, base_uri: str = "urn:hermes:graph"):
        self.base_uri = base_uri
        self.entities: Dict[str, SchemaEntity] = {}

    def add_entity(self, entity: SchemaEntity) -> SchemaEntity:
        self.entities[entity.entity_id] = entity
        return entity

    def create_software_source_code(
        self,
        name: str,
        file_path: str,
        programming_language: str,
        description: str = "",
        dependencies: Optional[List[str]] = None,
        part_of: Optional[str] = None,
    ) -> SchemaEntity:
        entity_id = f"urn:hermes:code:{file_path.lstrip('/')}"
        entity = SchemaEntity(
            entity_type="SoftwareSourceCode",
            entity_id=entity_id,
            name=name,
            description=description,
            programming_language=programming_language,
            dependencies=dependencies or [],
            part_of=part_of,
            properties={"codeSampleType": "full snippet", "runtimePlatform": "Python 3.13 / Fedora Linux"},
        )
        return self.add_entity(entity)

    def create_task_specification(
        self,
        task_id: str,
        title: str,
        description: str,
        target_platform: str = "ws-hermes",
        dependencies: Optional[List[str]] = None,
    ) -> SchemaEntity:
        entity_id = f"urn:hermes:task:{task_id}"
        entity = SchemaEntity(
            entity_type="TaskSpecification",
            entity_id=entity_id,
            name=title,
            description=description,
            target_platform=target_platform,
            dependencies=dependencies or [],
        )
        return self.add_entity(entity)

    def build_jsonld_payload(self) -> Dict[str, Any]:
        """Assembles all registered entities into an interconnected @graph JSON-LD payload."""
        return {
            "@context": self.SCHEMA_CONTEXT,
            "@graph": [entity.to_jsonld_dict() for entity in self.entities.values()],
        }

    def inject_plan_anchors(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Grounds a plan dict with deterministic Schema.org JSON-LD metadata."""
        out = dict(plan_data)
        out["@context"] = self.SCHEMA_CONTEXT
        out["@type"] = "SoftwareApplication"
        out["name"] = plan_data.get("title", plan_data.get("task_id", "HermesTask"))
        out["schema_graph"] = self.build_jsonld_payload()
        return out


def create_schema_builder(base_uri: str = "urn:hermes:graph") -> SchemaJSONLDBuilder:
    return SchemaJSONLDBuilder(base_uri=base_uri)
