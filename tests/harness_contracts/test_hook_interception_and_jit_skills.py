#!/usr/bin/env python3
"""
Phase-2 Contract Spike: Hook Interception, Capability Masks & JIT Skills (U2, U3, U4, U14)
==========================================================================================
Versioned contract test for Phase 2 (roadmap §3.4-B).

  - U2 Lifecycle Hooks: mutating tool payloads validated BEFORE disk;
    rejections carry exact <=5-line surgical slices (Trap-1 countermeasure);
    patches pass U12 AST Diff Size Gate; successful mutations produce
    shadow snapshots + trajectory events.
  - U3 Capability Masks: role-based allow/deny enforced at schema level.
  - U4 Bundled Plugin Standard: `.hermes/plugins/<name>/` packaging with
    plugin.yaml manifest, SKILL.md body, hooks, subagent profiles, and MCP;
    two-tier discovery with <=150 token Tier-1 overhead.
  - U14 Two-Tier JIT Skills: byte-static manifest index + on-demand
    skill content injection into active turn only.

100% offline & deterministic.
Run: pytest tests/harness_contracts/test_hook_interception_and_jit_skills.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from hermes_core.capability_masks import (  # noqa: E402
    DEFAULT_ROLE,
    ROLE_POLICIES,
    apply_to_agent,
    allowed_for,
    check_tool,
    mask_functions,
    resolve_role,
)
from hermes_core.hooks import LifecycleHookEngine, error_slice  # noqa: E402
from hermes_core.plugin_manifest import PluginManifest, load_manifest, estimate_tokens  # noqa: E402
from hermes_core.plugin_loader import (  # noqa: E402
    discover_plugins, tier1_summaries, summary_block_tokens,
    tier1_in_budget, activate_plugin, load_plugin_hooks,
)


@pytest.fixture()
def hook_engine():
    return LifecycleHookEngine()


@pytest.fixture()
def ws(tmp_path, monkeypatch):
    """Redirect the tools workspace root into an ephemeral tmp dir."""
    import hermes_core.tools as tools_mod
    monkeypatch.setattr(tools_mod, "DEFAULT_WORKSPACE", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# U3 — Subagent Capability Masks
# ---------------------------------------------------------------------------

class TestU3CapabilityMasks:
    def test_architect_cannot_write(self):
        for tool in ("write_file", "patch_file", "refactor_symbol"):
            ok, msg = check_tool("architect", tool)
            assert not ok and "CAPABILITY_MASK" in msg

    def test_coder_denied_test_runners(self):
        ok, msg = check_tool("coder", "run_test_suite")
        assert not ok and "denied" in msg
        assert check_tool("coder", "patch_file")[0]
        assert check_tool("coder", "execute_command")[0]

    def test_tester_denied_write_tools(self):
        for tool in ("write_file", "patch_file", "refactor_symbol"):
            assert not check_tool("tester", tool)[0]
        assert check_tool("tester", "run_test_suite")[0]

    def test_debugger_keeps_repair_surface(self):
        assert check_tool("debugger", "patch_file")[0]
        assert check_tool("debugger", "run_test_suite")[0]

    def test_unknown_role_defaults_read_only(self):
        assert resolve_role(object()) == DEFAULT_ROLE
        assert "write_file" not in allowed_for(DEFAULT_ROLE)

    def test_schema_level_masking_hides_tools_from_model(self):
        def read_file(): ...
        def write_file(): ...
        def run_test_suite(): ...

        class AgentLike:
            name = "@Architect"
            profile = None
            functions = [read_file, write_file, run_test_suite]

        agent, role = apply_to_agent(AgentLike())
        assert role == "architect"
        exposed = {f.__name__ for f in agent.functions}
        assert exposed == {"read_file"}  # write/grader never advertised

    def test_mask_functions_is_pure_filter(self):
        def patch_file(): ...
        def web_search(): ...
        out = mask_functions([patch_file, web_search], "tester")
        assert out == []

    def test_every_policy_superset_relationships_hold(self):
        # Architect strictly read-oriented; coder never graders; tester never mutators.
        assert "write_file" not in ROLE_POLICIES["architect"]
        assert "run_test_suite" not in ROLE_POLICIES["coder"]
        assert "write_file" not in ROLE_POLICIES["tester"]


# ---------------------------------------------------------------------------
# U2 — Event-Driven Lifecycle Hooks
# ---------------------------------------------------------------------------

class TestU2LifecycleHooks:
    def test_clean_write_passes(self, hook_engine):
        ok, msg = hook_engine.pre_tool_call(
            "coder", "write_file",
            {"filepath": "clean.py", "content": "def add(a, b):\n    return a + b\n"},
        )
        assert ok

    def test_python_syntax_error_rejected_with_exact_slice(self, hook_engine):
        bad = "def broken(:\n    pass\n\n\ndef sibling_ok():\n    return 7\n"
        ok, msg = hook_engine.pre_tool_call("coder", "write_file",
                                            {"filepath": "bad.py", "content": bad})
        assert not ok
        assert "[write_file] bad.py:1" in msg          # exact file:line pointer
        assert "1: def broken(:" in msg                 # numbered slice lines
        assert "Python SyntaxError" in msg

    def test_dangerous_js_pattern_rejected_at_line(self, hook_engine):
        js = "const a = 1;\nconst b = 2;\neval(userInput);\n"
        ok, msg = hook_engine.pre_tool_call("coder", "write_file",
                                            {"filepath": "app.js", "content": js})
        assert not ok
        assert "eval() call detected" in msg and "3:" in msg

    def test_patch_bloat_rejected_via_gate7(self, hook_engine):
        old_block = "def broken():\n    return x / 0"
        new_block = "\n".join([f"# filler {i}" for i in range(30)])
        ok, msg = hook_engine.pre_tool_call(
            "coder", "patch_file",
            {"filepath": "svc.py", "target_block": old_block, "replacement_block": new_block},
        )
        assert not ok and "PATCH BLOAT" in msg

    def test_sibling_obliteration_rejected(self, hook_engine):
        ok, msg = hook_engine.pre_tool_call(
            "coder", "patch_file",
            {"filepath": "svc.py",
             "target_block": "def target():\n    return 1\n\ndef keep_me():\n    return 2",
             "replacement_block": "def target():\n    return 42"},
        )
        assert not ok and "keep_me" in msg

    def test_simulated_patch_syntax_checked_before_disk(self, hook_engine, ws):
        target = ws / "mod.py"
        target.write_text("value = 1\nvalue = value + \n", encoding="utf-8")
        ok, msg = hook_engine.pre_tool_call(
            "coder", "patch_file",
            {"filepath": "mod.py",
             "target_block": "value = value + ",
             "replacement_block": "value = value +++"},
        )
        assert not ok
        assert "SyntaxError" in msg or "invalid syntax" in msg

    def test_valid_patch_passes(self, hook_engine, ws):
        target = ws / "mod.py"
        target.write_text("def broken():\n    return x / 0\n", encoding="utf-8")
        ok, msg = hook_engine.pre_tool_call(
            "coder", "patch_file",
            {"filepath": "mod.py",
             "target_block": "return x / 0",
             "replacement_block": "return 0 if x == 0 else x"},
        )
        assert ok

    def test_noop_and_empty_patches_rejected(self, hook_engine):
        for params in (
            {"filepath": "a.py", "target_block": "", "replacement_block": "x"},
            {"filepath": "a.py", "target_block": "x = 1", "replacement_block": "x = 1"},
        ):
            ok, msg = hook_engine.pre_tool_call("coder", "patch_file", params)
            assert not ok and "REJECTED" in msg

    def test_post_hook_shadows_successful_mutation(self, hook_engine, ws):
        target = ws / "artifact.html"
        target.write_text("<html><body>ok</body></html>", encoding="utf-8")
        event = hook_engine.post_tool_call("patch_file", {"filepath": "artifact.html"},
                                           "Successfully patched artifact.html.")
        snap = Path(event["shadow_snapshot"])
        assert event["ok"] is True
        assert snap.exists() and snap.is_relative_to(Path("/dev/shm"))
        assert json.loads((Path("/dev/shm/hermes_shadow") / "events.jsonl").read_text().splitlines()[-1])["tool"] == "patch_file"

    def test_failed_mutation_records_event_without_snapshot(self, hook_engine):
        event = hook_engine.post_tool_call("write_file", {"filepath": "x.py"}, "Error writing file.")
        assert event["ok"] is False and event["shadow_snapshot"] is None

    def test_error_slice_never_exceeds_5_lines(self):
        content = "\n".join(f"line{i}" for i in range(100))
        s = error_slice(content, 50)
        assert len(s.splitlines()) == 5 and "line49" in s


# ---------------------------------------------------------------------------
# U4 — Bundled Plugin Standard
# ---------------------------------------------------------------------------

class TestU4BundledPlugin:
    def test_manifest_dataclass_minimal_fields(self):
        m = PluginManifest(name="test", version="1.0.0", description="A test plugin.")
        assert m.name == "test"
        assert m.enabled is True
        assert m.hooks == {}

    def test_manifest_validate_rejects_empty_name(self):
        m = PluginManifest(name="", version="1.0.0", description="desc")
        with pytest.raises(ValueError, match="name"):
            m.validate()

    def test_manifest_validate_rejects_missing_version(self):
        m = PluginManifest(name="x", version="", description="desc")
        with pytest.raises(ValueError, match="version"):
            m.validate()

    def test_load_manifest_from_yaml(self, tmp_path):
        yml = tmp_path / "plugin.yaml"
        yml.write_text(
            "name: myplug\nversion: '2.0'\ndescription: Test plugin.\n"
            "tags: [test]\nenabled: true\n",
            encoding="utf-8",
        )
        m = load_manifest(yml)
        assert m.name == "myplug" and m.version == "2.0"
        assert "test" in m.tags

    def test_load_manifest_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_manifest(tmp_path / "nope.yaml")

    def test_summary_line_token_efficiency(self):
        m = PluginManifest(name="auth", version="1.0", description="OAuth2 login flow.", tags=["auth", "web"])
        line = m.summary_line()
        tokens = estimate_tokens(line)
        assert tokens <= 20, f"Summary line too verbose: {tokens} tokens"

    def test_tier1_summaries_for_multiple_plugins(self, tmp_path):
        plugins_root = tmp_path / "plugins"
        for i in range(5):
            d = plugins_root / f"plug{i}"
            d.mkdir(parents=True)
            (d / "plugin.yaml").write_text(
                f"name: plug{i}\nversion: '1.0'\ndescription: Plugin number {i}.\n",
                encoding="utf-8",
            )
        manifests = discover_plugins(plugins_root)
        assert len(manifests) == 5
        sums = tier1_summaries(manifests)
        assert all(isinstance(s, str) for s in sums)
        assert summary_block_tokens(sums) <= 150

    def test_disabled_plugins_excluded_from_discovery(self, tmp_path):
        plugins_root = tmp_path / "plugins"
        d = plugins_root / "off"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: off\nversion: '1.0'\ndescription: Disabled.\nenabled: false\n",
            encoding="utf-8",
        )
        assert len(discover_plugins(plugins_root)) == 0

    def test_tier1_token_budget_under_150(self, tmp_path):
        plugins_root = tmp_path / "plugins"
        for i in range(10):
            d = plugins_root / f"plugin{i}"
            d.mkdir(parents=True)
            (d / "plugin.yaml").write_text(
                f"name: plugin{i}\nversion: '1.0'\ndescription: Validation gate {i}.\n"
                f"tags: [tag{i}]\n",
                encoding="utf-8",
            )
        manifests = discover_plugins(plugins_root)
        assert len(manifests) == 10
        assert tier1_in_budget(manifests, budget=150)

    def test_tier2_activation_loads_skill_content(self, tmp_path):
        plugins_root = tmp_path / "plugins"
        d = plugins_root / "myplug"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: myplug\nversion: '1.0'\ndescription: Has skill.\n",
            encoding="utf-8",
        )
        (d / "SKILL.md").write_text("# My Skill\nDo stuff.", encoding="utf-8")
        result = activate_plugin(plugins_root, "myplug")
        assert result is not None
        assert "My Skill" in result["skill_content"]
        assert result["manifest"].name == "myplug"

    def test_tier2_activation_nonexistent_returns_none(self, tmp_path):
        assert activate_plugin(tmp_path / "plugins", "ghost") is None

    def test_tier2_activation_disabled_returns_none(self, tmp_path):
        d = tmp_path / "plugins" / "off"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: off\nversion: '1.0'\ndescription: Off.\nenabled: false\n",
            encoding="utf-8",
        )
        assert activate_plugin(tmp_path / "plugins", "off") is None

    def test_plugin_hooks_loadable(self, tmp_path):
        d = tmp_path / "plugins" / "hooked"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: hooked\nversion: '1.0'\ndescription: Has hook.\n"
            "hooks:\n  pre_commit: hooks/pre.py\n",
            encoding="utf-8",
        )
        hooks_dir = d / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "pre.py").write_text(
            "def run(ctx): return {'ok': True}", encoding="utf-8"
        )
        result = activate_plugin(tmp_path / "plugins", "hooked")
        assert "pre_commit" in result["hook_paths"]
        hook_fn = load_plugin_hooks(result["plugin_dir"], "hooks/pre.py")
        assert hook_fn is not None
        assert hook_fn({"filepath": "x.py"})["ok"] is True

    def test_plugin_manifest_to_dict_roundtrip(self):
        m = PluginManifest(
            name="rt", version="3.0", description="Roundtrip.",
            tags=["a"], hooks={"pre": "h.py"},
        )
        d = m.to_dict()
        assert d["name"] == "rt" and d["hooks"] == {"pre": "h.py"}

    def test_discover_plugins_empty_dir(self, tmp_path):
        assert discover_plugins(tmp_path / "no_plugins") == []

    def test_discover_plugins_skips_dirs_without_yaml(self, tmp_path):
        d = tmp_path / "plugins" / "broken"
        d.mkdir(parents=True)
        assert discover_plugins(tmp_path / "plugins") == []


# ---------------------------------------------------------------------------
# U14 — Two-Tier JIT Skills
# ---------------------------------------------------------------------------

class TestU14JITSkills:
    def test_skill_content_not_loaded_by_default(self, tmp_path):
        """Tier-1 discovery loads only manifest summaries, never SKILL.md bodies."""
        plugins_root = tmp_path / "plugins"
        d = plugins_root / "heavy"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: heavy\nversion: '1.0'\ndescription: Heavy skill.\n",
            encoding="utf-8",
        )
        (d / "SKILL.md").write_text("# Massive Skill\n" + "x" * 5000, encoding="utf-8")
        manifests = discover_plugins(plugins_root)
        summaries = tier1_summaries(manifests)
        full_text = "\n".join(summaries)
        assert "Massive Skill" not in full_text

    def test_skill_injected_only_on_activation(self, tmp_path):
        """Tier-2 activation loads full SKILL.md into active turn."""
        plugins_root = tmp_path / "plugins"
        d = plugins_root / "jit"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: jit\nversion: '1.0'\ndescription: JIT skill.\n",
            encoding="utf-8",
        )
        (d / "SKILL.md").write_text("# JIT Instructions\nDo this.", encoding="utf-8")
        result = activate_plugin(plugins_root, "jit")
        assert "JIT Instructions" in result["skill_content"]
        assert "Do this." in result["skill_content"]

    def test_tier1_token_overhead_under_120_tokens(self, tmp_path):
        """10 indexed skills must cost <=120 tokens in system prompt (roadmap §2.4)."""
        plugins_root = tmp_path / "plugins"
        for i in range(10):
            d = plugins_root / f"skill{i}"
            d.mkdir(parents=True)
            (d / "plugin.yaml").write_text(
                f"name: skill{i}\nversion: '1.0'\ndescription: Skill card {i}.\n",
                encoding="utf-8",
            )
        manifests = discover_plugins(plugins_root)
        sums = tier1_summaries(manifests)
        tokens = summary_block_tokens(sums)
        assert tokens <= 120, f"Tier-1 overhead {tokens} tokens exceeds 120 budget"

    def test_two_tier_isolation(self, tmp_path):
        """Tier-1 and Tier-2 are strictly separated — summary never includes body."""
        plugins_root = tmp_path / "plugins"
        d = plugins_root / "iso"
        d.mkdir(parents=True)
        (d / "plugin.yaml").write_text(
            "name: iso\nversion: '1.0'\ndescription: Isolation test.\n",
            encoding="utf-8",
        )
        (d / "SKILL.md").write_text(
            "# SECRET_INTERNALS\nprivileged_api_call()\n", encoding="utf-8"
        )
        manifests = discover_plugins(plugins_root)
        summary = tier1_summaries(manifests)[0]
        assert "SECRET_INTERNALS" not in summary
        assert "privileged_api_call" not in summary
        activated = activate_plugin(plugins_root, "iso")
        assert "SECRET_INTERNALS" in activated["skill_content"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
