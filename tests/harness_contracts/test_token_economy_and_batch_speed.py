#!/usr/bin/env python3
"""
Phase-1 Contract Spike: Token Economy & Batch Speed (U1, U9, U12, U15)
=====================================================================
Versioned contract test per the Living Test Matrix (roadmap §3.4 Dimension B):
every newly implemented capability MUST commit its matching contract test.

  - U1  Code Mode SDK: micro-surface, fail-fast, prose/fence extraction,
        sub-25s single-pass batch pipeline (read -> patch -> gate -> test).
  - U9  Minimal Preset: <350-token system prompt, ONLY patch+bash tools,
        explicit tool-availability declaration.
  - U12 Karpathy Surgical Laws: <60-token rule block + observer_gate
        AST Diff Size Gate (3x bloat limit, sibling-signature preservation).
  - U15 Codex Token Economy: >=6x differential compaction, ephemeral tool
        buffers (verdict + 5-line slice), immutable goal anchor survival.

100% offline & deterministic. No GPU, no llama-server, no network.
Run: pytest tests/harness_contracts/test_token_economy_and_batch_speed.py -q
"""

from __future__ import annotations

import ast
import importlib.util
import sys
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

try:
    from bin.extract_code_mode import extract_code_validated  # noqa: E402
except ImportError:
    from extract_code_mode import extract_code_validated  # noqa: E402
from hermes_core.presets import (  # noqa: E402
    MINIMAL_ALLOWED_TOOLS,
    MINIMAL_SYSTEM_PROMPT,
    build_minimal_agent,
    estimate_prompt_tokens,
    filter_functions,
)
from hermes_core.token_engine import (  # noqa: E402
    DifferentialStateCompactor,
    EphemeralToolBuffer,
    GoalAnchor,
)
from hermes_core.middleware import MythosCognitiveGovernor  # noqa: E402


# ---------------------------------------------------------------------------
# Loading shims for non-package modules (bin/, ws-ai/)
# ---------------------------------------------------------------------------

def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_hermes_sdk():
    p = ROOT / "sdk" / "hermes_sdk.py"
    if not p.exists():
        p = ROOT / "ws-ai" / "sdk" / "hermes_sdk.py"
    return _load("hermes_sdk", p)


def load_observer_gate():
    return _load("observer_gate_mod", ROOT / "bin" / "observer_gate.py")


# ---------------------------------------------------------------------------
# U1 — Code Mode SDK
# ---------------------------------------------------------------------------

class TestU1CodeModeSDK:
    def test_micro_surface_max_5_methods(self):
        """Trap-3 countermeasure: SDK surface is capped at the 5 flat methods."""
        sdk_mod = load_hermes_sdk()
        public = [m for m in dir(sdk_mod.HermesSDK) if not m.startswith("_")]
        allowed = {"read_range", "search", "apply_patch", "run_observer_gate", "run_test"}
        assert set(public) <= allowed, f"SDK surface bloat: {set(public) - allowed}"

    def test_extractor_corpus_20_mixed_outputs(self):
        """Trap-1 verification: 20 raw model outputs w/ prose+fences -> 100% AST-clean."""
        corpus = [
            'Here is the script:\n```python\nx = {i: i * 2 for i in range(3)}\n```\nLet me know if you need changes!',
            "Sure!\n```python\nimport os\nprint(os.sep)\n```",
            "```python\ndef f(a):\n    return a + 1\n```\n`note the fence escapes above`",
            "<think>reasoning</think>\n```py\nfor i in range(3):\n    print(i)\n```",
            'I will now provide the code:\n~~~python\nclass A:\n    pass\n~~~\nThis script builds the class.',
            "```python\ns = \"```not a fence``\"\nprint(s)\n```",
            "Below is the patch script:\n```python\nfrom pathlib import Path\np = Path('x')\n```",
            "```python\nimport json\nd = {'a': [1, 2, 3]}\n```",
            "Note:\n```python\nlambda_fn = lambda v: v * 2\n```",
            "Here's what I found:\n```python\ntry:\n    raise ValueError('x')\nexcept ValueError:\n    pass\n```",
            "Step 1 done. Now run this:\n```python\nnums = list(range(10))\nassert len(nums) == 10\n```",
            "```python\nwith open('/dev/null') as f:\n    data = f.read()\n```",
            "The script below does it:\n```python\nresult = sum(i*i for i in range(5))\n```",
            "```python\nmatch = {'k': None}\nif match['k'] is None:\n    match['k'] = 0\n```",
            "Output:\n```python\nasync def go():\n    return 42\n```",
            "Sure, here you go:\n```python\na, b = 1, 2\na, b = b, a\n```",
            "```python\nimport re\nrx = re.compile(r'\\d+')\n```",
            "This program prints:\n```python\nprint('hello world')\n```",
            "```python\nxs = [n for n in range(20) if n % 2 == 0]\n```",
            "Final answer:\n```python\ndone = True\n```",
        ]
        parsed = 0
        for raw in corpus:
            code = extract_code_validated(raw)  # raises on any pollution
            ast.parse(code)
            parsed += 1
        assert parsed == len(corpus)

    def test_fail_fast_patch_aborts_with_slice(self):
        """Trap-2 verification: blind execution impossible; exact error slice emitted."""
        sdk_mod = load_hermes_sdk()
        sdk = sdk_mod.HermesSDK()
        with pytest.raises(sdk_mod.HermesSDKError) as ei:
            sdk.apply_patch("definitely_missing_file.py", "old", "new")
        assert ei.value.method == "patch"

    def test_batch_pipeline_under_25s(self):
        """Roadmap 1.1: read -> patch -> gate -> test collapses into one sub-25s pass."""
        sdk_mod = load_hermes_sdk()
        sdk = sdk_mod.HermesSDK()
        t0 = time.time()

        art = Path("/dev/shm/hermes_contract/code_mode_artifact.html")
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("<html><body><h1>probe</h1></body></html>", encoding="utf-8")

        import os
        os.environ["HERMES_SDK_WORKSPACE"] = "/dev/shm/hermes_contract"
        rel = "code_mode_artifact.html"
        head = sdk.read_range(rel, 1, 1)
        assert "probe" in head
        sdk.apply_patch(rel, "<h1>probe</h1>", "<h1>patched-probe</h1>")
        verdict = sdk.run_observer_gate(rel)
        assert verdict["passed"] is True
        # Prove execution lands INSIDE the ws-ai distrobox container toolchain.
        res = sdk.run_test('test "$CONTAINER_ID" = "ws-ai" && echo container-ok')
        assert res["passed"] is True and "container-ok" in res["output"]

        elapsed = time.time() - t0
        assert elapsed < 25.0, f"batch pass took {elapsed:.1f}s (budget 25s)"


# ---------------------------------------------------------------------------
# U9 — Minimal Mode Benchmark Preset
# ---------------------------------------------------------------------------

class TestU9MinimalPreset:
    def test_system_prompt_under_350_tokens(self):
        assert estimate_prompt_tokens(MINIMAL_SYSTEM_PROMPT) < 350

    def test_tool_availability_declaration_present(self):
        """Trap-1 countermeasure: explicit runtime tool declaration."""
        assert "ONLY 'patch_file' and 'execute_command' exist in this runtime." in MINIMAL_SYSTEM_PROMPT
        assert "All other tools are disabled." in MINIMAL_SYSTEM_PROMPT

    def test_only_patch_and_bash_survive_filtering(self):
        def patch_file(): ...
        def execute_command(): ...
        def web_search(): ...
        def read_symbol(): ...
        def search_web(): ...

        kept = filter_functions([patch_file, execute_command, web_search, read_symbol, search_web])
        assert {f.__name__ for f in kept} == set(MINIMAL_ALLOWED_TOOLS)

    def test_build_minimal_agent_strips_tools_and_sets_prompt(self):
        def patch_file(): ...
        def execute_command(): ...
        def search_web(): ...

        agent = types.SimpleNamespace(
            functions=[patch_file, execute_command, search_web],
            instructions="huge original prompt",
            tool_choice="auto",
        )
        patched = build_minimal_agent(agent, task_prompt="fix the bug")
        assert {f.__name__ for f in patched.functions} == set(MINIMAL_ALLOWED_TOOLS)
        assert MINIMAL_SYSTEM_PROMPT in patched.instructions
        assert "fix the bug" in patched.instructions
        assert patched.tool_choice is None

    def test_engine_rejects_unknown_preset(self):
        pytest.importorskip("openai")
        from hermes_core.swarm_engine import HermesOrchestrator
        orch = HermesOrchestrator(base_url="http://127.0.0.1:1/v1")  # never contacted
        with pytest.raises(ValueError, match="Unknown preset"):
            orch.run(agent=None, messages=[], preset="turbo")


# ---------------------------------------------------------------------------
# U12 — Karpathy Surgical Code Guardrails
# ---------------------------------------------------------------------------

class TestU12KarpathyGuardrails:
    def test_law_block_under_60_tokens(self):
        """Trap-2 countermeasure: compact rule block avoids attention diffusion."""
        block = MythosCognitiveGovernor.KARPATHY_SURGICAL_LAWS
        assert len(block) // 4 < 60

    def test_laws_embedded_for_coder_only(self):
        wrapped_coder = MythosCognitiveGovernor.wrap_instructions("base", coder=True)
        wrapped_other = MythosCognitiveGovernor.wrap_instructions("base", coder=False)
        assert "[KARPATHY LAWS]" in wrapped_coder
        assert "[KARPATHY LAWS]" not in wrapped_other

    def test_diff_size_gate_accepts_surgical_patch(self):
        og = load_observer_gate()
        old_block = "def broken():\n    return x / 0"
        new_block = "def broken():\n    if x == 0:\n        return 0\n    return x"
        verdict = og.check_ast_diff_size(old_block, new_block)
        assert verdict["passed"] is True

    def test_diff_size_gate_rejects_bloat(self):
        """Over-eager refactoring: replacement >3x minimal necessary size."""
        og = load_observer_gate()
        old_block = "def broken():\n    return x / 0"
        new_block = "\n".join(
            [f"# speculative line {i}" for i in range(20)]
            + ["def helper_a():", "    pass", "def helper_b():", "    pass"]
        )
        verdict = og.check_ast_diff_size(old_block, new_block)
        assert verdict["passed"] is False
        assert "PATCH BLOAT" in verdict["detail"]

    def test_diff_size_gate_flags_sibling_obliteration(self):
        """Trap-1 verification: sibling function signatures must survive patches."""
        og = load_observer_gate()
        old_block = "def target():\n    return 1\n\ndef sibling_keep_me():\n    return 2"
        new_block = "def target():\n    return 42"
        verdict = og.check_ast_diff_size(old_block, new_block)
        assert verdict["passed"] is False
        assert "sibling_keep_me" in verdict["detail"]

    def test_gate7_integrated_in_run_all_gates(self):
        og = load_observer_gate()
        art = Path("/dev/shm/hermes_contract/gate7_probe.html")
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("<html><body>g</body></html>", encoding="utf-8")
        result = og.run_all_gates(str(art), diff_old="def a():\n    pass", diff_new="\n".join([f"x{i} = {i}" for i in range(30)]))
        names = [c["name"] for c in result["checks"]]
        assert "ast_diff_size_gate" in names
        assert result["passed"] is False


# ---------------------------------------------------------------------------
# U15 — Codex 6x Token Economy State Engine
# ---------------------------------------------------------------------------

def _bloated_history(turns: int = 18) -> list:
    hist = [{
        "role": "user",
        "content": "<|GOAL_ANCHOR|>\nGOAL: fix solver\nTARGET: src/solver.py\n<|GOAL_ANCHOR|>",
    }]
    big_dump = "line of compiler noise padded to simulate raw file text output\n" * 60
    for i in range(turns):
        hist.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": f"c{i}", "type": "function",
                            "function": {"name": "read_file" if i % 3 else "patch_file", "arguments": "{}"}}],
        })
        content = big_dump
        if i >= turns - 5:
            content = "PASS (exit=0). Successfully patched src/solver.py."
        elif i % 6 == 0:
            content = "Successfully patched src/solver.py."
        hist.append({"role": "tool", "tool_call_id": f"c{i}", "name": "t", "content": content})
    hist.append({"role": "assistant", "content": "VERIFIED"})
    return hist


class TestU15TokenEconomy:
    def test_compaction_achieves_6x_reduction(self):
        baseline = _bloated_history()
        compactor = DifferentialStateCompactor(keep_recent=4)
        compacted = compactor.compact(baseline)
        ratio = DifferentialStateCompactor.reduction_ratio(baseline, compacted)
        assert len(compacted) < len(baseline)
        assert ratio >= 6.0, f"reduction only {ratio:.1f}x (need >=6x)"

    def test_goal_anchor_survives_all_prunings(self):
        """Trap-1 countermeasure: immutable anchor pinned across compaction."""
        baseline = _bloated_history(30)
        compacted = DifferentialStateCompactor(keep_recent=4).compact(baseline)
        assert "<|GOAL_ANCHOR|>" in compacted[0]["content"]
        assert compacted[0] == baseline[0]

    def test_ephemeral_buffer_keeps_full_log_returns_slice(self):
        with EphemeralToolBuffer("pytest_probe", keep_tail_lines=5) as buf:
            buf.write("\n".join(f"noise line {i}" for i in range(50)))
        summary = buf.finalize(exit_code=1)
        lines = [l for l in summary.splitlines() if l.strip() and not l.startswith("Full log")]
        body_lines = [l for l in lines if l.startswith("noise")]
        assert len(body_lines) == 5
        assert buf.buffer_path.exists() and buf.buffer_path.is_relative_to(Path("/dev/shm"))
        full = buf.buffer_path.read_text().splitlines()
        assert len(full) == 50  # nothing lost on disk
        buf.buffer_path.unlink(missing_ok=True)

    def test_ephemeral_buffer_pass_verdict_is_single_line(self):
        with EphemeralToolBuffer("pass_probe") as buf:
            buf.write("lots of streaming output\n" * 100)
        summary = buf.finalize(exit_code=0)
        assert summary.startswith("[pass_probe] PASS") and str(buf.buffer_path) in summary

    def test_goal_anchor_round_trip(self, tmp_path):
        plan = tmp_path / ".hermes" / "plan.json"
        GoalAnchor("ship phase 1", "ws-ai/sdk/hermes_sdk.py", ["no oracle leaks", "btrfs zero-wear"]).save(plan)
        loaded = GoalAnchor.load(plan)
        block = loaded.format_prompt_block()
        assert loaded.goal == "ship phase 1"
        assert loaded.current_target == "ws-ai/sdk/hermes_sdk.py"
        assert len(block.splitlines()) <= 10

    def test_short_history_is_never_touched(self):
        hist = [{"role": "user", "content": "task"}]
        out = DifferentialStateCompactor().compact(hist)
        assert out == hist


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
