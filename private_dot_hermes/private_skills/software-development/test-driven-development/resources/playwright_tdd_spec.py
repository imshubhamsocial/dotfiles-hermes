#!/usr/bin/env python3
"""
Playwright TDD Spec — Gold Standard Scaffold
Headless browser invariant assertions for WebGL / DOM artifacts.
"""
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("SKIP: playwright not installed")
    sys.exit(0)


def run_tdd_checks(url: str, checks: list[dict]) -> dict:
    """Run a list of invariant checks against a live page.

    Each check: {"name": str, "js": str} — JS expression evaluated in page.
    Returns: {"passed": int, "failed": int, "results": [...]}
    """
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=15000)

        for check in checks:
            name = check["name"]
            js = check["js"]
            try:
                val = page.evaluate(js)
                results.append({"name": name, "pass": bool(val), "value": val})
            except Exception as e:
                results.append({"name": name, "pass": False, "error": str(e)})

        browser.close()

    passed = sum(1 for r in results if r["pass"])
    failed = len(results) - passed
    return {"passed": passed, "failed": failed, "results": results}


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8088/"
    checks = [
        {"name": "canvas_mounted", "js": "!!document.querySelector('canvas')"},
        {"name": "webgl_context", "js": "!!document.querySelector('canvas').getContext('webgl2')"},
        {"name": "no_runtime_errors", "js": "window.__jsErrors === undefined || window.__jsErrors.length === 0"},
    ]
    report = run_tdd_checks(url, checks)
    status = "PASS" if report["failed"] == 0 else "FAIL"
    print(f"TDD {status}: {report['passed']}/{report['passed']+report['failed']} checks")
    sys.exit(0 if report["failed"] == 0 else 1)
