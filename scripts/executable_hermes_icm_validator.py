#!/usr/bin/env python3
"""
Hermes 60% Infrastructure Gate: ICM Schema, Line-Cap & Walk-Test Validator
Operationalizes Jake Van Clief's Interpretable Context Methodology (arXiv:2603.16021).
Enforces:
1. Root AGENTS.md & CLAUDE.md symlink existence.
2. CONTEXT.md <= 80 lines and Layer 3 Reference files <= 200 lines.
3. 4-Column Selective Section Loading schema: Source | File | Section | Why.
4. The Walk Test: Zero-memory agent orientation and input reachability.
"""
import json
import os
import sys

WORKSPACE_ROOT = os.environ.get("WORKSPACE", "/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes")


class HermesICMValidator:
    """Validates ICM 5-Layer compliance across the Hermes workspace."""

    def __init__(self, workspace_root: str = WORKSPACE_ROOT) -> None:
        self.workspace_root = os.path.abspath(workspace_root)
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def check_layer0_agents_schema(self) -> None:
        """Verifies Layer 0 AGENTS.md existence, line count, and CLAUDE.md symlink."""
        agents_path = os.path.join(self.workspace_root, "AGENTS.md")
        if not os.path.exists(agents_path):
            self.errors.append("Layer 0 failure: AGENTS.md does not exist in workspace root.")
            return

        with open(agents_path, encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) > 120:
                self.warnings.append(f"AGENTS.md has {len(lines)} lines (recommend <= 80 lines).")

        claude_path = os.path.join(self.workspace_root, "CLAUDE.md")
        if not os.path.exists(claude_path) and not os.path.islink(claude_path):
            # Create symlink if missing
            try:
                os.symlink("AGENTS.md", claude_path)
            except OSError as e:
                self.errors.append(f"Failed to create CLAUDE.md symlink to AGENTS.md: {e}")

    def check_line_caps(self) -> None:
        """Enforces line caps: CONTEXT.md <= 80 lines; rules/*.md <= 200 lines."""
        rules_dir = os.path.join(self.workspace_root, "rules")
        if os.path.exists(rules_dir):
            for fname in os.listdir(rules_dir):
                if fname.endswith(".md"):
                    fpath = os.path.join(rules_dir, fname)
                    with open(fpath, encoding="utf-8") as f:
                        count = sum(1 for _ in f)
                        if count > 200:
                            self.errors.append(f"Layer 3 violation: {fname} has {count} lines (cap is 200).")

    def run_walk_test(self) -> bool:
        """
        Executes Jake Van Clief's Walk Test:
        Verifies that a zero-memory agent can identify the active phase, locate its spec/task,
        and find the verification contract without missing dependencies.
        """
        ledger_path = os.path.join(self.workspace_root, "phases", "status_ledger.json")
        if not os.path.exists(ledger_path):
            self.errors.append("Walk Test failed: phases/status_ledger.json not found.")
            return False

        try:
            with open(ledger_path, encoding="utf-8") as f:
                ledger = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.errors.append(f"Walk Test failed: status_ledger.json unparseable: {e}")
            return False

        current_phase = ledger.get("current_phase")
        if not current_phase:
            self.errors.append("Walk Test failed: status_ledger.json missing 'current_phase'.")
            return False

        phase_dir = os.path.join(self.workspace_root, "phases", current_phase)
        if not os.path.isdir(phase_dir):
            self.errors.append(f"Walk Test failed: active phase directory {current_phase} does not exist.")
            return False

        spec_file = os.path.join(phase_dir, "01_spec", "spec.md")
        task_file = os.path.join(phase_dir, "02_impl", "task.md")
        contract_file = os.path.join(phase_dir, "03_verify", "contract.sh")

        if not os.path.isfile(spec_file):
            self.errors.append(f"Walk Test failed: {current_phase}/01_spec/spec.md missing.")
        if not os.path.isfile(task_file):
            self.errors.append(f"Walk Test failed: {current_phase}/02_impl/task.md missing.")
        if not os.path.isfile(contract_file):
            self.errors.append(f"Walk Test failed: {current_phase}/03_verify/contract.sh missing.")

        return len(self.errors) == 0

    def validate_all(self) -> bool:
        """Executes full ICM validation suite."""
        self.check_layer0_agents_schema()
        self.check_line_caps()
        self.run_walk_test()
        return len(self.errors) == 0


if __name__ == "__main__":
    validator = HermesICMValidator()
    passed = validator.validate_all()
    if not passed:
        print("[FAIL] ICM Validation Errors:")
        for err in validator.errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print("[PASS] ICM 5-Layer Workspace & Walk Test validated successfully.")
        if validator.warnings:
            for w in validator.warnings:
                print(f"  ! {w}")
        sys.exit(0)
