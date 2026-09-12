#!/usr/bin/env python3
"""
Verification Script for SMART Specification & Clean-Slate Regeneration Engine
=============================================================================
Absorbed from arXiv:2609.05364 (Design Docs Are All You Need: The SMART Paradigm).
Validates:
  1. Topological Spec DAG Discovery (prerequisite sorting)
  2. Dependency Cycle Detection (Kahn algorithm topological assertion)
  3. SymPy Minimal Symbolic IR & Reconciliation Anchors Evaluation
  4. Clean-Slate Module Regeneration (C_t = G(S_t), D_{t+1} = 0.0)
  5. Failed Anchor Interception & Generation Debt Prevention
"""

import os
import sys
import tempfile
from pathlib import Path

# Resolve hermes-agent path dynamically
_hermes_dir = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parents[1]))
for p in [
    _hermes_dir / "hermes-agent",
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.smart_engine import (
    CleanSlateRegenerator,
    DocDependencyResolver,
    ReconciliationAnchor,
    SmartRebuildReceipt,
    SpecDoc,
)


def verify_spec_dag_discovery() -> None:
    print("[1/5] Verifying Topological Spec DAG Discovery & Ordering...")
    specs_dir = _hermes_dir / "specs"
    resolver = DocDependencyResolver(specs_dir)
    specs = resolver.scan()

    assert len(specs) >= 3, f"Expected at least 3 specs, found {len(specs)}"
    assert "core_architecture" in specs
    assert "sparse_attention" in specs
    assert "online_storage" in specs

    ordered = resolver.topological_sort()
    order_ids = [d.spec_id for d in ordered]

    # core_architecture has no prereqs, so must appear before its dependents
    core_idx = order_ids.index("core_architecture")
    sparse_idx = order_ids.index("sparse_attention")
    storage_idx = order_ids.index("online_storage")

    assert core_idx < sparse_idx, "core_architecture must precede sparse_attention in topological order"
    assert core_idx < storage_idx, "core_architecture must precede online_storage in topological order"

    print(f"  ✓ Topological order verified: {' -> '.join(order_ids)}")


def verify_cycle_detection() -> None:
    print("[2/5] Verifying Dependency Cycle Detection...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        (tmp_p / "spec_a.md").write_text('---\nid: spec_a\nprerequisites: ["spec_b"]\n---\n# A', encoding="utf-8")
        (tmp_p / "spec_b.md").write_text('---\nid: spec_b\nprerequisites: ["spec_a"]\n---\n# B', encoding="utf-8")

        resolver = DocDependencyResolver(tmp_p)
        resolver.scan()
        try:
            resolver.topological_sort()
            assert False, "Cyclic dependency must raise ValueError"
        except ValueError as exc:
            assert "Cyclic dependency detected" in str(exc)
            print("  ✓ Cyclic dependency trap confirmed: successfully detected and blocked.")


def verify_sympy_reconciliation_anchors() -> None:
    print("[3/5] Verifying SymPy Minimal Symbolic IR & Reconciliation Anchors...")
    anchor_valid = ReconciliationAnchor(
        symbolic_expr="(N * N) / (N * k * B)",
        variable_bindings={"N": 8192, "k": 4, "B": 256},
        expected_value=8.0,
    )
    passed, val, diff = anchor_valid.evaluate()
    assert passed, f"Anchor should pass: val={val}, diff={diff}"
    assert abs(val - 8.0) < 1e-6

    # Test anchor with trigonometric or non-linear closed-form roll-up
    anchor_trig = ReconciliationAnchor(
        symbolic_expr="sin(x)**2 + cos(x)**2",
        variable_bindings={"x": 1.57079632679},
        expected_value=1.0,
    )
    passed_trig, val_trig, _ = anchor_trig.evaluate()
    assert passed_trig, "Trig identity anchor must evaluate to 1.0"

    print("  ✓ SymPy analytical expressions and reconciliation anchors evaluate to exact presets.")


def verify_clean_slate_regeneration() -> None:
    print("[4/5] Verifying Clean-Slate Regeneration (C_t = G(S_t), D_{t+1} = 0.0)...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_p = Path(tmp_dir)
        specs_dir = _hermes_dir / "specs"
        resolver = DocDependencyResolver(specs_dir)
        resolver.scan()
        ordered_specs = resolver.topological_sort()

        regenerator = CleanSlateRegenerator(workspace_root=workspace_p)

        receipts: list[SmartRebuildReceipt] = []
        for spec_doc in ordered_specs:
            receipt = regenerator.regenerate_spec(spec_doc)
            assert receipt.success, f"Regeneration failed: {receipt.message}"
            assert receipt.generation_debt_delta == 0.0, "Generation debt must be 0.0 by construction"
            assert receipt.anchors_passed == receipt.total_anchors, "All reconciliation anchors must pass"
            receipts.append(receipt)

            # Check that generated code file exists and is valid Python
            gen_file = workspace_p / spec_doc.target_artifact
            assert gen_file.exists(), f"Target file '{gen_file}' was not written"
            code_text = gen_file.read_text(encoding="utf-8")
            import ast
            ast.parse(code_text)

        print(f"  ✓ Successfully regenerated {len(receipts)} modules clean-slate (all generation debts D_{{t+1}} = 0.0).")


def verify_failed_anchor_interception() -> None:
    print("[5/5] Verifying Anchor Failure Interception & Drift Prevention...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_p = Path(tmp_dir)
        doc = SpecDoc(
            spec_id="flawed_spec",
            title="Flawed Spec",
            version=1,
            prerequisites=[],
            target_artifact="generated/flawed.py",
            content="Spec with impossible reconciliation anchor",
            reconciliation_anchors=[
                ReconciliationAnchor(
                    symbolic_expr="2 * x",
                    variable_bindings={"x": 5.0},
                    expected_value=999.0,  # Deliberate mismatch (10.0 != 999.0)
                )
            ],
        )

        regenerator = CleanSlateRegenerator(workspace_root=workspace_p)
        receipt = regenerator.regenerate_spec(doc)

        assert not receipt.success, "Regeneration with failing anchor must be blocked"
        assert receipt.generation_debt_delta > 0.0, "Failing anchor must record non-zero debt delta"
        assert not (workspace_p / "generated/flawed.py").exists(), "Flawed artifact must never be written to disk"
        print("  ✓ Flawed specification with mismatched anchor cleanly intercepted.")


def main():
    print("==================================================================")
    print("  HERMES CAPABILITY CONTRACT: SMART SPECIFICATION REGENERATION   ")
    print("  (arXiv:2609.05364: Design Docs Are All You Need - Zero Debt)   ")
    print("==================================================================")
    try:
        verify_spec_dag_discovery()
        verify_cycle_detection()
        verify_sympy_reconciliation_anchors()
        verify_clean_slate_regeneration()
        verify_failed_anchor_interception()
        print("==================================================================")
        print("  ✅ SMART ENGINE CONTRACT 100% COMPLETE — ALL GATES PASSING     ")
        print("==================================================================")
        return 0
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Contract verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
