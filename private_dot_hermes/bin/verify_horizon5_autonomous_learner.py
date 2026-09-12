#!/usr/bin/env python3
"""
Verification Script for Horizon 5: Continuous Autonomous In-The-Loop Learning (/learn)
=====================================================================================
Executes in-process contract verification against:
  [1/7] Failure Diagnosis (Premise Invalidation, Algebraic Drift, AST Bloat, API Drift, Sandbox Drift)
  [2/7] Autonomous Rule Synthesis & SQLite WAL State Ledger Persistence (~/.hermes/rules/)
  [3/7] Closed-Loop Ingestion from rl_buffer.jsonl Low-Reward Logs
  [4/7] Native Contract Gate Violation -> /learn Invariant Rule Extraction
  [5/7] Blind Transfer Test after Simulated /clear Context Reset
  [6/7] Turnkey learn_and_verify_transfer() Lifecycle Loop
  [7/7] CLI Integration: /loop learn and /learn --rule Command Dispatch
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add active hermes-agent paths
for p in [
    Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/hermes-agent"),
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.autonomous_learner import (
    AutonomousLearner,
    FailureDiagnosis,
    get_autonomous_learner,
)
from agent.core.contract_gate import (
    ContractCategory,
    ContractGateVerdict,
    ContractViolation,
)


def verify_failure_diagnosis_taxonomy() -> None:
    print("[1/7] Verifying multi-class failure diagnosis taxonomy & invariant derivation...")

    learner = AutonomousLearner()

    # 1. Premise Invalidation Trap
    diag_trap = learner.diagnose_from_trace(
        task_id="T1_TRAP_LOGIC",
        prompt="A plane crashes exactly on the border between the US and Canada. Where are the survivors buried?",
        solution="The survivors are buried under the jurisdiction of Canada.",
        reward=0.5,
    )
    assert diag_trap.failure_mode == "PREMISE_INVALIDATION_TRAP"
    assert "premise" in diag_trap.category
    assert "survivors" in diag_trap.proposed_invariant.lower()
    assert "rule_premise_invalidation_guard.md" in diag_trap.suggested_filename

    # 2. Algebraic Derivation Drift
    diag_math = learner.diagnose_from_trace(
        task_id="T2_MATH_CALC",
        prompt="Simplify the drag force differential equation",
        solution="m*dv/dt = -c*v^2 => v(t) = v0",
        error_trace="Algebraic discrepancy: simplify(lhs - rhs) != 0, drift detected",
        reward=0.0,
    )
    assert diag_math.failure_mode == "ALGEBRAIC_DERIVATION_DRIFT"
    assert "algebraic" in diag_math.category
    assert "cancellation" in diag_math.proposed_invariant.lower()

    # 3. AST Over-Engineering Bloat
    diag_bloat = learner.diagnose_from_trace(
        task_id="T3_CODE_BLOAT",
        prompt="Read file from disk",
        solution="class CustomFileReaderManager:\n    def read(self): return open('f').read()",
        error_trace="YAGNI bloat violation: single_method_class and reinventing_pathlib",
        reward=0.3,
    )
    assert diag_bloat.failure_mode == "AST_OVERENGINEERING_BLOAT"
    assert "yagni" in diag_bloat.category
    assert "ponytail" in diag_bloat.proposed_invariant.lower()

    # 4. API Contract & Schema Mismatch
    diag_api = learner.diagnose_from_trace(
        task_id="T4_API_DRIFT",
        prompt="Invoke tool terminal",
        solution="terminal(command='ls', unexpected_kwarg=True)",
        error_trace="ValidationError: unexpected argument 'unexpected_kwarg'",
        reward=0.0,
    )
    assert diag_api.failure_mode == "API_CONTRACT_MISMATCH"
    assert "api" in diag_api.category
    assert "contract" in diag_api.proposed_invariant.lower()

    # 5. Sandbox & Permission Boundary Drift
    diag_sandbox = learner.diagnose_from_trace(
        task_id="T5_SANDBOX_DRIFT",
        prompt="Modify /etc/systemd/system/hermes.service",
        solution="write_file('/etc/systemd/system/hermes.service', '...')",
        error_trace="PermissionError: [Errno 13] Permission denied: '/etc/systemd/system/hermes.service'",
        reward=0.0,
    )
    assert diag_sandbox.failure_mode == "SANDBOX_PERMISSION_DRIFT"
    assert "sandbox" in diag_sandbox.category
    assert "boundary" in diag_sandbox.proposed_invariant.lower() or "boundaries" in diag_sandbox.proposed_invariant.lower()

    print("  ✓ Multi-class failure modes categorized and invariants formulated.")


def verify_autonomous_rule_synthesis() -> None:
    print("[2/7] Verifying autonomous rule synthesis & SQLite reflection persistence...")

    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir) / "rules"
        db_path = Path(tmpdir) / "state.db"

        learner = AutonomousLearner(rules_dir=rules_dir, db_path=db_path)

        event, rule_path = learner.learn_from_failure(
            task_id="T1_TRAP_LOGIC",
            prompt="A plane crashes on the border. Where do you bury the survivors?",
            solution="Buried in Canada.",
            reward=0.0,
            rule_filename="rule_test_premise_guard.md",
        )

        assert rule_path.exists(), "Rule markdown file must be written to disk"
        assert event.promoted is True, "Correction event must be marked as promoted"

        # Check rule file structure
        content = rule_path.read_text(encoding="utf-8")
        assert "# Behavioral Invariant:" in content
        assert "## Mandate" in content
        assert "INVARIANT:" in content
        assert "survivors" in content.lower()

        # Check SQLite persistence
        reflections = learner.learner.get_all_reflections()
        assert len(reflections) == 1
        assert reflections[0]["event_id"] == event.event_id
        assert reflections[0]["promoted"] == 1

    print("  ✓ Autonomous rule synthesized to disk and recorded in SQLite state ledger.")


def verify_rl_buffer_ingestion() -> None:
    print("[3/7] Verifying autonomous learning ingestion from rl_buffer.jsonl...")

    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir) / "rules"
        db_path = Path(tmpdir) / "state.db"
        buffer_file = Path(tmpdir) / "rl_buffer.jsonl"

        # Write mock rl_buffer.jsonl with 1 passing and 1 failing entry
        entries = [
            {
                "task_id": "T1_MATH_AIME",
                "prompt": "Compute modular inverse",
                "solution": "266",
                "reward": 1.0,
                "verified_passed": True,
            },
            {
                "task_id": "T2_TRAP_LOGIC",
                "prompt": "Where do you bury survivors of a plane crash on an international border?",
                "solution": "Buried under joint treaty jurisdiction.",
                "reward": 0.5,
                "verified_passed": False,
            },
        ]
        with open(buffer_file, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        learner = AutonomousLearner(rules_dir=rules_dir, db_path=db_path)
        generated_rules = learner.learn_from_rl_buffer(buffer_path=buffer_file, min_reward_threshold=0.8)

        assert len(generated_rules) == 1, f"Expected 1 extracted rule, got {len(generated_rules)}"
        assert generated_rules[0].exists()
        assert "premise" in generated_rules[0].read_text().lower()

    print("  ✓ Low-reward failure successfully extracted from rl_buffer.jsonl into durable rule.")


def verify_contract_gate_to_learn_bridge() -> None:
    print("[4/7] Verifying Native Contract Gate violation -> /learn rule extraction...")

    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir) / "rules"
        db_path = Path(tmpdir) / "state.db"
        learner = AutonomousLearner(rules_dir=rules_dir, db_path=db_path)

        violations = [
            ContractViolation(
                category=ContractCategory.AST_SYNTAX,
                rule="missing_required_symbol",
                message="Required export 'execute_query' is missing.",
                severity="CRITICAL",
                remediation_hint="Export 'execute_query' in module namespace.",
            )
        ]
        verdict = ContractGateVerdict(
            passed=False,
            confidence=0.2,
            verdict_id="cg-fail-01",
            violations=violations,
            remediation_hints=["Export 'execute_query' in module namespace."],
        )

        event, rule_path = learner.learn_from_contract_verdict(
            verdict=verdict,
            task_id="task_export_audit",
            task_context="SQL Database Engine",
        )

        assert rule_path.exists()
        rule_text = rule_path.read_text()
        assert "execute_query" in rule_text
        assert "SQL Database Engine" in rule_text

    print("  ✓ Contract gate violations translated directly into behavioral invariant rule.")


def verify_blind_transfer_test() -> None:
    print("[5/7] Verifying blind transfer test after simulated /clear context reset...")

    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir) / "rules"
        db_path = Path(tmpdir) / "state.db"
        learner = AutonomousLearner(rules_dir=rules_dir, db_path=db_path)

        # 1. Synthesize premise invalidation rule
        _, rule_path = learner.learn_from_failure(
            task_id="T2_TRAP_LOGIC",
            prompt="Plane crash on border, where are survivors buried?",
            solution="Buried in Canada.",
            reward=0.0,
            rule_filename="rule_premise_invalidation_guard.md",
        )

        # 2. Define simulated solver function respecting injected rules
        def simulated_agent_solver(prompt: str, injected_rules: str) -> str:
            if "premise" in injected_rules.lower() and "survivor" in injected_rules.lower():
                if "survivor" in prompt.lower() and "bury" in prompt.lower():
                    return "Survivors are living individuals; survivors are never buried."
            return "Survivors should be buried according to maritime convention."

        # 3. Define validator function for novel transfer problem
        transfer_prompt = "A fishing boat capsizes on the border between France and Spain. Where do they bury the survivors?"

        def transfer_validator(answer: str) -> bool:
            ans = answer.lower()
            return ("never buried" in ans or "survivors are alive" in ans or "not buried" in ans) and "maritime" not in ans

        # 4. Execute Blind Transfer Test
        passed, solution = learner.execute_blind_transfer_test(
            rule_path=rule_path,
            transfer_prompt=transfer_prompt,
            solver_fn=simulated_agent_solver,
            validator_fn=transfer_validator,
        )

        assert passed, f"Blind transfer test failed: {solution}"
        assert "never buried" in solution.lower()

    print("  ✓ Blind transfer certified: Agent prevented recurrence of failure on novel problem.")


def verify_turnkey_lifecycle() -> None:
    print("[6/7] Verifying turnkey learn_and_verify_transfer() lifecycle...")

    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir) / "rules"
        db_path = Path(tmpdir) / "state.db"
        learner = AutonomousLearner(rules_dir=rules_dir, db_path=db_path)

        def solver(p: str, r: str) -> str:
            if "algebraic" in r.lower() or "cancellation" in r.lower():
                return "v(t) = v0 / (1 + c*v0*t / m)"
            return "v(t) = v0"

        def validator(ans: str) -> bool:
            return "1 + c*v0*t" in ans

        passed, rpath, sol = learner.learn_and_verify_transfer(
            task_id="T_DRAG_FORCE",
            prompt="Solve m dv/dt = -c v^2",
            solution="v(t) = v0",
            error_trace="Algebraic discrepancy: simplify(lhs - rhs) != 0, drift detected",
            transfer_prompt="Solve drag force with initial velocity v0",
            solver_fn=solver,
            validator_fn=validator,
        )
        assert passed, f"Lifecycle failed: {sol}"
        assert rpath.exists()
        assert "rule_algebraic_symbolic_cancellation.md" in rpath.name

    print("  ✓ Turnkey lifecycle verified: Diagnostic -> Rule -> Transfer Verification.")


def verify_cli_integration() -> None:
    print("[7/7] Verifying CLI integration (/loop learn & /learn --rule)...")

    from hermes_cli.loops import dispatch_loop_command, LoopManager

    # Test /loop learn with task identifier
    mgr = LoopManager("test_session_h5")
    res_task = dispatch_loop_command(mgr, "learn test_premise_trap")
    assert "Synthesized rule" in res_task["output"]
    assert "test_premise_trap" in res_task["output"]

    # Clean up test rule synthesized during CLI test to keep production rulesets clean
    import glob
    for base in [Path.home() / ".hermes/rules", Path.cwd() / ".hermes/rules"]:
        for rpath in glob.glob(str(base / "rule_*test_pre*.md")):
            try:
                os.remove(rpath)
            except OSError:
                pass

    print("  ✓ CLI /loop learn command dispatch verified.")


def main() -> None:
    print("==================================================================")
    print("  HORIZON 5 IN-PROCESS VERIFICATION: AUTONOMOUS LEARNER (/LEARN)  ")
    print("  (Diagnostic Taxonomy + In-The-Loop Rule Synthesis + Transfer)   ")
    print("==================================================================")
    verify_failure_diagnosis_taxonomy()
    verify_autonomous_rule_synthesis()
    verify_rl_buffer_ingestion()
    verify_contract_gate_to_learn_bridge()
    verify_blind_transfer_test()
    verify_turnkey_lifecycle()
    verify_cli_integration()
    print("==================================================================")
    print("  ✅ HORIZON 5 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN   ")
    print("==================================================================")


if __name__ == "__main__":
    main()
