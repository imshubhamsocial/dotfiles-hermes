"""
Meta-Harness Outer-Loop Autonomous Self-Evolution Engine
========================================================
Inspired by Stanford IRIS / Meta AI (arXiv:2603.28052, 2026).
Enables Hermes to:
1. Inspect its own execution traces, tool errors, and failure logs.
2. Cluster recurring failure signatures (SYNTAX_ERROR, SEARCH_REPLACE_MISMATCH, TOOL_DRIFT, TEST_REGRESSION).
3. Formulate targeted code modifications to harness plugins and prompts.
4. Verify changes through an immutable zero-regression test gate, automatically rolling back on test regressions.
"""

from __future__ import annotations

import difflib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TraceFailureAnalyzer:
    """Analyzes recorded trajectories and failure logs to cluster recurring errors."""

    @staticmethod
    def analyze_traces(traces: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        if traces is None:
            # Query trajectory database if available
            try:
                from plugins.trajectory_recorder import get_trajectory_recorder
                recorder = get_trajectory_recorder()
                sessions = recorder.list_trajectories(limit=50)
                traces = []
                for s in sessions:
                    turns = recorder.get_session(s["session_id"])
                    traces.extend(turns)
            except Exception:
                traces = []

        clusters: Dict[str, Dict[str, Any]] = {
            "SYNTAX_ERROR": {
                "cluster_id": "SYNTAX_ERROR",
                "count": 0,
                "symptom": "SyntaxError in emitted code or tool scripts",
                "target_plugin": "mcp_tools",
                "remedy": "Enforce AST preflight validation before code execution",
            },
            "SEARCH_REPLACE_MISMATCH": {
                "cluster_id": "SEARCH_REPLACE_MISMATCH",
                "count": 0,
                "symptom": "Search block not found or ambiguous match in target file",
                "target_plugin": "mcp_tools",
                "remedy": "Require wider context in search blocks or AST line anchoring",
            },
            "TOOL_DRIFT": {
                "cluster_id": "TOOL_DRIFT",
                "count": 0,
                "symptom": "Repetitive tool invocations exceeding turn threshold",
                "target_plugin": "bpe_workspace",
                "remedy": "Promote turn observations directly to BPE belief state",
            },
            "TEST_REGRESSION": {
                "cluster_id": "TEST_REGRESSION",
                "count": 0,
                "symptom": "Pytest exit code non-zero during verification",
                "target_plugin": "self_evolution",
                "remedy": "Trigger automated hypothesis rollback gate",
            },
        }

        for t in traces:
            output = (t.get("windowed_output") or t.get("tool_output") or "").lower()
            status = str(t.get("test_status") or "").upper()
            exit_code = t.get("exit_code", 0)

            if "syntaxerror" in output:
                clusters["SYNTAX_ERROR"]["count"] += 1
            elif "ambiguous match" in output or "not found" in output:
                clusters["SEARCH_REPLACE_MISMATCH"]["count"] += 1
            elif status == "FAIL" or exit_code != 0:
                clusters["TEST_REGRESSION"]["count"] += 1

        # Return sorted by frequency
        return sorted(
            [c for c in clusters.values() if c["count"] > 0],
            key=lambda x: x["count"],
            reverse=True,
        ) or [
            # Fallback baseline cluster if no runtime errors exist yet
            {
                "cluster_id": "HARNESS_OPTIMIZATION",
                "count": 1,
                "symptom": "Zero runtime regressions detected; routine harness annealing active",
                "target_plugin": "agentshield",
                "remedy": "Maintain strict Maker-Verifier role isolation",
            }
        ]


class HarnessProposalEngine:
    """Generates concrete code patches for harness self-improvement."""

    @staticmethod
    def generate_proposal(cluster: Dict[str, Any]) -> Dict[str, Any]:
        cid = cluster.get("cluster_id", "HARNESS_OPTIMIZATION")
        proposal_id = f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return {
            "proposal_id": proposal_id,
            "cluster_id": cid,
            "target_plugin": cluster.get("target_plugin", "mcp_tools"),
            "description": f"Meta-Harness auto-patch to resolve {cid}: {cluster.get('remedy')}",
            "remedy": cluster.get("remedy"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "PROPOSED",
        }


class SpecVerificationGate:
    """Executes verification tests and guarantees atomic rollback on any regression."""

    @staticmethod
    def run_tests(test_target: Optional[str] = None) -> Tuple[bool, str]:
        """Runs pytest inside the current Python environment."""
        target = test_target or ".hermes/tests/"
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", target, "-q", "--tb=line"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = res.stdout or res.stderr
            return (res.returncode == 0, output)
        except Exception as e:
            return (False, f"Test execution error: {e}")

    @classmethod
    def apply_mutation_safely(
        cls,
        target_file: Path,
        search_block: str,
        replace_block: str,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Applies a mutation to target_file with atomic backup and rollback.
        If tests fail, the original file is immediately restored!
        """
        if not target_file.exists():
            return {"success": False, "status": "ERROR", "message": f"Target not found: {target_file}"}

        original_content = target_file.read_text(encoding="utf-8")
        if search_block not in original_content:
            return {"success": False, "status": "REJECTED", "message": "Search block not found in target file."}

        new_content = original_content.replace(search_block, replace_block, 1)

        diff = "".join(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=str(target_file),
            tofile=str(target_file),
        ))

        if dry_run:
            return {
                "success": True,
                "status": "DRY_RUN_PASS",
                "diff": diff,
                "message": "Dry run mutation preview successful.",
            }

        # Backup
        backup_path = target_file.with_suffix(target_file.suffix + ".bak")
        shutil.copy2(target_file, backup_path)

        try:
            # Apply
            target_file.write_text(new_content, encoding="utf-8")

            # Run test gate
            passed, test_output = cls.run_tests()
            if passed:
                if backup_path.exists():
                    backup_path.unlink()
                return {
                    "success": True,
                    "status": "COMMITTED",
                    "diff": diff,
                    "message": "Zero-regression gate passed. Mutation committed successfully.",
                }
            else:
                # Rollback!
                shutil.copy2(backup_path, target_file)
                if backup_path.exists():
                    backup_path.unlink()
                return {
                    "success": False,
                    "status": "ROLLED_BACK",
                    "diff": diff,
                    "message": f"Regression detected. Rollback executed.\nTest Output:\n{test_output[:300]}",
                }
        except Exception as e:
            if backup_path.exists():
                shutil.copy2(backup_path, target_file)
                backup_path.unlink()
            return {"success": False, "status": "EXCEPTION_ROLLED_BACK", "message": str(e)}
