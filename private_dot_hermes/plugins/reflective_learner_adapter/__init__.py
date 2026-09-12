"""
Hermes Plugin: reflective_learner_adapter
=========================================
Google ADK 2.0 TaskDAG, Dreaming, Temporal Memory & NoRA Online Adaptation Buffer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home
from .experience_store import (
    EpisodeRecord,
    ExperienceStore,
    create_experience_store,
)
from .hooks.on_session_end import on_session_end
from .trajectory import (
    TrajectoryRecorder,
    active_path,
    events_to_otel_spans,
    flush_to_milestone_disk,
    get_trajectory_tracer,
    init_observability,
    load_events,
    verify_chain,
)


def get_nora_status() -> Dict[str, Any]:
    """Inspects the NoRA online adaptation training buffer."""
    buf_dir = get_hermes_home() / "memories" / "training_buffer"
    if not buf_dir.exists() and (get_hermes_home() / "training_buffer").exists():
        buf_dir = get_hermes_home() / "training_buffer"
    buf_file = buf_dir / "samples.jsonl"
    if not buf_file.exists():
        return {
            "total_samples": 0,
            "verified_samples": 0,
            "pending_adaptation": 0,
            "buffer_path": str(buf_file),
            "recent_samples": [],
        }

    lines = [l.strip() for l in buf_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    samples = []
    for line in lines:
        try:
            samples.append(json.loads(line))
        except Exception:
            pass

    verified = sum(1 for s in samples if s.get("verified", False))
    return {
        "total_samples": len(samples),
        "verified_samples": verified,
        "pending_adaptation": verified,
        "buffer_path": str(buf_file),
        "recent_samples": samples[-5:],
    }


def register(ctx=None):
    """Registers plugin reflective_learner_adapter into Hermes runtime."""
    if not ctx:
        return True

    # 1. Lifecycle Hook: on_session_end
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_end", on_session_end)

    # 2. Native CLI command: hermes nora status
    if hasattr(ctx, "register_cli_command"):
        def setup_nora(parser):
            parser.description = "Inspect NoRA (Normalized Low-Rank Adaptation) online adaptation pipeline"
            subparsers = parser.add_subparsers(dest="subcommand", help="NoRA actions")

            status_p = subparsers.add_parser("status", help="View training buffer and adaptation status")
            status_p.add_argument("--json", action="store_true", help="Output as JSON")

        def handle_nora(args):
            subcmd = getattr(args, "subcommand", None) or "status"
            if subcmd == "status":
                st = get_nora_status()
                if getattr(args, "json", False):
                    print(json.dumps(st, indent=2))
                else:
                    print("NoRA Online Adaptation Pipeline Status:")
                    print("  Stage 1 (Signal Capture): ACTIVE")
                    print("  Stage 2-4 (Hot-Swap):     Awaiting llama.cpp LoRA hot-reload API")
                    print(f"  Buffer File:              {st['buffer_path']}")
                    print(f"  Total Ingested Trajectories: {st['total_samples']}")
                    print(f"  Verified Samples (Ready):    {st['verified_samples']}")
                    if st["recent_samples"]:
                        print("  Recent Ingested Sessions:")
                        for s in st["recent_samples"]:
                            mark = "✓" if s.get("verified") else "✗"
                            print(f"    - [{mark}] {s.get('session_id', 'unknown')[:12]}: {s.get('title', 'N/A')}")
                return 0
            return 0

        ctx.register_cli_command("nora", "Inspect NoRA online adaptation status", setup_nora, handle_nora)

    # 3. Native Slash command: /nora
    if hasattr(ctx, "register_command"):
        def slash_nora(raw_args: str) -> str:
            st = get_nora_status()
            lines = [
                "**NoRA Online Adaptation Status**",
                "- **Stage 1 (Signal Capture)**: `ACTIVE`",
                "- **Stage 2-4 (Gradient & Hot-Swap)**: `Planned (llama.cpp LoRA reload blocker)`",
                f"- **Total Captured Trajectories**: `{st['total_samples']}`",
                f"- **Verified Samples (Ready)**: `{st['verified_samples']}`",
            ]
            return "\n".join(lines)

        ctx.register_command("nora", slash_nora, "Inspect NoRA adaptation pipeline status", "")

    return True


__all__ = [
    "EpisodeRecord",
    "ExperienceStore",
    "create_experience_store",
    "TrajectoryRecorder",
    "init_observability",
    "get_trajectory_tracer",
    "active_path",
    "load_events",
    "verify_chain",
    "events_to_otel_spans",
    "flush_to_milestone_disk",
    "on_session_end",
    "get_nora_status",
    "register",
]
