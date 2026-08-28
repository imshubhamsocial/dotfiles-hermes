#!/usr/bin/env python3
"""
CLI entry point for Hermes Web Grounding Layer (Milestone U62)
Usage:
  python3 bin/web_grounding.py "<query>" [--policy always|before_plan|before_code|on_error|never] [--json]
"""
import argparse
import json
import sys
from hermes_core.web_grounding import create_web_grounding_engine


def main():
    parser = argparse.ArgumentParser(description="Hermes Token-Efficient Web Grounding")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--policy", default="always", choices=["always", "before_plan", "before_code", "on_error", "never"])
    parser.add_argument("--context", default=None, help="Trigger context")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")

    args = parser.parse_args()
    engine = create_web_grounding_engine()
    result = engine.ground(
        query=args.query,
        policy=args.policy,
        trigger_context=args.context,
        max_results=args.max_results,
        max_tokens=args.max_tokens,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.markdown_context:
            print(result.markdown_context)
        else:
            print(f"Grounding skipped (policy={args.policy}, executed={result.executed})")


if __name__ == "__main__":
    main()
