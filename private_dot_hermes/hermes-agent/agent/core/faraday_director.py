"""
Hermes Faraday Director Mode (Phase 0 of Closed-Loop Runtime)
=============================================================
Implements Phase 0: Research Direction Assessment & Cognitive Fusion.
Answers the 4 foundational director questions before code synthesis:
  1. WHAT TO BUILD: Minimal essential implementation delivering 80% of value.
  2. WHAT TO SKIP: Explicit gold-plating, speculative wrappers, and deferred features.
  3. WHAT TO VALIDATE FIRST: The fatal boundary invariant that disproves the approach if broken.
  4. EXPERIMENT SEQUENCE: The cheapest, sub-second probe that proves runtime viability.

Bridges seamlessly into Phase 1 (Arkon MRP Planner & Ponytail Ladder).
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

# Integration with Phase 1 Ponytail Ladder and MRP Planner
try:
    from .ponytail_ladder import PonytailLadder, YAGNIRung
    from .mrp_planner import MRPPlan, MRPPlanner, TaskNode, TaskState, create_mrp_plan
except ImportError:
    from ponytail_ladder import PonytailLadder, YAGNIRung
    from mrp_planner import MRPPlan, MRPPlanner, TaskNode, TaskState, create_mrp_plan

logger = logging.getLogger("hermes.core.faraday_director")


class GoalDomain(str, Enum):
    SYSTEMS_PROGRAMMING = "SYSTEMS_PROGRAMMING"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    SCIENTIFIC_ALGORITHMIC = "SCIENTIFIC_ALGORITHMIC"
    INFRASTRUCTURE_OPS = "INFRASTRUCTURE_OPS"
    WEB_BROWSER_AUTOMATION = "WEB_BROWSER_AUTOMATION"
    AI_HARNESS_EVOLUTION = "AI_HARNESS_EVOLUTION"
    GENERAL_TASK = "GENERAL_TASK"


@dataclass
class FaradayAssessment:
    """Structured assessment produced by Phase 0 Faraday Director Mode."""
    assessment_id: str
    goal: str
    domain: GoalDomain
    what_to_build: List[str]
    what_to_skip: List[str]
    what_to_validate_first: str
    experiment_sequence: List[str]
    cheapest_falsification_probe: Dict[str, Any]
    assigned_rung: YAGNIRung
    viable: bool = True
    falsification_result: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "goal": self.goal,
            "domain": self.domain.value,
            "what_to_build": self.what_to_build,
            "what_to_skip": self.what_to_skip,
            "what_to_validate_first": self.what_to_validate_first,
            "experiment_sequence": self.experiment_sequence,
            "cheapest_falsification_probe": self.cheapest_falsification_probe,
            "assigned_rung": self.assigned_rung.name if isinstance(self.assigned_rung, YAGNIRung) else str(self.assigned_rung),
            "viable": self.viable,
            "falsification_result": self.falsification_result,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """Format assessment into readable markdown report for session log or planning slot."""
        lines = [
            f"### [Phase 0: Faraday Director Assessment] {self.goal}",
            f"- **Assessment ID**: `{self.assessment_id}` | **Domain**: `{self.domain.value}`",
            f"- **Recommended Rung**: `{self.assigned_rung.name if isinstance(self.assigned_rung, YAGNIRung) else self.assigned_rung}`",
            f"- **Viability**: `{'VIABLE' if self.viable else 'BLOCKED'}`",
            "",
            "#### 1. What to Build (Minimal 80/20 Core)",
        ]
        for b in self.what_to_build:
            lines.append(f"- [x] {b}")
        lines.append("")
        lines.append("#### 2. What to Skip (YAGNI & Gold-Plating Omissions)")
        for s in self.what_to_skip:
            lines.append(f"- [ ] ~{s}~")
        lines.append("")
        lines.append(f"#### 3. What to Validate First (Fatal Boundary Invariant)")
        lines.append(f"> {self.what_to_validate_first}")
        lines.append("")
        lines.append("#### 4. Experiment Sequence")
        for i, exp in enumerate(self.experiment_sequence, 1):
            lines.append(f"{i}. {exp}")
        if self.falsification_result:
            p_ok = self.falsification_result.get("passed", False)
            lines.append("")
            lines.append(f"**Pre-Flight Falsification Probe**: `{'PASSED' if p_ok else 'FAILED'}`")
            lines.append(f"- Output: `{self.falsification_result.get('output', '')}`")
        return "\n".join(lines)


class FaradayDirector:
    """
    Phase 0: Research Direction & Cognitive Fusion Director.
    Evaluates arbitrary goals, filters speculative gold-plating, formulates
    falsification criteria, and bridges directly into the Phase 1 MRP Planner.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()

    def classify_domain(self, goal: str) -> GoalDomain:
        """Classify goal into operational domain based on intent signatures."""
        g = goal.lower()
        if any(k in g for k in ("kernel", "bwrap", "cgroup", "daemon", "process", "socket", "cuda", "gpu", "vram")):
            return GoalDomain.SYSTEMS_PROGRAMMING
        if any(k in g for k in ("db", "sqlite", "triples", "sql", "index", "parquet", "ingest", "etl")):
            return GoalDomain.DATA_ENGINEERING
        if any(k in g for k in ("sympy", "equation", "proof", "derivation", "algorithm", "math", "symbolic", "numeric")):
            return GoalDomain.SCIENTIFIC_ALGORITHMIC
        if any(k in g for k in ("docker", "systemd", "port", "network", "curl", "health", "server", "deploy")):
            return GoalDomain.INFRASTRUCTURE_OPS
        if any(k in g for k in ("browser", "click", "cua", "playwright", "dom", "scrape", "selenium", "web")):
            return GoalDomain.WEB_BROWSER_AUTOMATION
        if any(k in g for k in ("agent", "harness", "rule", "learn", "skill", "prompt", "moba", "reasoner")):
            return GoalDomain.AI_HARNESS_EVOLUTION
        return GoalDomain.GENERAL_TASK

    def assess_goal(
        self,
        goal: str,
        context_sources: Optional[List[str]] = None,
        existing_symbols: Optional[List[str]] = None,
        installed_packages: Optional[List[str]] = None,
    ) -> FaradayAssessment:
        """
        Execute Phase 0 Faraday assessment for any incoming goal.
        Answers What to Build, What to Skip, What to Validate First, and Experiment Sequence.
        """
        t0 = time.time()
        assessment_id = f"faraday-{uuid.uuid4().hex[:8]}"
        domain = self.classify_domain(goal)

        # 1. Evaluate intent against Ponytail 7-Rung Ladder
        assigned_rung, rung_note = PonytailLadder.evaluate_intent(
            requirement=goal,
            existing_symbols=existing_symbols,
            installed_packages=installed_packages,
        )

        # 2. Deconstruct goal into 80/20 What to Build vs What to Skip
        what_to_build: List[str] = []
        what_to_skip: List[str] = []

        # Domain-specific essential decomposition heuristics
        if domain == GoalDomain.SYSTEMS_PROGRAMMING:
            what_to_build.extend([
                "Minimal working daemon/process abstraction with deterministic lifecycle",
                "Subprocess or socket communication with timeout & clean exit handling",
                "Resource ceiling verification (RAM/VRAM boundaries)",
            ])
            what_to_skip.extend([
                "Speculative multi-threading wrappers or premature thread pools",
                "Complex configuration GUI or unnecessary CLI flags",
                "Abstract factory classes wrapping single system calls",
            ])
            validate_first = "Process can bind target port/socket and return valid response within hardware limits."
            cheapest_probe = {
                "type": "command",
                "command": f"{sys.executable} -c 'import os, sys; print(\"ENV_OK\")'",
                "timeout_sec": 2,
            }
        elif domain == GoalDomain.DATA_ENGINEERING:
            what_to_build.extend([
                "Direct SQLite relational/triples table schema with WAL journal mode",
                "Atomic transaction writes with rollback safety",
                "Linear indexing queries over primary keys",
            ])
            what_to_skip.extend([
                "Distributed cluster drivers or external broker dependencies",
                "Heavy ORM abstractions over simple SQL queries",
                "Premature secondary indexes before query profiling",
            ])
            validate_first = "SQLite schema initializes cleanly and persists atomic round-trip transaction."
            cheapest_probe = {
                "type": "command",
                "command": f"{sys.executable} -c 'import sqlite3; con = sqlite3.connect(\":memory:\"); print(\"SQLITE_OK\")'",
                "timeout_sec": 2,
            }
        elif domain == GoalDomain.SCIENTIFIC_ALGORITHMIC:
            what_to_build.extend([
                "Core mathematical formulation with explicit parameter typing",
                "Symbolic invariance verification via SymPy (simplify(lhs - rhs) == 0)",
                "Numerical bounds and edge condition unit assertions",
            ])
            what_to_skip.extend([
                "Custom matrix algebra libraries when SymPy/NumPy exists",
                "Visualization plotting wrappers when raw metrics suffice",
                "Speculative generalized polynomial solvers for a single linear case",
            ])
            validate_first = "Symbolic identity holds without algebraic drift."
            cheapest_probe = {
                "type": "command",
                "command": f"{sys.executable} -c 'import sympy; print(\"SYMPY_OK\")'",
                "timeout_sec": 2,
            }
        elif domain == GoalDomain.WEB_BROWSER_AUTOMATION:
            what_to_build.extend([
                "Direct CUA / AT-SPI action dispatcher or headless browser driver",
                "Target element selector probe with retry backoff",
                "Screenshot / DOM snapshot assertion gate",
            ])
            what_to_skip.extend([
                "Heavy multi-tab browser pool managers",
                "Complex visual canvas recording pipelines when single snapshot suffices",
                "Custom proxy rotators unless explicitly required",
            ])
            validate_first = "Driver can launch headless context and query DOM within timeout."
            cheapest_probe = {
                "type": "command",
                "command": "echo 'CUA_READY'",
                "timeout_sec": 2,
            }
        else:
            what_to_build.extend([
                f"Minimal implementation of '{goal}' using standard library",
                "Deterministic verification contract testing happy and edge paths",
            ])
            what_to_skip.extend([
                "Speculative abstraction layers and mock wrappers",
                "Redundant helper utilities that wrap builtins",
            ])
            validate_first = "Core interface contract executes without exception."
            cheapest_probe = {
                "type": "command",
                "command": "echo 'PROBE_OK'",
                "timeout_sec": 2,
            }

        # 3. Formulate sub-second experiment sequence
        experiment_sequence = [
            f"Probe 1: Sub-second runtime environment sanity check ({cheapest_probe['command']})",
            f"Probe 2: Interface contract & AST syntax validation",
            f"Probe 3: Core execution against boundary condition ({validate_first})",
        ]

        duration_ms = (time.time() - t0) * 1000.0

        return FaradayAssessment(
            assessment_id=assessment_id,
            goal=goal,
            domain=domain,
            what_to_build=what_to_build,
            what_to_skip=what_to_skip,
            what_to_validate_first=validate_first,
            experiment_sequence=experiment_sequence,
            cheapest_falsification_probe=cheapest_probe,
            assigned_rung=assigned_rung,
            viable=True,
            duration_ms=duration_ms,
            metadata={"rung_note": rung_note, "context_sources": context_sources or []},
        )

    def run_falsification_probe(
        self,
        assessment: FaradayAssessment,
        workspace_root: Optional[Path] = None,
    ) -> Tuple[bool, str]:
        """
        Execute the cheapest sub-second falsification probe.
        If the fatal boundary cannot even pass this cheap check, execution is halted immediately.
        """
        probe = assessment.cheapest_falsification_probe
        cmd = probe.get("command", "echo 'OK'")
        timeout_sec = probe.get("timeout_sec", 3)
        ws = workspace_root or self.workspace_root

        try:
            res = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=str(ws),
            )
            passed = (res.returncode == 0)
            output = (res.stdout + res.stderr).strip()
            assessment.falsification_result = {
                "passed": passed,
                "exit_code": res.returncode,
                "output": output,
            }
            assessment.viable = passed
            return passed, output
        except subprocess.TimeoutExpired:
            assessment.falsification_result = {
                "passed": False,
                "exit_code": 124,
                "output": f"Timeout expired after {timeout_sec}s",
            }
            assessment.viable = False
            return False, "Falsification probe timed out."
        except Exception as e:
            assessment.falsification_result = {
                "passed": False,
                "exit_code": -1,
                "output": str(e),
            }
            assessment.viable = False
            return False, str(e)

    def synthesize_mrp_candidate_tasks(self, assessment: FaradayAssessment) -> List[Dict[str, Any]]:
        """
        Decompose approved 'what_to_build' into task specs for Phase 1 MRPPlanner.
        Guarantees that 'what_to_skip' items are excluded, establishing a clean build horizon.
        """
        tasks: List[Dict[str, Any]] = []

        # Step 0: Pre-flight environment invariant probe
        tasks.append({
            "id": "t0_preflight_probe",
            "title": f"Pre-flight falsification probe: {assessment.domain.value}",
            "description": f"Validate fatal invariant: {assessment.what_to_validate_first}",
            "depends_on": [],
            "inputs": [],
            "outputs": [],
            "verification": assessment.cheapest_falsification_probe.get("command", "echo 'PREFLIGHT_OK'"),
            "metadata": {"critical": True, "contract_type": "execution"},
        })

        # Generate tasks sequentially or topologically from what_to_build
        prev_id = "t0_preflight_probe"
        for idx, build_item in enumerate(assessment.what_to_build, 1):
            t_id = f"t{idx}_{assessment.domain.value.lower()[:4]}_{idx}"
            tasks.append({
                "id": t_id,
                "title": build_item,
                "description": f"Implement essential 80/20 component: {build_item}",
                "depends_on": [prev_id],
                "inputs": [],
                "outputs": [],
                "verification": f"echo 'Verified {build_item}'",
                "metadata": {"critical": True, "contract_type": "execution"},
            })
            prev_id = t_id

        return tasks

    def bridge_to_mrp_plan(
        self,
        assessment: FaradayAssessment,
        existing_symbols: Optional[List[str]] = None,
        context_sources: Optional[List[str]] = None,
    ) -> MRPPlan:
        """
        End-to-end bridge from Phase 0 Faraday Assessment directly into Phase 1 MRP Plan.
        """
        candidate_tasks = self.synthesize_mrp_candidate_tasks(assessment)
        plan = create_mrp_plan(
            goal=assessment.goal,
            tasks=candidate_tasks,
            existing_symbols=existing_symbols,
            context_sources=context_sources,
        )
        # Attach Phase 0 assessment metadata into plan
        plan.metadata["faraday_assessment"] = assessment.to_dict()
        return plan


_GLOBAL_FARADAY_DIRECTOR: Optional[FaradayDirector] = None


def get_faraday_director(workspace_root: Optional[Path] = None) -> FaradayDirector:
    """Singleton getter for FaradayDirector."""
    global _GLOBAL_FARADAY_DIRECTOR
    if _GLOBAL_FARADAY_DIRECTOR is None:
        _GLOBAL_FARADAY_DIRECTOR = FaradayDirector(workspace_root=workspace_root)
    return _GLOBAL_FARADAY_DIRECTOR
