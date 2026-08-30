#!/usr/bin/env python3.13
"""
Hermes Agent OS — Hub Mode Fleet Commander CLI (Roadmap 6 - Milestone 5)
=======================================================================
Coordinates multi-agent delegation across specialist roles (@researcher, @architect,
@coder, @tester), tracking state persistently in ~/.hermes/hub/state.json.

Usage:
    python3.13 bin/hub_cli.py status
    python3.13 bin/hub_cli.py spawn <role> "<goal>"
    python3.13 bin/hub_cli.py complete <task_id> --verdict "<summary>"
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import uuid
from pathlib import Path


def find_hub_state_path() -> Path:
    candidates = [
        Path.home() / ".hermes/hub/state.json",
        Path(__file__).resolve().parents[1] / "hub/state.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Default
    p = Path.home() / ".hermes/hub/state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_hub_state() -> dict:
    p = find_hub_state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": "1.0.0", "active_tasks": [], "completed_tasks": [], "agent_pool": {}, "message_bus": []}


def save_hub_state(state: dict):
    p = find_hub_state_path()
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def cmd_status(args):
    state = load_hub_state()
    print("================================================================")
    print("            HERMES AGENT OS — HUB MODE COMMAND CENTER           ")
    print("================================================================\n")
    print(f"Active Tasks ({len(state.get('active_tasks', []))}):")
    for t in state.get("active_tasks", []):
        print(f"  [{t['task_id'][:8]}] @{t['role']} | Goal: {t['goal']}")
        print(f"     Spawned: {t['spawned_at']} | Status: {t['status']}")
    print()

    print("Specialist Agent Pool:")
    for role, info in state.get("agent_pool", {}).items():
        last = info.get("last_active") or "Idle"
        print(f"  @{role:<12} | {info.get('role')} (Tools: {', '.join(info.get('tools', []))}) [Last: {last}]")
    print()

    print(f"Completed Tasks: {len(state.get('completed_tasks', []))}")


def cmd_spawn(args):
    state = load_hub_state()
    role = args.role.lstrip("@")
    if role not in state.get("agent_pool", {}):
        print(f"[-] Warning: @{role} not in standard pool, adding dynamically.")
        state.setdefault("agent_pool", {})[role] = {
            "role": f"Specialist agent for {role}",
            "tools": ["file", "terminal", "web"],
            "last_active": None,
            "skill_affinity": []
        }

    task_id = str(uuid.uuid4())
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    task = {
        "task_id": task_id,
        "role": role,
        "goal": args.goal,
        "spawned_at": now_iso,
        "status": "RUNNING",
        "output": None
    }
    state.setdefault("active_tasks", []).append(task)
    state["agent_pool"][role]["last_active"] = now_iso
    save_hub_state(state)

    print(f"[+] Task spawned successfully: {task_id}")
    print(f"    Assigned to: @{role}")
    print(f"    Goal:        {args.goal}")


def cmd_complete(args):
    state = load_hub_state()
    active = state.get("active_tasks", [])
    matched = None
    for idx, t in enumerate(active):
        if t["task_id"].startswith(args.task_id):
            matched = active.pop(idx)
            break

    if not matched:
        print(f"[-] Task ID {args.task_id} not found in active tasks.", file=sys.stderr)
        return

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    matched["status"] = "COMPLETED"
    matched["completed_at"] = now_iso
    matched["verdict"] = args.verdict
    state.setdefault("completed_tasks", []).append(matched)
    save_hub_state(state)
    print(f"[+] Task [{matched['task_id'][:8]}] marked COMPLETED.")
    print(f"    Verdict: {args.verdict}")


def main():
    parser = argparse.ArgumentParser(description="Hermes Hub Mode Fleet Commander CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Inspect active tasks and agent pool status")
    p_status.set_defaults(func=cmd_status)

    # spawn
    p_spawn = subparsers.add_parser("spawn", help="Spawn subagent task")
    p_spawn.add_argument("role", help="Specialist role (researcher, architect, coder, tester)")
    p_spawn.add_argument("goal", help="Target goal or engineering milestone")
    p_spawn.set_defaults(func=cmd_spawn)

    # complete
    p_comp = subparsers.add_parser("complete", help="Complete and archive active task")
    p_comp.add_argument("task_id", help="Task ID prefix or full UUID")
    p_comp.add_argument("--verdict", default="SUCCESS", help="Execution verdict or synthesis summary")
    p_comp.set_defaults(func=cmd_complete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
