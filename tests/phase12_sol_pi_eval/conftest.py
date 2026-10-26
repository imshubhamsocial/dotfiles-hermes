"""Testbed conftest.py epistemic verification receipt hook (Phase 12 / Layer 1)."""

import hashlib
import json
import os
import pathlib
import subprocess


def pytest_sessionfinish(session, exitstatus):
    """Generates /tmp/hermes_verified_receipt.json if all modified source files were tested and passed."""
    try:
        diff_files = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], text=True).splitlines()
    except Exception:
        diff_files = []

    mod_py = [
        f for f in diff_files
        if f.endswith(".py")
        and not os.path.basename(f).startswith("test_")
        and f != "conftest.py"
        and os.path.exists(f)
    ]

    ran_items = {
        os.path.basename(str(getattr(item, "path", getattr(item, "fspath", ""))))
        for item in getattr(session, "items", [])
    }

    missing = [f for f in mod_py if f"test_{os.path.basename(f)}" not in ran_items]

    if missing or session.testscollected == 0:
        print(f"\n⚠️ VERIFICATION INCOMPLETE: Modified {missing} not covered by executed tests ({ran_items}).")
    elif exitstatus == 0:
        try:
            sha = hashlib.sha256(subprocess.check_output(["git", "diff", "HEAD"])).hexdigest()
        except Exception:
            sha = ""
        receipt_data = {
            "exitstatus": 0,
            "git_diff_sha256": sha,
            "tested": list(ran_items),
            "modified": mod_py
        }
        pathlib.Path("/tmp/hermes_verified_receipt.json").write_text(json.dumps(receipt_data, indent=2))
        print("\n✅ VERIFICATION RECEIPT VALIDATED: All modified modules tested and passed (exit 0).")
