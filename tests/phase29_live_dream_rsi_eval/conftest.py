"""Testbed conftest.py epistemic verification receipt hook (Phase 29)."""

import hashlib
import json
import os
import pathlib
import subprocess
import sys


def pytest_sessionfinish(session, exitstatus):
    """Generates /tmp/hermes_verified_receipt.json if all modified source files were tested and passed."""
    testbed_root = pathlib.Path(__file__).resolve().parent
    ref = "HEAD"
    try:
        raw_diff = subprocess.check_output(
            ["git", "-C", str(testbed_root), "diff", "--name-only", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
        mod_py = [
            f for f in raw_diff
            if f.endswith(".py")
            and not os.path.basename(f).startswith("test_")
            and f != "conftest.py"
            and (testbed_root / f).exists()
        ]
        if not mod_py:
            last_commit = subprocess.check_output(
                ["git", "-C", str(testbed_root), "log", "-n", "1", "--format=%H", "--", "scenario/"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if last_commit:
                ref = f"{last_commit}^!"
                raw_diff = subprocess.check_output(
                    ["git", "-C", str(testbed_root), "diff-tree", "--no-commit-id", "--name-only", "-r", last_commit],
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).splitlines()
                mod_py = [
                    f for f in raw_diff
                    if f.endswith(".py")
                    and not os.path.basename(f).startswith("test_")
                    and f != "conftest.py"
                    and (testbed_root / f).exists()
                ]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        mod_py = []

    ran_items = {
        os.path.basename(str(getattr(item, "path", getattr(item, "fspath", ""))))
        for item in getattr(session, "items", [])
    }

    def is_covered(f):
        stem = pathlib.Path(f).stem
        return (
            f"test_{os.path.basename(f)}" in ran_items
            or stem in sys.modules
            or any(stem in item for item in ran_items)
        )

    missing = [f for f in mod_py if not is_covered(f)]

    if missing or session.testscollected == 0:
        print(f"\n⚠️ VERIFICATION INCOMPLETE: Modified {missing} not covered by executed tests ({ran_items}).")
    elif exitstatus == 0 and mod_py:
        try:
            sha = hashlib.sha256(
                subprocess.check_output(
                    ["git", "-C", str(testbed_root), "diff", ref],
                    stderr=subprocess.DEVNULL,
                )
            ).hexdigest()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            sha = ""
        receipt_data = {
            "exitstatus": 0,
            "git_diff_sha256": sha,
            "tested": list(ran_items),
            "modified": mod_py
        }
        pathlib.Path("/tmp/hermes_verified_receipt.json").write_text(json.dumps(receipt_data, indent=2))
        print("\n✅ VERIFICATION RECEIPT VALIDATED: All modified modules tested and passed (exit 0).")
