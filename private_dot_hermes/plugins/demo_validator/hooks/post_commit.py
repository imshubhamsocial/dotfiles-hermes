#!/usr/bin/env python3
"""Demo plugin post-commit hook: logs successful mutations."""
import time


def run(context: dict) -> dict:
    return {
        "ok": True,
        "detail": f"Post-commit logged at {int(time.time())}.",
        "event": "plugin_post_commit",
    }
