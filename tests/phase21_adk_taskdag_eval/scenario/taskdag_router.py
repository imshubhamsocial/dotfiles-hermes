"""Google ADK 2.9+ Multi-Agent TaskDAG & A2A Federation Router (Phase 21).

Grounded in Google ADK 2.9.0 and Agent2Agent (A2A) JSON-RPC 2.0 protocol:
- Topological DAG scheduling with cycle detection in diamond-graph topologies.
- Sandboxed persona privilege enforcement (@architect, @coder, @tester, @critic).
- Zero context pollution across agent transfers via typed structured payload filtering.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PersonaRole(str, Enum):
    ARCHITECT = "@architect"
    CODER = "@coder"
    TESTER = "@tester"
    CRITIC = "@critic"


class CycleDetectedException(Exception):
    """Raised when a circular dependency is detected in TaskDAG."""


class PersonaPrivilegeViolationError(Exception):
    """Raised when a sandboxed persona invokes an unauthorized tool action."""


ALLOWED_PERSONA_PERMISSIONS: dict[str, set[str]] = {
    PersonaRole.ARCHITECT.value: {
        "read_file",
        "ast_grep_outline",
        "inspect_symbols",
        "analyze_spec",
    },
    PersonaRole.CODER.value: {
        "apply_patch",
        "edit_file",
        "surgical_replace",
    },
    PersonaRole.TESTER.value: {
        "run_pytest",
        "run_compiler",
        "run_linter",
    },
    PersonaRole.CRITIC.value: {
        "evaluate_trajectory",
        "compute_reward",
        "verify_receipt",
    },
}


@dataclass
class TaskNode:
    node_id: str
    persona: str
    action: str
    dependencies: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    executed: bool = False
    result: dict[str, Any] | None = None


@dataclass
class A2AEvent:
    jsonrpc: str
    method: str
    params: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
        }


class TaskDAGRouter:
    """Deterministic TaskDAG Scheduler & A2A Event Router."""

    def __init__(self):
        self.nodes: dict[str, TaskNode] = {}
        self.events: list[A2AEvent] = []
        self.metrics: dict[str, Any] = {
            "cuda_vram_delta_mib": 0,
            "context_pollution_tokens": 0,
            "persona_privilege_violations": 0,
            "dag_completion_rate": 0.0,
        }

    def add_node(self, node: TaskNode) -> None:
        """Registers a TaskNode in the graph."""
        self.nodes[node.node_id] = node

    def validate_persona_action(self, persona: str, action: str) -> None:
        """Validates that persona has privilege to invoke action."""
        allowed = ALLOWED_PERSONA_PERMISSIONS.get(persona, set())
        if action not in allowed:
            self.metrics["persona_privilege_violations"] += 1
            raise PersonaPrivilegeViolationError(
                f"Security Sandbox Violation: Persona '{persona}' is forbidden from invoking action '{action}'. "
                f"Allowed actions: {sorted(allowed)}"
            )

    def topological_schedule(self) -> list[str]:
        """Calculates topological ordering with robust diamond-graph cycle detection.
        
        Uses Kahn's algorithm with in-degree tracking:
        Handles arbitrary DAGs including diamonds (A -> B, A -> C, B -> D, C -> D)
        and detects circular dependencies accurately.
        """
        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}
        adj: dict[str, list[str]] = {nid: [] for nid in self.nodes}

        for nid, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    adj[dep].append(nid)
                    in_degree[nid] += 1
                else:
                    raise KeyError(f"Dependency node '{dep}' not registered in TaskDAG")

        # Collect nodes with in-degree 0
        queue: list[str] = [nid for nid, deg in in_degree.items() if deg == 0]
        schedule: list[str] = []

        while queue:
            # Deterministic sorting for tie-breaking
            queue.sort()
            curr = queue.pop(0)
            schedule.append(curr)

            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(schedule) != len(self.nodes):
            cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
            raise CycleDetectedException(
                f"Cycle detected in TaskDAG topology. Nodes in cycle: {cycle_nodes}"
            )

        return schedule

    def transfer_to_agent(
        self,
        sender: str,
        recipient: str,
        task_id: str,
        payload: dict[str, Any],
        sanitize_logs: bool = True,
    ) -> A2AEvent:
        """Emits a typed A2A transfer_to_agent JSON-RPC 2.0 event with zero context pollution."""
        structured_payload: dict[str, Any] = {}
        pollution_detected = 0

        for key, value in payload.items():
            if key in {"raw_terminal_output", "stdout_dump", "stderr_trace", "log_flood"}:
                if not sanitize_logs:
                    pollution_detected += len(str(value).split())
                    structured_payload[key] = value
                else:
                    structured_payload["summary"] = f"Filtered {len(str(value))} bytes of telemetry log"
            else:
                structured_payload[key] = value

        self.metrics["context_pollution_tokens"] += pollution_detected

        event = A2AEvent(
            jsonrpc="2.0",
            method="transfer_to_agent",
            params={
                "sender": sender,
                "recipient": recipient,
                "task_id": task_id,
                "structured_payload": structured_payload,
                "raw_logs_pruned": sanitize_logs,
            },
        )
        self.events.append(event)
        return event

    def execute_dag(self) -> dict[str, Any]:
        """Executes the TaskDAG in topological schedule order."""
        schedule = self.topological_schedule()
        executed_count = 0

        for i, node_id in enumerate(schedule):
            node = self.nodes[node_id]
            self.validate_persona_action(node.persona, node.action)

            # Simulated execution
            node.executed = True
            node.result = {
                "status": "success",
                "node_id": node_id,
                "persona": node.persona,
                "action": node.action,
            }
            executed_count += 1

            # If there's a subsequent dependent node, transfer context
            if i + 1 < len(schedule):
                next_node = self.nodes[schedule[i + 1]]
                self.transfer_to_agent(
                    sender=node.persona,
                    recipient=next_node.persona,
                    task_id=node_id,
                    payload={"result": node.result},
                    sanitize_logs=True,
                )

        completion_rate = executed_count / len(self.nodes) if self.nodes else 0.0
        self.metrics["dag_completion_rate"] = completion_rate

        return {
            "schedule": schedule,
            "executed_count": executed_count,
            "completion_rate": completion_rate,
            "metrics": self.metrics,
        }
