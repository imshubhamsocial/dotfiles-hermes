#!/usr/bin/env python3
"""
Verification Script for Phase 3: Native Contract Gate (ProcessVerifier + SymPy + AST Check)
=============================================================================================
Executes in-process contract verification against:
  1. ProcessVerifier System-1 Fast & System-2 Deep Consistency Checks
  2. SymPy Symbolic Verifier (Algebraic Equivalence, Derivation Chains, Bounds)
  3. AST Structural & Simplicity Verifier (Syntax, Required Symbols, Security Invariants, Anti-Bloat)
  4. NativeContractGate Unified Verdicts & Diagnostic Trace Formatting
  5. Closed-Loop Integration with LoopOrchestrator (/loop Enforcement & Bounded Interception)
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

from agent.core.mrp_planner import (
    MRPPlan,
    TaskDependencyGraph,
    TaskNode,
    TaskState,
    create_mrp_plan,
)
from agent.core.loop_orchestrator import (
    LoopOrchestrator,
    LoopReceipt,
    LoopTerminationReason,
)
from agent.core.contract_gate import (
    ContractCategory,
    ContractGateVerdict,
    ContractViolation,
    NativeContractGate,
    SymPyContractVerifier,
    ASTContractVerifier,
    get_native_contract_gate,
)
from agent.core.process_verifier import (
    ProcessVerifier,
    System1FastChecker,
    System2DeepVerifier,
)


def verify_process_verifier_layer() -> None:
    print("[1/5] Verifying ProcessVerifier System-1 & System-2 checks...")

    pv = ProcessVerifier()

    # 1. System-1: Empty output detection
    r_empty = pv.verify_step("", step_type="reasoning")
    assert not r_empty.passed, "Empty step must fail"
    assert "Empty step output" in r_empty.anomalies

    # 2. System-1: Hallucination / refusal pattern detection
    r_refusal = pv.verify_step("As an AI language model, I cannot verify this hardware.", step_type="reasoning")
    assert not r_refusal.passed, "Refusal boilerplate must fail"
    assert any("boilerplate" in a.lower() for a in r_refusal.anomalies)

    # 3. System-1: Mismatched brackets
    r_brackets = pv.verify_step("def foo():\n    return {'a': [1, 2, 3}", step_type="reasoning")
    assert not r_brackets.passed, "Mismatched brackets must fail"
    assert any("bracket" in a.lower() or "brace" in a.lower() for a in r_brackets.anomalies)

    # 4. System-2: Contradiction detection in reasoning
    contradictory_text = """
    We evaluate the boundary condition for the sparse cache.
    Wait, that's wrong, the cache size exceeds physical memory.
    Therefore the answer is 42.
    """
    r_contradict = pv.verify_step(contradictory_text, step_type="math")
    assert not r_contradict.passed, "Unresolved contradiction must fail System-2 check"
    assert any("contradiction" in a.lower() for a in r_contradict.anomalies)

    # 5. Sound reasoning step passes
    sound_text = """
    We examine the computational complexity of the block-sparse kernel.
    For N=4096 and block size B=256, the active blocks are 4.
    Hence, the total FLOP count scales as O(N * 4 * B), yielding a 4.0x compression ratio.
    In conclusion, the algorithmic bound is satisfied.
    """
    r_sound = pv.verify_step(sound_text, step_type="math")
    assert r_sound.passed, f"Sound reasoning step should pass: {r_sound.anomalies}"
    assert r_sound.confidence >= 0.85

    print("  ✓ ProcessVerifier System-1 fast heuristics and System-2 deep checks verified.")


def verify_sympy_layer() -> None:
    print("[2/5] Verifying SymPy symbolic invariant engine (algebraic identity & anti-drift)...")

    # 1. Algebraic identity equivalence
    ok_poly, msg_poly = SymPyContractVerifier.verify_equation(
        "(x + y)**3",
        "x**3 + 3*x**2*y + 3*x*y**2 + y**3"
    )
    assert ok_poly, f"Polynomial expansion should hold: {msg_poly}"

    ok_trig, msg_trig = SymPyContractVerifier.verify_equation(
        "sin(theta)**2 + cos(theta)**2",
        "1"
    )
    assert ok_trig, f"Trigonometric identity should hold: {msg_trig}"

    # 2. Rejection of invalid algebraic equivalence
    bad_poly, msg_bad = SymPyContractVerifier.verify_equation(
        "(x + y)**2",
        "x**2 + y**2"
    )
    assert not bad_poly, "Freshman's dream (x+y)^2 == x^2 + y^2 must be rejected"
    assert "Discrepancy" in msg_bad or "simplifies to" in msg_bad

    # 3. Multi-step derivation chain (anti-algebraic drift)
    valid_chain = [
        "2*(x + 3) + 4*x",
        "2*x + 6 + 4*x",
        "6*x + 6",
        "6*(x + 1)",
    ]
    chain_ok, chain_anom = SymPyContractVerifier.verify_derivation_chain(valid_chain)
    assert chain_ok, f"Valid derivation chain should pass: {chain_anom}"

    # Broken derivation chain (drift at step 2 -> 3)
    broken_chain = [
        "2*(x + 3) + 4*x",
        "2*x + 6 + 4*x",
        "6*x + 12",  # Drift! Should be 6*x + 6
        "6*(x + 2)",
    ]
    drift_ok, drift_anom = SymPyContractVerifier.verify_derivation_chain(broken_chain)
    assert not drift_ok, "Algebraic drift in derivation chain must be caught"
    assert len(drift_anom) >= 1
    assert "Derivation step 1 -> 2 broken" in drift_anom[0]

    # 4. Numeric Bounds verification
    bounds_ok, val, b_msg = SymPyContractVerifier.verify_numeric_bounds(
        expr_str="x**2 + 5",
        min_bound=10.0,
        max_bound=20.0,
        substitutions={"x": 3.0},  # 3^2 + 5 = 14
    )
    assert bounds_ok, f"Expression bounds should hold: {b_msg}"
    assert val == 14.0

    print("  ✓ SymPy algebraic identity, derivation drift detection, and bounds certified.")


def verify_ast_check_layer() -> None:
    print("[3/5] Verifying AST Structural & Simplicity Verifier...")

    # 1. Syntax error precision
    bad_syntax = "def compute_hash(val):\n    return hash(val"
    syn_ok, tree, syn_violations = ASTContractVerifier.verify_python_syntax(bad_syntax)
    assert not syn_ok
    assert tree is None
    assert any("syntax" in v.rule.lower() for v in syn_violations)

    # 2. Security invariants: forbidden eval/exec detection
    unsafe_code = """
def run_dynamic(payload: str):
    return eval(payload)
"""
    u_ok, u_tree, _ = ASTContractVerifier.verify_python_syntax(unsafe_code)
    assert u_ok and u_tree is not None
    sec_violations = ASTContractVerifier.verify_security_invariants(u_tree)
    assert len(sec_violations) >= 1
    assert any("forbidden_function_call" == v.rule for v in sec_violations)

    # 3. Security invariants: naked except with pass
    naked_code = """
def silent_fail():
    try:
        do_something()
    except:
        pass
"""
    n_ok, n_tree, _ = ASTContractVerifier.verify_python_syntax(naked_code)
    assert n_ok and n_tree is not None
    naked_violations = ASTContractVerifier.verify_security_invariants(n_tree)
    assert any("naked_except_pass" == v.rule for v in naked_violations)

    # 4. Required symbols / exports verification
    module_code = """
def solve_equation(expr):
    return expr

class EquationSolver:
    pass

VERSION = "1.0.0"
"""
    m_ok, m_tree, _ = ASTContractVerifier.verify_python_syntax(module_code)
    assert m_ok and m_tree is not None
    # All present
    exp_ok = ASTContractVerifier.verify_required_exports(m_tree, ["solve_equation", "EquationSolver", "VERSION"])
    assert len(exp_ok) == 0

    # Missing export
    exp_missing = ASTContractVerifier.verify_required_exports(m_tree, ["solve_equation", "NonExistentHelper"])
    assert len(exp_missing) == 1
    assert "NonExistentHelper" in exp_missing[0].message

    # 5. Simplicity / anti-bloat integration
    bloated = """
class Wrapper:
    def __init__(self, val):
        self.val = val
    def get(self):
        return self.val
"""
    simp_ok, score, simp_viols = ASTContractVerifier.verify_simplicity(bloated, strict=True)
    assert not simp_ok, "Over-engineered single-method class must fail simplicity check"
    assert len(simp_viols) >= 1

    print("  ✓ AST syntax parsing, security boundaries, exports, and YAGNI simplicity certified.")


def verify_native_contract_gate_unified() -> None:
    print("[4/5] Verifying NativeContractGate unified verdicts & diagnostic traces...")

    gate = NativeContractGate()

    # 1. Code verification: Clean, idiomatically lean code
    clean_code = """
from pathlib import Path

def read_manifest(path: str) -> str:
    \"\"\"Read and return manifest text content.\"\"\"
    return Path(path).read_text(encoding="utf-8")
"""
    v_code = gate.verify_code(clean_code, required_symbols=["read_manifest"])
    assert v_code.passed, f"Clean code should pass: {v_code.violations}"
    assert v_code.ast_score >= 0.85
    assert len(v_code.violations) == 0

    # 2. Code verification: Code with syntax error produces structured diagnostic trace
    broken_code = "def broken():\n    return [1, 2,"
    v_broken = gate.verify_code(broken_code)
    assert not v_broken.passed
    trace = v_broken.to_diagnostic_trace()
    assert "[ContractGate:" in trace
    assert "Status: FAILED" in trace
    assert "SyntaxError" in trace

    # 3. Math verification: Sound derivation & equations
    math_text = """
    We evaluate the kinetic friction dissipation.
    The work done equals the change in kinetic energy: W = Delta K.
    Therefore, the final velocity satisfies v_f = sqrt(v_0^2 - 2*mu*g*d).
    In conclusion, the deceleration profile is verified.
    """
    v_math = gate.verify_math_reasoning(
        reasoning_text=math_text,
        symbolic_equations=[("(a + b)**2", "a**2 + 2*a*b + b**2")],
        derivation_steps=["(x - 1)*(x + 1)", "x**2 - 1"],
    )
    assert v_math.passed, f"Valid math reasoning should pass: {v_math.violations}"
    assert v_math.symbolic_verified

    # 4. Math verification: Algebraic violation produces actionable remediation
    v_bad_math = gate.verify_math_reasoning(
        reasoning_text=math_text,
        symbolic_equations=[("(a + b)**2", "a**2 + b**2")],
    )
    assert not v_bad_math.passed
    assert any(v.category == ContractCategory.SYMBOLIC_MATH for v in v_bad_math.violations)
    assert len(v_bad_math.remediation_hints) > 0

    print("  ✓ NativeContractGate unified code and math reasoning verification verified.")


def verify_loop_orchestrator_closed_loop_gate() -> None:
    print("[5/5] Verifying closed-loop contract gate enforcement inside LoopOrchestrator...")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_gate_loop.db"
        gate = NativeContractGate()

        # 1. Successful Plan with Contract Compliance
        tasks_pass = [
            {
                "id": "generate_clean_code",
                "title": "Generate clean helper function",
                "description": "Produce lean Python module",
                "depends_on": [],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'def calculate_ratio(a, b):\n    return a / b if b != 0 else 0.0'",
            },
            {
                "id": "verify_calculation",
                "title": "Verify ratio output",
                "description": "Confirm mathematical validity",
                "depends_on": ["generate_clean_code"],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'Ratio verification confirmed. The final answer is valid.'",
            },
        ]

        plan_pass = create_mrp_plan(goal="Generate Verified Code", tasks=tasks_pass, existing_symbols=["echo"])
        orch_pass = LoopOrchestrator(max_steps=5, db_path=test_db, contract_gate=gate)
        receipt_pass = orch_pass.execute_plan(plan_pass)

        assert receipt_pass.termination_reason == LoopTerminationReason.DONE
        assert len(receipt_pass.completed_task_ids) == 2
        assert len(receipt_pass.failed_task_ids) == 0

        # 2. Plan Interception on Contract Gate Failure (Refusal Boilerplate / Broken Syntax)
        tasks_fail = [
            {
                "id": "hallucinated_step",
                "title": "Produce module",
                "description": "Returns refusal boilerplate",
                "depends_on": [],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'As an AI language model, I cannot write this code.'",
            },
            {
                "id": "unreached_step",
                "title": "Dependent Step",
                "description": "Should be blocked",
                "depends_on": ["hallucinated_step"],
                "inputs": [],
                "outputs": [],
                "verification": "echo 'Never run'",
            },
        ]

        plan_fail = create_mrp_plan(goal="Failing Contract Plan", tasks=tasks_fail, existing_symbols=["echo"])
        orch_fail = LoopOrchestrator(max_steps=5, db_path=test_db, contract_gate=gate)
        receipt_fail = orch_fail.execute_plan(plan_fail)

        assert receipt_fail.termination_reason == LoopTerminationReason.BLOCKED
        assert "hallucinated_step" in receipt_fail.failed_task_ids
        assert "unreached_step" not in receipt_fail.completed_task_ids

        # Confirm failure record contains the Contract Gate Diagnostic Trace
        failed_record = receipt_fail.records[0]
        assert "Contract Gate Failure" in failed_record.result.error
        assert "boilerplate" in failed_record.result.error.lower()

    print(f"  ✓ Closed-loop contract enforcement confirmed: compliant tasks DONE, contract violations BLOCKED with diagnostic traces.")


def main() -> None:
    print("==================================================================")
    print("  PHASE 3 IN-PROCESS VERIFICATION: NATIVE CONTRACT GATE           ")
    print("  (ProcessVerifier + SymPy Symbolic Invariants + AST Check)       ")
    print("==================================================================")
    verify_process_verifier_layer()
    verify_sympy_layer()
    verify_ast_check_layer()
    verify_native_contract_gate_unified()
    verify_loop_orchestrator_closed_loop_gate()
    print("==================================================================")
    print("  ✅ PHASE 3 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN     ")
    print("==================================================================")


if __name__ == "__main__":
    main()
