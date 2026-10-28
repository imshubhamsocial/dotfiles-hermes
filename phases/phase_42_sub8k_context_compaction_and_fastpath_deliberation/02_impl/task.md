# Phase 42 Implementation Task

1. Verify `compact_messages` inside `.hermes/mcp_ephemeral_bridge.py` strips historical `<deliberation>` blocks and truncates oversized tool outputs.  
2. Benchmark a multi-turn tool-calling round-trip against Port 1934 -> Port 8138 and assert wall-clock turn latency < 10.0 seconds and prompt characters < 8,000.
