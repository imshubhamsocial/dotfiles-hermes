"""
Hermes Autonomous In-The-Loop Learner (Phase 4 of Closed-Loop Runtime)
======================================================================
Implements Phase 4: Autonomous Learning (/learn) & Closed-Loop Rule Extraction.
When an execution fails, low-reward signal occurs, or Phase 3 Contract Gate rejects:
  1. Triggers autonomous self-reflection turn (diagnosing conceptual divergence).
  2. Formulates generalized behavioral invariants (Rule 0 / Mandate).
  3. Persists new rules into ~/.hermes/rules/ via ReflectiveLearner.
  4. Automatically synchronizes newly synthesized rules to Chezmoi.
  5. Executes blind transfer verification after simulated /clear context reset.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

# Core module imports
try:
    from .reflective_learner import CorrectionEvent, ReflectiveLearner, create_reflective_learner
    from .contract_gate import ContractCategory, ContractGateVerdict, ContractViolation
except ImportError:
    from reflective_learner import CorrectionEvent, ReflectiveLearner, create_reflective_learner
    from contract_gate import ContractCategory, ContractGateVerdict, ContractViolation

logger = logging.getLogger("hermes.core.autonomous_learner")

DEFAULT_RULES_DIR = Path.home() / ".hermes" / "rules"
DEFAULT_RL_BUFFER = Path.home() / ".hermes" / "evolution" / "rl_buffer.jsonl"
DEFAULT_CHEZMOI_DIR = Path.home() / ".local" / "share" / "chezmoi"


@dataclass
class FailureDiagnosis:
    """Diagnostic breakdown of an execution failure or low-reward step."""
    failure_id: str
    task_id: str
    failure_mode: str
    root_cause: str
    proposed_invariant: str
    category: str
    suggested_filename: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutonomousLearner:
    """
    Phase 4: Autonomous In-The-Loop Learning Engine (/learn).
    Extracts durable behavioral invariants from failure traces and verifies
    transfer onto novel problems.
    """

    def __init__(
        self,
        rules_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
        chezmoi_dir: Optional[Path] = None,
    ):
        self.rules_dir = Path(rules_dir) if rules_dir else DEFAULT_RULES_DIR
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.learner = create_reflective_learner(db_path=db_path, rules_dir=self.rules_dir)
        self.chezmoi_dir = Path(chezmoi_dir) if chezmoi_dir else DEFAULT_CHEZMOI_DIR

    def diagnose_from_trace(
        self,
        task_id: str,
        prompt: str,
        solution: str,
        error_trace: str = "",
        reward: float = 0.0,
    ) -> FailureDiagnosis:
        """
        Diagnose the conceptual breakdown from failure trace, solution, or prompt.
        Isolates root causes: Premise Invalidation, Algebraic Drift, AST Over-engineering, or Refusal.
        """
        fid = f"diag-{uuid.uuid4().hex[:8]}"
        combined = (prompt + " " + solution + " " + error_trace).lower()

        # 1. Adversarial Premise Invalidation Trap
        if any(k in combined for k in ("survivor", "plane crash", "bury", "border", "false premise", "unexamined")):
            return FailureDiagnosis(
                failure_id=fid,
                task_id=task_id,
                failure_mode="PREMISE_INVALIDATION_TRAP",
                root_cause="Uncritically accepted an invalid or paradoxical question premise without asserting factual ground truth.",
                proposed_invariant=(
                    "Always audit and explicitly validate the existential and logical premises of a query before "
                    "computing, deriving, or generating a solution. If a premise is physically, legally, or logically "
                    "invalid (e.g. burying survivors), immediately falsify the premise rather than hallucinating jurisdiction or rules."
                ),
                category="premise_invalidation",
                suggested_filename="rule_premise_invalidation_guard.md",
            )

        # 2. Algebraic & Symbolic Calculation Drift
        if any(k in combined for k in ("algebraic", "sympy", "drift", "simplify", "derivation", "identity", "equation")):
            return FailureDiagnosis(
                failure_id=fid,
                task_id=task_id,
                failure_mode="ALGEBRAIC_DERIVATION_DRIFT",
                root_cause="Step-by-step mathematical derivation exhibited non-conservative algebraic transformation.",
                proposed_invariant=(
                    "Maintain strict, explicit symbolic cancellation and differential reduction: whenever a variable "
                    "or expression is algebraically canceled or transformed, verify equivalence at every intermediate step. "
                    "Never drop terms whose coefficient is non-zero without explicit derivation."
                ),
                category="algebraic_reasoning",
                suggested_filename="rule_algebraic_symbolic_cancellation.md",
            )

        # 3. YAGNI Over-Engineering / AST Bloat
        if any(k in combined for k in ("bloat", "overengineering", "single_method_class", "reinventing_pathlib", "yagni")):
            return FailureDiagnosis(
                failure_id=fid,
                task_id=task_id,
                failure_mode="AST_OVERENGINEERING_BLOAT",
                root_cause="Synthesized redundant helper wrapper class when native standard library or single line was sufficient.",
                proposed_invariant=(
                    "Adhere strictly to the Ponytail 7-Rung YAGNI Ladder: never construct custom wrapper classes or "
                    "helper abstractions when standard library functions (e.g. pathlib.Path) or single expressions solve the requirement."
                ),
                category="simplicity_yagni",
                suggested_filename="rule_ponytail_yagni_simplicity.md",
            )

        # 4. API Contract & Schema Mismatch
        if any(k in combined for k in ("schema", "unexpected argument", "missing argument", "validation error", "unrecognized parameter", "typeerror")):
            return FailureDiagnosis(
                failure_id=fid,
                task_id=task_id,
                failure_mode="API_CONTRACT_MISMATCH",
                root_cause="Invoked tool or subsystem with invalid arguments or schema mismatch.",
                proposed_invariant=(
                    "Adhere strictly to external and tool API contracts: never supply hallucinated keyword arguments "
                    "or pass unvalidated parameter schemas. Validate request payloads against declared type definitions."
                ),
                category="api_contracts",
                suggested_filename="rule_api_contract_guard.md",
            )

        # 5. Sandbox & Permission Boundaries
        if any(k in combined for k in ("permission denied", "read-only", "operation not permitted", "access denied")):
            return FailureDiagnosis(
                failure_id=fid,
                task_id=task_id,
                failure_mode="SANDBOX_PERMISSION_DRIFT",
                root_cause="Attempted mutation or execution outside authorized operational boundaries.",
                proposed_invariant=(
                    "Respect sandbox execution boundaries: write state and temporary artifacts only into authorized "
                    "workspace or user data directories, avoiding unauthorized root mutations."
                ),
                category="sandbox_security",
                suggested_filename="rule_sandbox_boundary_guard.md",
            )

        # 6. General Contract / Runtime Failure
        return FailureDiagnosis(
            failure_id=fid,
            task_id=task_id,
            failure_mode="RUNTIME_CONTRACT_VIOLATION",
            root_cause=error_trace[:200] if error_trace else "Execution failed to satisfy acceptance criteria.",
            proposed_invariant=(
                f"Ensure strict compliance with execution verification contract for task '{task_id}'. "
                "Eliminate boilerplate refusal patterns and verify non-zero outputs."
            ),
            category="runtime_behavior",
            suggested_filename=f"rule_runtime_{task_id.lower()[:8]}.md",
        )

    def learn_from_failure(
        self,
        task_id: str,
        prompt: str,
        solution: str,
        error_trace: str = "",
        reward: float = 0.0,
        rule_filename: Optional[str] = None,
    ) -> Tuple[CorrectionEvent, Path]:
        """
        Closed-loop /learn turn:
        Diagnoses failure, captures correction, writes permanent rule, and commits to Chezmoi.
        """
        diagnosis = self.diagnose_from_trace(
            task_id=task_id,
            prompt=prompt,
            solution=solution,
            error_trace=error_trace,
            reward=reward,
        )

        fname = rule_filename or diagnosis.suggested_filename
        event = self.learner.capture_correction(
            user_feedback=diagnosis.proposed_invariant,
            category=diagnosis.category,
        )

        rule_path = self.learner.synthesize_and_persist_rule(event, rule_filename=fname)
        logger.info(f"[/learn Generated Rule] Persisted new rule to {rule_path}")

        # Mirror to local workspace .hermes/rules/ if it exists and differs from rules_dir
        workspace_rules_dir = Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/rules")
        if workspace_rules_dir.is_dir() and workspace_rules_dir.resolve() != self.rules_dir.resolve():
            try:
                shutil.copy2(rule_path, workspace_rules_dir / rule_path.name)
            except Exception:
                pass

        # Commit to Chezmoi
        self.commit_rule_to_chezmoi(rule_path)

        return event, rule_path

    def learn_from_contract_verdict(
        self,
        verdict: ContractGateVerdict,
        task_id: str,
        task_context: str,
    ) -> Tuple[CorrectionEvent, Path]:
        """
        Closed-loop bridge from Phase 3:
        When a task fails NativeContractGate, automatically distill the violations into a new rule.
        """
        rule_snippets = [v.remediation_hint or v.message for v in verdict.violations]
        invariant_text = (
            f"When executing tasks in context '{task_context}', satisfy contract: "
            + "; ".join(rule_snippets)
        )
        category = "contract_gate"
        fname = f"rule_contract_{task_id.lower()[:8]}.md"

        event = self.learner.capture_correction(
            user_feedback=invariant_text,
            category=category,
        )
        rule_path = self.learner.synthesize_and_persist_rule(event, rule_filename=fname)

        workspace_rules_dir = Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/rules")
        if workspace_rules_dir.is_dir() and workspace_rules_dir.resolve() != self.rules_dir.resolve():
            try:
                shutil.copy2(rule_path, workspace_rules_dir / rule_path.name)
            except Exception:
                pass

        self.commit_rule_to_chezmoi(rule_path)
        return event, rule_path

    def learn_from_rl_buffer(
        self,
        buffer_path: Optional[Path] = None,
        min_reward_threshold: float = 0.8,
    ) -> List[Path]:
        """
        Scan rl_buffer.jsonl for low-reward or failed tasks and autonomously extract rules.
        """
        path = buffer_path or DEFAULT_RL_BUFFER
        if not path.exists():
            return []

        generated_rules: List[Path] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    reward = entry.get("reward", 1.0)
                    verified = entry.get("verified_passed", True)
                    if reward < min_reward_threshold or not verified:
                        task_id = entry.get("task_id", "task_unknown")
                        prompt = entry.get("prompt", "")
                        solution = entry.get("solution", "")
                        _, rpath = self.learn_from_failure(
                            task_id=task_id,
                            prompt=prompt,
                            solution=solution,
                            reward=reward,
                        )
                        generated_rules.append(rpath)
                except Exception as e:
                    logger.warning(f"Failed to process RL buffer entry: {e}")

        return generated_rules

    def execute_blind_transfer_test(
        self,
        rule_path: Path,
        transfer_prompt: str,
        solver_fn: Callable[[str, str], str],
        validator_fn: Callable[[str], bool],
    ) -> Tuple[bool, str]:
        """
        Executes a blind transfer test:
        1. Reads newly synthesized rule from disk.
        2. Simulates /clear context reset (fresh empty context + rule injection).
        3. Runs solver_fn with injected rule.
        4. Validates outcome with validator_fn.
        """
        if not rule_path.exists():
            return False, f"Rule path {rule_path} does not exist."

        rule_content = rule_path.read_text(encoding="utf-8")

        # Execute solver under injected rule
        solution = solver_fn(transfer_prompt, rule_content)

        # Validate
        passed = validator_fn(solution)
        return passed, solution

    def learn_and_verify_transfer(
        self,
        task_id: str,
        prompt: str,
        solution: str,
        error_trace: str,
        transfer_prompt: str,
        solver_fn: Callable[[str, str], str],
        validator_fn: Callable[[str], bool],
        reward: float = 0.0,
    ) -> Tuple[bool, Path, str]:
        """
        Turnkey Horizon 5 in-the-loop learning cycle:
        1. Diagnoses failure and synthesizes invariant rule.
        2. Persists rule, mirrors to workspace, and syncs to Chezmoi.
        3. Executes blind transfer test on novel problem after /clear reset.
        Returns (passed, rule_path, transfer_solution).
        """
        event, rule_path = self.learn_from_failure(
            task_id=task_id,
            prompt=prompt,
            solution=solution,
            error_trace=error_trace,
            reward=reward,
        )
        passed, trans_sol = self.execute_blind_transfer_test(
            rule_path=rule_path,
            transfer_prompt=transfer_prompt,
            solver_fn=solver_fn,
            validator_fn=validator_fn,
        )
        return passed, rule_path, trans_sol

    def commit_rule_to_chezmoi(self, rule_path: Path) -> bool:
        """
        Mirror newly synthesized rule to Chezmoi and commit.
        """
        try:
            # Locate target chezmoi path
            chezmoi_rules_dir = self.chezmoi_dir / "private_dot_hermes" / "rules"
            if not chezmoi_rules_dir.is_dir():
                return False

            target = chezmoi_rules_dir / rule_path.name
            shutil.copy2(rule_path, target)

            # Git commit in chezmoi
            res = subprocess.run(
                ["git", "add", str(target)],
                cwd=str(self.chezmoi_dir),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                subprocess.run(
                    ["git", "commit", "-m", f"feat(rules): autonomously synthesize {rule_path.name} via ReflectiveLearner"],
                    cwd=str(self.chezmoi_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            return True
        except Exception as e:
            logger.warning(f"Chezmoi rule commit failed (non-fatal): {e}")
            return False


_GLOBAL_AUTONOMOUS_LEARNER: Optional[AutonomousLearner] = None


def get_autonomous_learner() -> AutonomousLearner:
    """Singleton getter for AutonomousLearner."""
    global _GLOBAL_AUTONOMOUS_LEARNER
    if _GLOBAL_AUTONOMOUS_LEARNER is None:
        _GLOBAL_AUTONOMOUS_LEARNER = AutonomousLearner()
    return _GLOBAL_AUTONOMOUS_LEARNER
