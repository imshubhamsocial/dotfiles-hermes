"""
Hermes CLI — Production Entrypoint
==================================
Main `hermes` command with all subcommands.
"""

import os
import sys
import json
import subprocess
import click
from pathlib import Path

# Ensure we can import hermes_core whether installed or in dev
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from hermes_harness.paths import get_paths, HermesPaths


def _ensure_venv_active(paths: HermesPaths) -> None:
    """Ensure the production venv is on sys.path for imports."""
    venv_site = paths.install_prefix / ".venv" / "lib" / "python3.12" / "site-packages"
    if venv_site.exists() and str(venv_site) not in sys.path:
        sys.path.insert(0, str(venv_site))


def _run_solo(prompt_text: str, profile_name: str, model: str, base_url: str,
              max_turns: int, verbose: bool) -> None:
    """Execute a single-shot task with the configured profile."""
    from hermes_core.swarm_engine import HermesOrchestrator
    from hermes_core.swarm_system import architect_agent, coder_agent, tester_agent, researcher_agent

    profile_map = {
        "architect": architect_agent,
        "coder": coder_agent,
        "tester": tester_agent,
        "researcher": researcher_agent,
    }

    agent = profile_map.get(profile_name)
    if not agent:
        click.echo(f"Error: unknown profile '{profile_name}'", err=True)
        sys.exit(1)

    agent = agent.model_copy(update={"model": model, "temperature": 1.0})
    orch = HermesOrchestrator(base_url=base_url, api_key="local")

    if verbose:
        click.echo(f"🤖 Profile: {profile_name} | Model: {model} | Server: {base_url}")

    resp = orch.run(agent, [{"role": "user", "content": prompt_text}],
                    max_turns=max_turns, verbose=verbose)

    if verbose:
        click.echo(f"\n✅ Completed in {len(resp.messages) if hasattr(resp, 'messages') else 'N/A'} turns")

    # Print final response if available
    if hasattr(resp, "messages") and resp.messages:
        last = resp.messages[-1]
        if last.get("role") == "assistant":
            click.echo(last.get("content", ""))


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("prompt", nargs=-1, required=False)
@click.option("--profile", "-p", default="coder", help="Profile to use (architect, coder, tester, researcher)")
@click.option("--model", "-m", default=None, help="Model override")
@click.option("--base-url", "-u", default=None, help="API base URL override")
@click.option("--max-turns", default=3, help="Maximum conversation turns")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(prompt, profile, model, base_url, max_turns, verbose):
    """Execute a single-shot task. Default mode when no subcommand given."""
    paths = get_paths()
    _ensure_venv_active(paths)

    model = model or paths.default_model
    base_url = base_url or paths.default_base_url

    if prompt:
        prompt_text = " ".join(prompt)
    else:
        click.echo("Error: provide prompt as arguments", err=True)
        sys.exit(1)

    _run_solo(prompt_text, profile, model, base_url, max_turns, verbose)


@click.command()
def exam():
    """Run the final integration exam (all capabilities live)."""
    # Import the exam module directly using the full path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_final_integration_exam",
        "/opt/hermes-harness/bin/run_final_integration_exam.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.argv = ["hermes-exam"]
    sys.exit(module.main())


@click.command()
@click.argument("trajectory_file", type=click.Path(exists=True))
@click.option("--max-steps", type=int, default=None)
@click.option("--json", "json_out", type=click.Path(), default="/dev/shm/replay_report.json")
def replay(trajectory_file, max_steps, json_out):
    """Replay a trajectory against current rules (U7)."""
    from hermes_core.replay import replay_trajectory
    import json

    rep = replay_trajectory(trajectory_file, max_steps=max_steps)
    Path(json_out).write_text(json.dumps({
        "summary": rep.summary(),
        "steps": [vars(s) for s in rep.steps]
    }, indent=2))

    click.echo(f"Replayed: {rep.replayed_steps} steps, {rep.drifted_steps} drift, match={rep.deterministic_match}")
    click.echo(f"Report: {json_out}")
    if not rep.deterministic_match:
        sys.exit(1)


@click.command()
@click.argument("trajectory_file", type=click.Path(exists=True))
def lineage(trajectory_file):
    """Run supervisory scan on trajectory (U17)."""
    from hermes_core.lineage import supervisory_scan

    ivs = supervisory_scan(trajectory_file)
    for iv in ivs:
        click.echo(f"{iv.kind} @seq={iv.at_seq}: {iv.reason}")
    if not ivs:
        click.echo("No interventions — healthy trajectory")


@click.command()
@click.argument("skill_name")
@click.option("--generations", default=5)
def evolve(skill_name, generations):
    """Run self-evolution on a skill (U18)."""
    click.echo(f"Evolving skill '{skill_name}' for {generations} generations...")
    click.echo("Not yet implemented in CLI — use Python API directly")


@click.command()
def doctor():
    """Health check: llama-server, VRAM, profiles, skills."""
    paths = get_paths()
    _ensure_venv_active(paths)

    click.echo("🏥 HERMES DOCTOR")
    click.echo("-" * 40)

    # 1. llama-server health
    import urllib.request
    try:
        with urllib.request.urlopen(f"{paths.default_base_url.replace('/v1', '')}/health", timeout=3) as r:
            health = json.loads(r.read())
            click.echo(f"  llama-server: {'✅' if health.get('status') == 'ok' else '❌'} {health}")
    except Exception as e:
        click.echo(f"  llama-server: ❌ {e}")

    # 2. VRAM
    try:
        vram = int(subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True).stdout.strip().splitlines()[0])
        budget = 4812
        click.echo(f"  VRAM: {vram} MiB / {budget} MiB {'✅' if vram <= budget else '❌'}")
    except Exception as e:
        click.echo(f"  VRAM: ❌ {e}")

    # 3. Profiles
    profiles = list(paths.profiles_dir.glob("*/config.yaml")) if paths.profiles_dir.exists() else []
    click.echo(f"  Profiles: {len(profiles)} found ✅" if profiles else "  Profiles: ❌ none found")

    # 4. Skills
    skills = list(paths.skills_dir.iterdir()) if paths.skills_dir.exists() else []
    click.echo(f"  Skills: {len(skills)} linked ✅" if skills else "  Skills: ⚠️ none linked")

    # 5. Paths sanity
    click.echo(f"\n  Config dir: {paths.config_dir}")
    click.echo(f"  Install prefix: {paths.install_prefix}")
    click.echo(f"  Trajectory: {paths.trajectory_path}")
    click.echo(f"  Lineage: {paths.lineage_path}")


@click.command()
@click.argument("target_path", default=".", type=click.Path(exists=True))
@click.option("--index/--no-index", default=True, help="Index AST symbol knowledge graph")
def onboard(target_path, index):
    """Ingest & onboard a repository (U28)."""
    from hermes_core.repo_onboard import create_repo_onboarder
    onboarder = create_repo_onboarder(workspace_root=target_path)
    info = onboarder.onboard(target_path, index_symbols=index)
    summary = onboarder.generate_onboarding_summary(info)
    click.echo(summary)


@click.command()
@click.argument("query")
@click.option("--max-pages", default=3, help="Max web pages to ingest")
def search(query, max_pages):
    """Fast web research & token-bounded markdown synthesis (U23)."""
    from hermes_core.fast_research import create_fast_research_engine
    engine = create_fast_research_engine()
    res = engine.research(query, max_pages=max_pages)
    click.echo(res.summary_markdown)


@click.command()
@click.argument("binary_path", type=click.Path(exists=True))
def sec_audit(binary_path):
    """Security & mitigation audit on an ELF binary (U24)."""
    from hermes_core.security_ctf import SecurityCTFToolsuite
    data = Path(binary_path).read_bytes()
    tool = SecurityCTFToolsuite()
    info = tool.analyze_binary(data)
    click.echo(f"🛡️  Binary Security Audit: {Path(binary_path).name}")
    click.echo(f"  Architecture : {info.arch} ({info.bitness}-bit, {info.endianness})")
    click.echo(f"  NX (No-Exec) : {'✅' if info.mitigations.nx else '❌'}")
    click.echo(f"  Stack Canary : {'✅' if info.mitigations.canary else '❌'}")
    click.echo(f"  PIE          : {'✅' if info.mitigations.pie else '❌'}")
    click.echo(f"  RELRO        : {info.mitigations.relro}")


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
def lsp_check(file_path):
    """Run live compiler & AST diagnostics on a source file (U29)."""
    from hermes_core.lsp_bridge import create_lsp_bridge
    bridge = create_lsp_bridge(workspace_root=Path(file_path).parent, auto_fallback=True)
    bridge.open_document(file_path, Path(file_path).read_text())
    diags = bridge.format_diagnostics_for_prompt(file_path)
    click.echo(diags)


@click.command()
def audit():
    """Run master capability & contract spike integrity verification."""
    import subprocess
    cmd = [sys.executable, "bin/verify_harness_integrity.py"]
    res = subprocess.run(cmd, capture_output=False)
    sys.exit(res.returncode)


@click.command()
def status():
    """Display live 7-layer Agent OS system status."""
    from hermes_core.agent_os import create_agent_os_daemon
    daemon = create_agent_os_daemon()
    st = daemon.get_system_status()
    click.echo("🌐 HERMES AGENT OS TELEMETRY")
    click.echo("-" * 40)
    for k, v in st.items():
        click.echo(f"  {k:30s} : {v}")


@click.group()
@click.version_option(version="2.0.0", prog_name="hermes")
def cli():
    """Hermes Agent OS Harness — deterministic agent orchestration."""
    pass


# Add commands
cli.add_command(run)
cli.add_command(exam)
cli.add_command(replay)
cli.add_command(lineage)
cli.add_command(evolve)
cli.add_command(doctor)
cli.add_command(onboard)
cli.add_command(search)
cli.add_command(sec_audit, name="sec-audit")
cli.add_command(lsp_check, name="lsp-check")
cli.add_command(audit)
cli.add_command(status)


# Make 'run' the default command when no subcommand is provided
def main():
    # Check if first arg looks like a subcommand
    subcommands = {
        "exam", "replay", "lineage", "evolve", "doctor", "run",
        "onboard", "search", "sec-audit", "lsp-check", "audit", "status",
        "--help", "-h", "--version"
    }

    if len(sys.argv) > 1 and sys.argv[1] not in subcommands:
        # First arg is not a known subcommand - treat as prompt for 'run'
        sys.argv.insert(1, "run")

    cli()


if __name__ == "__main__":
    main()