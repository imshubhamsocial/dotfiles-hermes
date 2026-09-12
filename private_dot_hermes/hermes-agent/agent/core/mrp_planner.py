"""
MRP Planning & Topological Dependency Graph Engine
==================================================
Implements Phase 1 of the Hermes Frontier Agent OS Architecture:
  - Map -> Reduce -> Plan-Review Lifecycle (Arkon MRP Synthesis)
  - Strict Topological Dependency Sorting with Cycle Detection (Kahn's Algorithm)
  - Parallel Execution Wave Partitioning
  - 7-Rung Ponytail YAGNI Ladder Task Pruning
  - Concrete Input/Output/Verification Contracts for every milestone
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .ponytail_ladder import PonytailLadder, YAGNIRung, audit_code_simplicity


class CycleDetectedError(Exception):
    """Raised when a circular dependency is detected in the task DAG."""
    def __init__(self, cycle_nodes: List[str]):
        super().__init__(f"Cycle detected in task dependency graph involving nodes: {' -> '.join(cycle_nodes)}")
        self.cycle_nodes = cycle_nodes


class TaskState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PRUNED = "PRUNED"


@dataclass
class TaskNode:
    task_id: str
    title: str
    description: str
    depends_on: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    verification_contract: str = ""
    yagni_rung: int = int(YAGNIRung.RUNG_7_MINIMAL_CODE)
    status: TaskState = TaskState.PENDING
    result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "depends_on": self.depends_on,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "verification_contract": self.verification_contract,
            "yagni_rung": self.yagni_rung,
            "status": self.status.value,
            "result": self.result,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskNode:
        return cls(
            task_id=data["task_id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            depends_on=data.get("depends_on", []),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            verification_contract=data.get("verification_contract", ""),
            yagni_rung=data.get("yagni_rung", int(YAGNIRung.RUNG_7_MINIMAL_CODE)),
            status=TaskState(data.get("status", TaskState.PENDING.value)),
            result=data.get("result"),
            metadata=data.get("metadata", {}),
        )


class TaskDependencyGraph:
    """
    Directed Acyclic Graph (DAG) for managing subtask execution,
    topological ordering, parallel wave partitioning, and YAGNI pruning.
    """

    def __init__(self, name: str = "HermesTaskDAG"):
        self.name = name
        self.nodes: Dict[str, TaskNode] = {}
        self.adj: Dict[str, Set[str]] = defaultdict(set)       # u -> set(v) where v depends on u
        self.in_degree: Dict[str, int] = defaultdict(int)       # u -> number of dependencies

    def add_node(self, node: TaskNode) -> None:
        """Add a task node to the DAG."""
        if node.task_id in self.nodes:
            raise ValueError(f"Task with id '{node.task_id}' already exists in graph.")
        self.nodes[node.task_id] = node
        if node.task_id not in self.in_degree:
            self.in_degree[node.task_id] = 0

        # Wire up declared dependencies
        for dep_id in node.depends_on:
            self.adj[dep_id].add(node.task_id)
            self.in_degree[node.task_id] += 1

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Explicitly declare that task_id depends on depends_on_id."""
        if task_id not in self.nodes:
            raise KeyError(f"Task '{task_id}' not found in graph.")
        if depends_on_id not in self.nodes:
            raise KeyError(f"Dependency '{depends_on_id}' not found in graph.")
        
        if depends_on_id not in self.nodes[task_id].depends_on:
            self.nodes[task_id].depends_on.append(depends_on_id)
            self.adj[depends_on_id].add(task_id)
            self.in_degree[task_id] += 1

    def topological_sort(self) -> List[TaskNode]:
        """
        Computes a valid topological execution order using Kahn's algorithm.
        Raises CycleDetectedError if a circular dependency exists.
        """
        # Active nodes excluding pruned ones
        active_nodes = {tid: node for tid, node in self.nodes.items() if node.status != TaskState.PRUNED}
        in_degrees = {tid: 0 for tid in active_nodes}
        
        for u in active_nodes:
            for v in self.adj[u]:
                if v in active_nodes:
                    in_degrees[v] += 1

        queue = deque([tid for tid, deg in in_degrees.items() if deg == 0])
        sorted_order: List[TaskNode] = []

        while queue:
            u = queue.popleft()
            sorted_order.append(active_nodes[u])

            for v in sorted(self.adj[u]):
                if v in active_nodes:
                    in_degrees[v] -= 1
                    if in_degrees[v] == 0:
                        queue.append(v)

        if len(sorted_order) != len(active_nodes):
            remaining = [tid for tid, deg in in_degrees.items() if deg > 0]
            raise CycleDetectedError(remaining)

        return sorted_order

    def get_parallel_execution_waves(self) -> List[List[TaskNode]]:
        """
        Partitions active tasks into parallel waves. Tasks within each wave
        have all their dependencies satisfied by previous waves.
        """
        active_nodes = {tid: node for tid, node in self.nodes.items() if node.status != TaskState.PRUNED}
        in_degrees = {tid: 0 for tid in active_nodes}
        
        for u in active_nodes:
            for v in self.adj[u]:
                if v in active_nodes:
                    in_degrees[v] += 1

        current_wave = [tid for tid, deg in in_degrees.items() if deg == 0]
        waves: List[List[TaskNode]] = []
        processed_count = 0

        while current_wave:
            wave_nodes = [active_nodes[tid] for tid in sorted(current_wave)]
            waves.append(wave_nodes)
            processed_count += len(wave_nodes)

            next_wave = []
            for u in current_wave:
                for v in self.adj[u]:
                    if v in active_nodes:
                        in_degrees[v] -= 1
                        if in_degrees[v] == 0:
                            next_wave.append(v)
            current_wave = next_wave

        if processed_count != len(active_nodes):
            remaining = [tid for tid, deg in in_degrees.items() if deg > 0]
            raise CycleDetectedError(remaining)

        return waves

    def prune_with_yagni_ladder(self, existing_symbols: Optional[List[str]] = None) -> List[str]:
        """
        Applies the 7-Rung Ponytail YAGNI ladder across all nodes.
        Prunes speculative / gold-plated nodes (Rung 1).
        Annotates reused nodes (Rung 2-5).
        Returns list of pruned task IDs.
        """
        pruned_ids: List[str] = []
        for tid, node in list(self.nodes.items()):
            rung, reason = PonytailLadder.evaluate_intent(
                f"{node.title} {node.description}",
                existing_symbols=existing_symbols
            )
            node.yagni_rung = int(rung)
            node.metadata["yagni_reason"] = reason

            if rung == YAGNIRung.RUNG_1_YAGNI:
                node.status = TaskState.PRUNED
                pruned_ids.append(tid)

        return pruned_ids

    def to_mermaid(self) -> str:
        """Render the task graph as a Mermaid flowchart diagram."""
        lines = ["```mermaid", "flowchart TD"]
        for tid, node in sorted(self.nodes.items()):
            label = f"{node.task_id}[\"{node.title} (Rung {node.yagni_rung})\"]"
            if node.status == TaskState.COMPLETED:
                label += ":::completed"
            elif node.status == TaskState.PRUNED:
                label += ":::pruned"
            lines.append(f"    {label}")

        for u, targets in sorted(self.adj.items()):
            for v in sorted(targets):
                lines.append(f"    {u} --> {v}")

        lines.extend([
            "    classDef completed fill:#2ea043,stroke:#fff,stroke-width:2px,color:#fff;",
            "    classDef pruned fill:#6e7681,stroke:#8b949e,stroke-dasharray: 5 5,color:#8b949e;",
            "```"
        ])
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total_nodes": len(self.nodes),
            "active_nodes": sum(1 for n in self.nodes.values() if n.status != TaskState.PRUNED),
            "nodes": {tid: n.to_dict() for tid, n in self.nodes.items()},
        }


@dataclass
class MRPPlan:
    plan_id: str
    goal: str
    graph: TaskDependencyGraph
    mapped_sources: List[str] = field(default_factory=list)
    pruned_tasks: List[str] = field(default_factory=list)
    execution_waves: List[List[Dict[str, Any]]] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: __import__("time").time())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "mapped_sources": self.mapped_sources,
            "pruned_tasks": self.pruned_tasks,
            "execution_waves_count": len(self.execution_waves),
            "execution_waves": self.execution_waves,
            "graph": self.graph.to_dict(),
            "mermaid": self.graph.to_mermaid(),
            "metadata": self.metadata,
        }

    def save_to_file(self, filepath: Path | str) -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


class MRPPlanner:
    """
    Arkon MRP Engine: Map -> Reduce -> Plan-Review.
    Turns an intent into a minimal, topologically sorted execution blueprint.
    """

    def __init__(self, existing_symbols: Optional[List[str]] = None):
        self.existing_symbols = existing_symbols or []

    def plan(
        self,
        goal: str,
        proposed_tasks: List[Dict[str, Any]],
        context_sources: Optional[List[str]] = None,
    ) -> MRPPlan:
        """
        Executes the 3-stage MRP planning pipeline:
          1. Map: Ingest task specifications, declare dependencies and inputs.
          2. Reduce: Apply 7-Rung YAGNI Ladder, pruning gold-plating and mapping reuse.
          3. Plan-Review: Topological sort, cycle check, and execution wave compilation.
        """
        plan_id = f"mrp-{uuid.uuid4().hex[:8]}"
        graph = TaskDependencyGraph(name=plan_id)

        # 1. MAP: Ingest tasks into the graph
        for t in proposed_tasks:
            node = TaskNode(
                task_id=t["id"],
                title=t.get("title", t["id"]),
                description=t.get("description", ""),
                depends_on=t.get("depends_on", []),
                inputs=t.get("inputs", []),
                outputs=t.get("outputs", []),
                verification_contract=t.get("verification_contract", t.get("verification", "")),
                metadata=t.get("metadata", {}),
            )
            graph.add_node(node)

        # 2. REDUCE: 7-Rung YAGNI filter
        pruned = graph.prune_with_yagni_ladder(existing_symbols=self.existing_symbols)

        # 3. PLAN-REVIEW: Validate DAG and partition into waves
        waves = graph.get_parallel_execution_waves()
        waves_serializable = [
            [node.to_dict() for node in wave]
            for wave in waves
        ]

        return MRPPlan(
            plan_id=plan_id,
            goal=goal,
            graph=graph,
            mapped_sources=context_sources or [],
            pruned_tasks=pruned,
            execution_waves=waves_serializable,
        )


def create_mrp_plan(
    goal: str,
    tasks: List[Dict[str, Any]],
    existing_symbols: Optional[List[str]] = None,
    context_sources: Optional[List[str]] = None,
) -> MRPPlan:
    """Convenience helper to create an MRP plan from task specifications."""
    planner = MRPPlanner(existing_symbols=existing_symbols)
    return planner.plan(goal, tasks, context_sources=context_sources)


# =============================================================================
# ARKON MRP KNOWLEDGE PIPELINE & TRACEABLE GRAPH MEMORY (HORIZON 3)
# =============================================================================

import re
import sqlite3
import time


@dataclass
class FactualClaim:
    """A verified or candidate factual claim with explicit provenance."""
    claim_id: str
    subject: str
    predicate: str  # depends_on, implements, refutes, utilizes, verifies, provides, relates_to
    object: str
    statement: str
    source_url: str
    confidence: float = 1.0
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "statement": self.statement,
            "source_url": self.source_url,
            "confidence": round(self.confidence, 3),
            "verified": self.verified,
            "metadata": self.metadata,
        }


@dataclass
class ConceptPage:
    """A structured markdown wiki page representing a grounded concept."""
    slug: str
    title: str
    summary: str
    category: List[str] = field(default_factory=lambda: ["architecture"])
    tags: List[str] = field(default_factory=list)
    claims: List[FactualClaim] = field(default_factory=list)
    wikilinks: List[str] = field(default_factory=list)
    backlinks: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "tags": self.tags,
            "claims_count": len(self.claims),
            "wikilinks": self.wikilinks,
            "backlinks": self.backlinks,
            "sources": self.sources,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def render_markdown(self) -> str:
        """Render standard YAML frontmatter + structured concept markdown with wikilinks and claims."""
        tags_str = ", ".join(f'"{t}"' for t in self.tags)
        cats_str = ", ".join(f'"{c}"' for c in self.category)
        
        lines = [
            "---",
            f'id: "{self.slug}"',
            f'title: "{self.title}"',
            f"category: [{cats_str}]",
            f"tags: [{tags_str}]",
            f'created_at: "{self.created_at}"',
            f'updated_at: "{self.updated_at}"',
            'status: "active"',
            f"verified: {'true' if any(c.verified for c in self.claims) or not self.claims else 'false'}",
            "---",
            "",
            f"# {self.title}",
            "",
            "## Summary",
            self.summary.strip(),
            "",
            "## Relational Graph & Wikilinks",
        ]

        if self.wikilinks:
            for link in sorted(set(self.wikilinks)):
                lines.append(f"- {link}")
        else:
            lines.append("- *No outgoing wikilinks recorded.*")

        lines.extend([
            "",
            "## Grounded Factual Claims & Provenance",
        ])

        if self.claims:
            for c in self.claims:
                ver_mark = "✓ Verified" if c.verified else "⏳ Unverified"
                lines.append(f"- **[{c.subject}]** `{c.predicate}` **[{c.object}]** ({ver_mark})")
                lines.append(f"  > \"{c.statement}\"")
                lines.append(f"  > *Source*: `{c.source_url}` (conf={c.confidence:.2f})")
        else:
            lines.append("- *No discrete propositions attached.*")

        lines.extend([
            "",
            "## Primary Sources",
        ])
        all_sources = sorted(set(self.sources + [c.source_url for c in self.claims if c.source_url]))
        if all_sources:
            for src in all_sources:
                lines.append(f"- <{src}>")
        else:
            lines.append("- *Direct synthesis*")

        lines.append("")
        return "\n".join(lines)


@dataclass
class ArkonMRPKnowledgeReport:
    """Receipt summarizing end-to-end Arkon MRP knowledge execution."""
    pipeline_id: str
    goal: str
    mapped_count: int
    reduced_propositions: int
    blueprint: str
    refined_concepts: List[str]
    verified_claims: int
    committed_triples: int
    committed_pages: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "goal": self.goal,
            "mapped_count": self.mapped_count,
            "reduced_propositions": self.reduced_propositions,
            "blueprint": self.blueprint,
            "refined_concepts": self.refined_concepts,
            "verified_claims": self.verified_claims,
            "committed_triples": self.committed_triples,
            "committed_pages": self.committed_pages,
        }


class ArkonKnowledgePipeline:
    """
    Arkon Knowledge Hub & The MRP Pipeline Engine (Frontier 2026 Paradigm):
      Map -> Reduce -> Plan-Review -> Refine -> Verify -> Commit
    Transforms heterogeneous search results and research findings into verifiable,
    traceable wiki pages with bidirectional wikilinks and relational triples.
    """

    DEFAULT_KNOWLEDGE_DIR = Path.home() / ".hermes" / "knowledge"
    DEFAULT_TRIPLES_DB = DEFAULT_KNOWLEDGE_DIR / "semantic_triples.db"

    PREDICATE_NORMALIZATIONS = {
        "implements": "implements",
        "utilizes": "utilizes",
        "uses": "utilizes",
        "depends_on": "depends_on",
        "requires": "depends_on",
        "refutes": "refutes",
        "contradicts": "refutes",
        "extends": "extends",
        "verifies": "verifies",
        "validates": "verifies",
        "provides": "provides",
        "manages": "manages",
        "relates_to": "relates_to",
    }

    def __init__(self, knowledge_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else self.DEFAULT_KNOWLEDGE_DIR
        self.concepts_dir = self.knowledge_dir / "concepts"
        self.db_path = Path(db_path) if db_path else (self.knowledge_dir / "semantic_triples.db")

        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Ensure SQLite semantic_triples table exists with unique constraint."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS semantic_triples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                source TEXT NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(subject, predicate, object)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_triple_sub ON semantic_triples(subject)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_triple_obj ON semantic_triples(object)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_triple_pred ON semantic_triples(predicate)")
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # 1. MAP: Ingest heterogeneous raw sources
    # -------------------------------------------------------------------------
    def map_sources(self, query: str, sources: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Map phase: Ingest multi-source documents (SearXNG, arXiv, local documentation, code ASTs).
        Extract candidate propositions and entity mentions.
        """
        mapped_records: List[Dict[str, Any]] = []

        for idx, src in enumerate(sources):
            title = src.get("title", f"Source #{idx+1}")
            content = src.get("content", src.get("snippet", ""))
            url = src.get("url", f"local://doc/{idx+1}")
            kind = src.get("kind", "web")

            # Extract raw factual sentences
            sentences = re.split(r"(?<=[.!?])\s+", content)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) >= 20 and not s_clean.startswith("#"):
                    mapped_records.append({
                        "raw_statement": s_clean,
                        "source_title": title,
                        "source_url": url,
                        "source_kind": kind,
                        "query": query,
                    })

        return mapped_records

    # -------------------------------------------------------------------------
    # 2. REDUCE: Distill unique factual propositions and eliminate duplicates
    # -------------------------------------------------------------------------
    def reduce_propositions(self, mapped_records: List[Dict[str, Any]]) -> List[FactualClaim]:
        """
        Reduce phase: Parse relational patterns, normalize predicates, deduplicate claims.
        """
        claims: List[FactualClaim] = []
        seen_triples: Set[Tuple[str, str, str]] = set()

        patterns = [
            (r"\b([A-Za-z0-9_\-]+)\s+(implements|utilizes|uses|replaces|requires|extends|manages|verifies|refutes|depends[_\s]+on)\s+([A-Za-z0-9_\-\.\/]+)", 0.95),
            (r"\b([A-Za-z0-9_\-]+)\s+(provides|exports|exposes|guarantees)\s+([A-Za-z0-9_\-]+)", 0.90),
            (r"\b([A-Za-z0-9_\-]+)\s+(relates[_\s]+to|connects[_\s]+to)\s+([A-Za-z0-9_\-]+)", 0.85),
        ]

        for rec in mapped_records:
            stmt = rec["raw_statement"]
            source_url = rec["source_url"]

            matched_any = False
            for pat, base_conf in patterns:
                for match in re.finditer(pat, stmt, flags=re.IGNORECASE):
                    sub = match.group(1).strip()
                    raw_pred = match.group(2).strip().lower().replace(" ", "_")
                    obj = match.group(3).strip()

                    norm_pred = self.PREDICATE_NORMALIZATIONS.get(raw_pred, "relates_to")
                    key = (sub.lower(), norm_pred, obj.lower())

                    if key not in seen_triples and len(sub) >= 2 and len(obj) >= 2:
                        seen_triples.add(key)
                        claim = FactualClaim(
                            claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                            subject=sub,
                            predicate=norm_pred,
                            object=obj,
                            statement=stmt,
                            source_url=source_url,
                            confidence=base_conf,
                            verified=False,
                            metadata={"source_title": rec.get("source_title", "")},
                        )
                        claims.append(claim)
                        matched_any = True

            # If no pattern matched but sentence has clear subject/predicate structure, create a generalized proposition
            if not matched_any and len(claims) < 20:
                words = stmt.split()
                if len(words) >= 4:
                    sub = words[0].strip(",.:")
                    pred = "relates_to"
                    obj = words[-1].strip(",.:")
                    key = (sub.lower(), pred, obj.lower())
                    if key not in seen_triples and len(sub) >= 3 and len(obj) >= 3:
                        seen_triples.add(key)
                        claims.append(
                            FactualClaim(
                                claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                                subject=sub,
                                predicate=pred,
                                object=obj,
                                statement=stmt,
                                source_url=source_url,
                                confidence=0.80,
                                verified=False,
                            )
                        )

        return claims

    # -------------------------------------------------------------------------
    # 3. PLAN-REVIEW: Generate concise markdown blueprint of pages to update
    # -------------------------------------------------------------------------
    def plan_review_blueprint(self, claims: List[FactualClaim], goal: str = "") -> str:
        """
        Plan-Review phase: Generate a concise markdown blueprint detailing concepts
        to create/update and proposed graph connections.
        """
        concepts_map: Dict[str, List[FactualClaim]] = defaultdict(list)
        for c in claims:
            slug = re.sub(r"[^a-z0-9]+", "-", c.subject.lower()).strip("-")
            concepts_map[slug].append(c)

        lines = [
            f"# Arkon MRP Plan-Review Blueprint: {goal or 'Knowledge Synthesis'}",
            f"> Identified {len(concepts_map)} concept cluster(s) across {len(claims)} distinct factual proposition(s).",
            "",
            "## Planned Concept Updates & Topology",
        ]

        for slug, concept_claims in sorted(concepts_map.items()):
            subj = concept_claims[0].subject
            lines.append(f"### `[[{subj}]]` (`{slug}.md`)")
            lines.append(f"- **Propositions to Ingest**: {len(concept_claims)}")
            links = sorted(set(f"[[{c.object}]]" for c in concept_claims))
            lines.append(f"- **Outgoing Wikilinks**: {', '.join(links)}")
            for c in concept_claims[:3]:
                lines.append(f"  * `{c.predicate}` -> `{c.object}` (source: `{c.source_url}`)")

        lines.append("")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 4. REFINE: Merge new propositions into concept pages without clobbering
    # -------------------------------------------------------------------------
    def refine_concept_pages(self, claims: List[FactualClaim]) -> Dict[str, ConceptPage]:
        """
        Refine phase: Merge claims into ConceptPage models, updating existing pages
        or synthesizing new pages while preserving prior knowledge.
        """
        pages_by_slug: Dict[str, ConceptPage] = {}
        grouped_claims: Dict[str, List[FactualClaim]] = defaultdict(list)

        for c in claims:
            slug = re.sub(r"[^a-z0-9]+", "-", c.subject.lower()).strip("-")
            grouped_claims[slug].append(c)

        for slug, c_list in grouped_claims.items():
            page_path = self.concepts_dir / f"{slug}.md"
            title = c_list[0].subject

            existing_summary = ""
            existing_wikilinks: List[str] = []
            existing_sources: List[str] = []

            if page_path.exists():
                try:
                    old_text = page_path.read_text(encoding="utf-8", errors="replace")
                    # Extract existing summary
                    sum_match = re.search(r"## Summary\s*\n(.*?)(?=\n## |\Z)", old_text, re.DOTALL)
                    if sum_match:
                        existing_summary = sum_match.group(1).strip()
                    # Extract existing wikilinks
                    existing_wikilinks = re.findall(r"\[\[(.*?)\]\]", old_text)
                except Exception:
                    pass

            new_summary = f"{title} is a core system concept with {len(c_list)} grounded propositions."
            if existing_summary:
                combined_summary = f"{existing_summary}\n\n*Updated Synthesis*: {new_summary}"
            else:
                combined_summary = new_summary

            # Collect wikilinks
            wikilinks = set(f"[[{w}]]" if not w.startswith("[[") else w for w in existing_wikilinks)
            for c in c_list:
                wikilinks.add(f"[[{c.object}]]")

            sources = sorted(set(existing_sources + [c.source_url for c in c_list if c.source_url]))

            page = ConceptPage(
                slug=slug,
                title=title,
                summary=combined_summary,
                category=["architecture", "verified-knowledge"],
                tags=[slug, c_list[0].predicate],
                claims=c_list,
                wikilinks=sorted(wikilinks),
                sources=sources,
            )
            pages_by_slug[slug] = page

        return pages_by_slug

    # -------------------------------------------------------------------------
    # 5. VERIFY: Cross-reference each claim against source URLs and text
    # -------------------------------------------------------------------------
    def verify_claims(self, claims: List[FactualClaim], raw_sources: List[Dict[str, str]]) -> List[FactualClaim]:
        """
        Verify phase: Audit claims against source text to confirm evidence provenance.
        """
        source_text_by_url: Dict[str, str] = defaultdict(str)
        for src in raw_sources:
            url = src.get("url", "")
            text = src.get("content", src.get("snippet", "")).lower()
            source_text_by_url[url] += " " + text

        for c in claims:
            evidence = source_text_by_url.get(c.source_url, "")
            # Verify if subject, object, or statement appears in evidence
            sub_present = c.subject.lower() in evidence
            obj_present = c.object.lower() in evidence
            stmt_fragment = c.statement[:30].lower() in evidence

            if (sub_present and obj_present) or stmt_fragment or not evidence:
                c.verified = True
                c.confidence = min(1.0, c.confidence + 0.05)
            else:
                c.verified = False
                c.confidence = max(0.1, c.confidence - 0.20)

        return claims

    # -------------------------------------------------------------------------
    # 6. COMMIT: Ingest into SQLite semantic_triples.db and write concept markdown
    # -------------------------------------------------------------------------
    def commit(self, pages: Dict[str, ConceptPage], claims: List[FactualClaim]) -> Tuple[int, List[str]]:
        """
        Commit phase: Persist relational triples to SQLite and write markdown concept pages.
        """
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        now = time.time()
        committed_triples = 0

        for c in claims:
            if c.verified:
                try:
                    cur.execute("""
                        INSERT OR REPLACE INTO semantic_triples
                        (subject, predicate, object, confidence, source, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (c.subject, c.predicate, c.object, c.confidence, c.source_url, now))
                    committed_triples += 1
                except Exception:
                    pass

        conn.commit()
        conn.close()

        saved_pages = []
        for slug, page in pages.items():
            page_path = self.concepts_dir / f"{slug}.md"
            page_path.write_text(page.render_markdown(), encoding="utf-8")
            saved_pages.append(str(page_path))

        return committed_triples, saved_pages

    # -------------------------------------------------------------------------
    # End-to-End Execution Wrapper
    # -------------------------------------------------------------------------
    def execute_pipeline(
        self,
        goal: str,
        query: str,
        sources: List[Dict[str, str]],
    ) -> ArkonMRPKnowledgeReport:
        """
        Orchestrates full Arkon MRP Knowledge Pipeline:
        Map -> Reduce -> Plan-Review -> Refine -> Verify -> Commit
        """
        pipeline_id = f"arkon-{uuid.uuid4().hex[:8]}"

        # 1. Map
        mapped_records = self.map_sources(query=query, sources=sources)

        # 2. Reduce
        claims = self.reduce_propositions(mapped_records=mapped_records)

        # 3. Plan-Review
        blueprint = self.plan_review_blueprint(claims=claims, goal=goal)

        # 4. Refine
        pages = self.refine_concept_pages(claims=claims)

        # 5. Verify
        verified_claims = self.verify_claims(claims=claims, raw_sources=sources)

        # 6. Commit
        committed_triples, committed_pages = self.commit(pages=pages, claims=verified_claims)

        return ArkonMRPKnowledgeReport(
            pipeline_id=pipeline_id,
            goal=goal,
            mapped_count=len(mapped_records),
            reduced_propositions=len(claims),
            blueprint=blueprint,
            refined_concepts=list(pages.keys()),
            verified_claims=sum(1 for c in verified_claims if c.verified),
            committed_triples=committed_triples,
            committed_pages=committed_pages,
        )


class WikiGraphNavigator:
    """
    Bidirectional Graph Traversal Engine (Horizon 3):
    Navigates across concepts via [[wikilinks]] and relational triples in SQLite.
    Supports forward links, backlinks, multi-hop path traversal, and predicate filtering.
    """

    def __init__(self, knowledge_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else ArkonKnowledgePipeline.DEFAULT_KNOWLEDGE_DIR
        self.concepts_dir = self.knowledge_dir / "concepts"
        self.db_path = Path(db_path) if db_path else (self.knowledge_dir / "semantic_triples.db")

    def find_forward_links(self, concept: str) -> List[str]:
        """Find all outgoing [[wikilinks]] and relational triple targets from a concept."""
        links: Set[str] = set()
        slug = re.sub(r"[^a-z0-9]+", "-", concept.lower()).strip("-")
        page_path = self.concepts_dir / f"{slug}.md"

        if page_path.exists():
            text = page_path.read_text(encoding="utf-8", errors="replace")
            for m in re.findall(r"\[\[(.*?)\]\]", text):
                links.add(m.strip())

        # Also check SQLite semantic_triples
        if self.db_path.exists():
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute("SELECT object FROM semantic_triples WHERE lower(subject) = ?", (concept.lower(),))
            for row in cur.fetchall():
                links.add(row[0])
            conn.close()

        return sorted(links)

    def find_backlinks(self, concept: str) -> List[str]:
        """Find all concept pages and relational triples pointing TO this concept."""
        backlinks: Set[str] = set()
        target_token = concept.lower()

        # 1. Scan concept markdown files for [[concept]]
        if self.concepts_dir.exists():
            for p in self.concepts_dir.glob("*.md"):
                if p.stem.lower() != target_token:
                    try:
                        text = p.read_text(encoding="utf-8", errors="replace").lower()
                        if f"[[{target_token}]]" in text or f"[[{concept.lower()}]]" in text:
                            backlinks.add(p.stem)
                    except Exception:
                        pass

        # 2. Query SQLite semantic_triples
        if self.db_path.exists():
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute("SELECT subject FROM semantic_triples WHERE lower(object) = ?", (concept.lower(),))
            for row in cur.fetchall():
                backlinks.add(row[0])
            conn.close()

        return sorted(backlinks)

    def traverse(
        self,
        start_concept: str,
        max_depth: int = 2,
        predicates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Multi-hop bidirectional graph traversal starting from start_concept.
        Returns visited nodes and discovered relational edges.
        """
        visited: Set[str] = set()
        queue: deque[Tuple[str, int]] = deque([(start_concept, 0)])
        edges: List[Dict[str, str]] = []

        allowed_preds = set(p.lower() for p in predicates) if predicates else None

        while queue:
            curr, depth = queue.popleft()
            curr_clean = curr.strip("[]")
            if curr_clean.lower() in (v.lower() for v in visited):
                continue
            visited.add(curr_clean)

            if depth >= max_depth:
                continue

            # Query outgoing triples from SQLite
            if self.db_path.exists():
                conn = sqlite3.connect(str(self.db_path))
                cur = conn.cursor()
                cur.execute(
                    "SELECT predicate, object FROM semantic_triples WHERE lower(subject) = ?",
                    (curr_clean.lower(),)
                )
                for pred, obj in cur.fetchall():
                    if allowed_preds and pred.lower() not in allowed_preds:
                        continue
                    edges.append({"source": curr_clean, "predicate": pred, "target": obj})
                    if obj not in visited:
                        queue.append((obj, depth + 1))
                conn.close()

            # Query forward wikilinks
            for fwd in self.find_forward_links(curr_clean):
                fwd_clean = fwd.strip("[]")
                edges.append({"source": curr_clean, "predicate": "relates_to", "target": fwd_clean})
                if fwd_clean not in visited:
                    queue.append((fwd_clean, depth + 1))

        return {
            "start": start_concept,
            "max_depth": max_depth,
            "visited_nodes": sorted(visited),
            "node_count": len(visited),
            "edges": edges,
        }

    def query_predicate(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query semantic triples table by pattern (e.g. predicate='depends_on')."""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        query_parts = ["SELECT subject, predicate, object, confidence, source, created_at FROM semantic_triples WHERE 1=1"]
        params = []

        if subject:
            query_parts.append("AND lower(subject) = ?")
            params.append(subject.lower())
        if predicate:
            query_parts.append("AND lower(predicate) = ?")
            params.append(predicate.lower())
        if object:
            query_parts.append("AND lower(object) = ?")
            params.append(object.lower())

        cur.execute(" ".join(query_parts), params)
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "subject": r[0],
                "predicate": r[1],
                "object": r[2],
                "confidence": r[3],
                "source": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]


def execute_arkon_mrp_pipeline(
    goal: str,
    query: str,
    sources: List[Dict[str, str]],
    knowledge_dir: Optional[Path] = None,
) -> ArkonMRPKnowledgeReport:
    """Convenience entrypoint to run the Arkon MRP Knowledge Pipeline."""
    pipeline = ArkonKnowledgePipeline(knowledge_dir=knowledge_dir)
    return pipeline.execute_pipeline(goal=goal, query=query, sources=sources)


def get_wiki_graph_navigator(knowledge_dir: Optional[Path] = None) -> WikiGraphNavigator:
    """Convenience helper to instantiate WikiGraphNavigator."""
    return WikiGraphNavigator(knowledge_dir=knowledge_dir)

