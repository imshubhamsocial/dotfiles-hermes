#!/usr/bin/env python3
"""
CLI entry point for Speculative Programmatic Tool Calling (sPTC / Milestone U79)
Usage:
  python3 bin/speculative_tool_executor.py --demo
"""
import time
from hermes_core.speculative_executor import create_speculative_executor


def main():
    executor = create_speculative_executor()

    # Register mock pure search tool
    def mock_web_search(query: str):
        time.sleep(0.05)  # Simulate network latency
        return f"Grounded results for '{query}'"

    executor.register_tool_handler("web_search", mock_web_search)

    stream_sample = """
    Let me search for the current Python specification.
    web_search(query="python dataclasses specification")
    Then I will formulate the blueprint.
    """

    print("[sPTC] Observing streaming text delta...")
    launched = executor.observe_stream_delta(stream_sample)
    print(f"[sPTC] Speculatively launched {len(launched)} tool promise(s): {launched}")

    print("[sPTC] Main execution reaches tool call point...")
    res, speculated = executor.claim_or_execute("web_search", {"query": "python dataclasses specification"})
    print(f"[sPTC] Result: '{res}' | Claimed from Speculation: {speculated}")


if __name__ == "__main__":
    main()
