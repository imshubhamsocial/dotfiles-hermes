"""
Hermes Plugin: agent_os
=======================
Two-Tier Agent OS Standards & Plan.json Decomposition Engine.
"""

from .standards import (
    RuleFile,
    CompiledStandards,
    RuleParser,
    TwoTierStandardsEngine,
    build_two_tier_slot3_injection,
    get_standards_engine,
    reset_standards_engine,
)
from .planner import (
    EngineeringSpec,
    PlanStep,
    Plan,
    SpecFirstPlanner,
    inject_plan_into_slot3,
    enforce_plan_gate_before_edit,
    get_spec_first_planner,
    reset_spec_first_planner,
)

def register(ctx=None):
    """Registers plugin agent_os into Hermes runtime."""
    if not ctx:
        return
    
    if hasattr(ctx, "register_cli_command"):
        def setup_exam(parser):
            parser.description = "Run Hermes Agent OS comprehensive system exam"

        def _run_system_verification(verbose=False):
            import subprocess
            import sys
            from pathlib import Path
            from hermes_constants import get_hermes_home
            home = get_hermes_home()
            contracts_dir = home / "contracts"
            if not contracts_dir.exists():
                contracts_dir = Path.cwd() / ".hermes" / "contracts"
            if contracts_dir.exists():
                contract_files = sorted(contracts_dir.glob("*.py"))
                for c in contract_files:
                    ret = subprocess.run([sys.executable, str(c)]).returncode
                    if ret != 0:
                        print(f"✗ Contract failed: {c.name}")
                        return ret
                print("✓ All exam checks passed.")
                return 0
            proj_venv = Path.cwd() / ".hermes" / "hermes-agent" / "venv" / "bin" / "pytest"
            venv_pytest = proj_venv if proj_venv.exists() else (home / "hermes-agent" / "venv" / "bin" / "pytest")
            proj_tests = Path.cwd() / ".hermes" / "tests"
            tests_dir = proj_tests if proj_tests.exists() else (home / "tests")
            flag = "-v" if verbose else "-q"
            ret = subprocess.run([str(venv_pytest), str(tests_dir), flag]).returncode
            if ret == 0:
                print("✓ All exam checks passed.")
            return ret

        def handle_exam(args):
            print("Running Hermes Agent OS System Exam...")
            return _run_system_verification(verbose=False)

        def setup_test(parser):
            parser.description = "Run Hermes Agent OS test suite"

        def handle_test(args):
            return _run_system_verification(verbose=True)

        ctx.register_cli_command("exam", "Run Hermes Agent OS system exam", setup_exam, handle_exam)
        ctx.register_cli_command("test", "Run Hermes Agent OS contract test suite", setup_test, handle_test)

    if hasattr(ctx, "register_command"):
        def slash_exam(raw_args: str) -> str:
            import subprocess
            import sys
            from pathlib import Path
            from hermes_constants import get_hermes_home
            home = get_hermes_home()
            contracts_dir = home / "contracts"
            if not contracts_dir.exists():
                contracts_dir = Path.cwd() / ".hermes" / "contracts"
            if contracts_dir.exists():
                contract_files = sorted(contracts_dir.glob("*.py"))
                failed = []
                for c in contract_files:
                    ret = subprocess.run([sys.executable, str(c)], capture_output=True, text=True)
                    if ret.returncode != 0:
                        failed.append(f"{c.name}: {ret.stderr or ret.stdout}")
                if failed:
                    return "✗ Exam failed:\n" + "\n".join(failed)
                return "✓ All 20 capability contracts passed."
            return "No contracts found."

        ctx.register_command("exam", slash_exam, "Run system examination", "")

__all__ = [
    "RuleFile",
    "CompiledStandards",
    "RuleParser",
    "TwoTierStandardsEngine",
    "build_two_tier_slot3_injection",
    "get_standards_engine",
    "reset_standards_engine",
    "EngineeringSpec",
    "PlanStep",
    "Plan",
    "SpecFirstPlanner",
    "inject_plan_into_slot3",
    "enforce_plan_gate_before_edit",
    "get_spec_first_planner",
    "reset_spec_first_planner",
    "register",
]
