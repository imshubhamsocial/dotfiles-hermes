# HERMES ROADMAP 3: AUTONOMOUS SINGLE-BINARY TEST PLAN SUITE
## Definitive Production Validation Framework for Standalone Hermes Agent OS

> **Document Suite ID**: `Desktop/hermes/roadmap3/`  
> **Target System**: Hermes Single-Binary Autonomous Agent (`hermes <prompt>` / `hermes -z --yolo "<prompt>"`)  
> **Foundation**: Roadmap 1 (U1–U20 Living Harness Primitives) & Roadmap 2 (U21–U35 Autonomous Agent OS & Metacognitive Loop)  
> **Reference Standard**: Google Antigravity CLI, OpenAI Codex CLI (`@openai/codex`), Anthropic Claude Code (`@anthropic-ai/claude-code`)  
> **Hardware Envelope**: Single Local GPU (NVIDIA RTX 3050 Laptop / 4GB VRAM / CC 8.6) + `ws-ai` Distrobox Substrate  
> **Inference Engine**: Local 4B SLMs (Gemma-4-E4B-it / Qwen-3.6-4B-it) with MTP Speculative Decoding on `:8138` + OmniRoute on `:20128`

---

## 🗺️ Master Sitemap & Document Navigation

This test plan suite contains 7 authoritative documents detailing the exact methodology, test cases, telemetry probes, regression batteries, and parity benchmarks required to validate Hermes as a standalone, autonomous coding agent.

| Document | Purpose | Key Focus Areas |
| :--- | :--- | :--- |
| [`00_MASTER_HERMES_AUTONOMOUS_TEST_PLAN.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/00_MASTER_HERMES_AUTONOMOUS_TEST_PLAN.md) | **Master Executive Overview & Architecture** | Transition from `multibot.py` to single binary; 6-pillar test framework; 100-point Production Readiness Index (PRI). |
| [`01_SINGLE_BINARY_INVOCATION_AND_TOOL_CALLING_MATRIX.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/01_SINGLE_BINARY_INVOCATION_AND_TOOL_CALLING_MATRIX.md) | **CLI Invocation & Tool Calling Matrix** | `hermes <prompt>`, dynamic schema reflection, role-based tool pruning, `bwrap` sandboxing, and Code Mode SDK. |
| [`02_HIERARCHICAL_PROMPT_DECOMPOSITION_AND_DAG_TRACKING_PLAN.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/02_HIERARCHICAL_PROMPT_DECOMPOSITION_AND_DAG_TRACKING_PLAN.md) | **Prompt Decomposition & State Tracking** | Decomposing monolithic prompts into SQLite WAL `TaskDAG` milestones, AST symbol graph querying, and sub-350 tok scratchpads. |
| [`03_FAILURE_MODES_REGRESSIONS_AND_EDGE_CASE_TEST_SUITE.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/03_FAILURE_MODES_REGRESSIONS_AND_EDGE_CASE_TEST_SUITE.md) | **Failure Modes & Regression Battery** | Duplicate declaration patch trap, context compaction freezes, tool loop locks, silent drops, and Observer Gate pre-commits. |
| [`04_ANTIGRAVITY_CODEX_CLAUDE_PARITY_BENCHMARK_SPEC.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/04_ANTIGRAVITY_CODEX_CLAUDE_PARITY_BENCHMARK_SPEC.md) | **Frontier Agent Parity Benchmark** | Side-by-side comparison against Antigravity CLI, OpenAI Codex, and Claude Code across 10 standardized engineering tasks. |
| [`05_HARDWARE_CALIBRATED_TEST_RUNNERS_AND_AUTOMATION_HARNESS.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/05_HARDWARE_CALIBRATED_TEST_RUNNERS_AND_AUTOMATION_HARNESS.md) | **Test Runners & Telemetry Probes** | Automated test harnesses, sub-50ms system auditor, GPU VRAM guards (<3.8 GB), and deterministic test arbiters. |
| [`06_PRODUCTION_GAP_ANALYSIS_AND_ROADMAP3_RECOMMENDATIONS.md`](file:///var/home/imshubhamsocial/Desktop/hermes/roadmap3/06_PRODUCTION_GAP_ANALYSIS_AND_ROADMAP3_RECOMMENDATIONS.md) | **Production Gap Analysis & Roadmap 3 Specs** | What is working today vs remaining production gaps (multi-file context sieve, branch swapping, CLI unifier `U36`–`U45`). |

---

## 🚀 Quickstart & Verification Commands

```bash
# 1. Verify underlying Agent OS harness integrity (235 tests across U1–U35)
python3 bin/verify_harness_integrity.py

# 2. Check local inference engine & hardware health
hermes doctor
# or: python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8138/health').read().decode())"

# 3. Test single-binary one-shot autonomous execution
~/.local/bin/hermes --yolo -z "Create a Python vector math module in /dev/shm/vec.py with 3D dot/cross product and pytest suite"

# 4. View live 7-layer Agent OS telemetry
hermes status

# 5. Run contract test suite
python3 -m pytest tests/harness_contracts/ -q
```
