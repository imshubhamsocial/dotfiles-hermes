#!/usr/bin/env python3
"""
CLI entry point for 4-Tier Skill Hierarchy Router (Milestone U63)
Usage:
  python3 bin/skill_router.py "<prompt>" [--max-tokens 200] [--json]
"""
import argparse
import json
import sys
from hermes_core.skill_router import create_skill_router


def main():
    parser = argparse.ArgumentParser(description="Hermes 4-Tier Skill Router")
    parser.add_argument("prompt", help="Prompt or task to route skills for")
    parser.add_argument("--max-tokens", type=int, default=200, help="Maximum injected tokens")
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")

    args = parser.parse_args()
    router = create_skill_router()
    result = router.route(args.prompt, max_tokens=args.max_tokens)

    if args.json:
        out = {
            "matched": result.matched,
            "skill_name": result.skill.name if result.skill else None,
            "tier": result.skill.tier if result.skill else None,
            "score": result.score,
            "token_count": result.token_count,
            "injected_prompt": result.injected_prompt,
        }
        print(json.dumps(out, indent=2))
    else:
        if result.matched:
            print(result.injected_prompt)
        else:
            print("No matching skill found in 4-tier catalog.")


if __name__ == "__main__":
    main()
