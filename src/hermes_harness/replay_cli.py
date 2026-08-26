"""Replay CLI entrypoint."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

from hermes_core.replay import replay_trajectory
import json


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("trajectory_file", type=Path)
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--json", type=Path, default=Path("/dev/shm/replay_report.json"))
    args = ap.parse_args()

    rep = replay_trajectory(args.trajectory_file, max_steps=args.max_steps)
    args.json.write_text(json.dumps({
        "summary": rep.summary(),
        "steps": [vars(s) for s in rep.steps]
    }, indent=2))

    print(f"Replayed: {rep.replayed_steps} steps, {rep.drifted_steps} drift, match={rep.deterministic_match}")
    print(f"Report: {args.json}")
    sys.exit(0 if rep.deterministic_match else 1)


if __name__ == "__main__":
    main()