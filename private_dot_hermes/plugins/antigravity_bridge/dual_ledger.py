"""
Microsoft Magentic-One Dual Ledger & Stall Detection Architecture for Hermes.
Maintains two synchronized context states to prevent drift on long-horizon tasks:
1. Task Ledger: High-level strategic roadmap, verified ground truths, milestone checklists.
2. Progress Ledger: Operational step-by-step monitor, sub-agent observations, stall counter.
3. 2-Turn Stall Circuit Breaker: Intercepts repetitive/stalled loops after 2 zero-progress turns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


class TaskMilestone:
    def __init__(self, id: str, description: str, completed: bool = False):
        self.id = id
        self.description = description
        self.completed = completed


class MagenticDualLedger:
    """Manages Task Ledger and Progress Ledger with 2-turn stall circuit breaking."""

    def __init__(self, objective: str):
        self.objective = objective
        self.task_ledger: Dict[str, Any] = {
            "objective": objective,
            "verified_facts": [],
            "working_hypotheses": [],
            "milestones": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self.progress_ledger: List[Dict[str, Any]] = []
        self.stall_counter: int = 0
        self.max_stall_threshold: int = 2

    def add_milestone(self, id: str, description: str):
        self.task_ledger["milestones"].append({"id": id, "description": description, "completed": False})

    def complete_milestone(self, id: str):
        for m in self.task_ledger["milestones"]:
            if m["id"] == id:
                m["completed"] = True
                self.task_ledger["last_updated"] = datetime.now(timezone.utc).isoformat()
                self.stall_counter = 0  # Measurable progress resets stall counter
                break

    def add_fact(self, fact: str):
        if fact not in self.task_ledger["verified_facts"]:
            self.task_ledger["verified_facts"].append(fact)
            self.stall_counter = 0

    def record_step(
        self,
        step_index: int,
        agent_role: str,
        action: str,
        observation: str,
        success: bool,
        measurable_progress: bool = False,
    ) -> Tuple[bool, str]:
        """
        Records an execution step in the Progress Ledger.
        Evaluates stall condition (returns True, warning if stalled).
        """
        step_entry = {
            "step_index": step_index,
            "agent_role": agent_role,
            "action": action,
            "observation": observation[:500],
            "success": success,
            "measurable_progress": measurable_progress,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.progress_ledger.append(step_entry)

        if measurable_progress and success:
            self.stall_counter = 0
            return False, "Progress verified."
        else:
            self.stall_counter += 1

        if self.stall_counter >= self.max_stall_threshold:
            return True, (
                f"STALL CIRCUIT BREAKER: {self.stall_counter} consecutive turns without measurable progress. "
                "Pausing delegation to trigger strategic re-planning."
            )
        return False, "Nominal operational state."

    def render_markdown_ledgers(self) -> str:
        """Renders both ledgers in a clean markdown format for context injection."""
        milestones_md = "\n".join(
            f"- [{'x' if m['completed'] else ' '}] {m['id']}: {m['description']}"
            for m in self.task_ledger["milestones"]
        ) or "None defined."

        facts_md = "\n".join(f"- {fact}" for fact in self.task_ledger["verified_facts"]) or "None established."

        recent_steps = self.progress_ledger[-3:]
        steps_md = "\n".join(
            f"Step {s['step_index']} [{s['agent_role']}]: {'SUCCESS' if s['success'] else 'FAIL'} - {s['action'][:80]}"
            for s in recent_steps
        ) or "No prior steps recorded."

        return f"""### Magentic-One Task Ledger
**Objective:** {self.objective}
**Verified Facts:**
{facts_md}

**Milestones:**
{milestones_md}

### Progress Ledger (Stall Counter: {self.stall_counter}/{self.max_stall_threshold})
{steps_md}"""
