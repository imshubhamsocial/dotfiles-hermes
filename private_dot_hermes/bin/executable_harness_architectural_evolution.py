#!/usr/bin/env python3.13
"""
Full-System Google Env-Harness Architectural Evolution CLI
==========================================================
Mines historical trajectory streams, extracts recurring failures, grounds fixes via
SearXNG web research, executes genetic Pareto optimization with held-out generalization
guards, and exports the evolved harness architecture.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project roots
def find_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / 'tests').exists() and (parent / 'pyproject.toml').exists():
            return parent
        if (parent / '.hermes').exists() and parent.name != '.hermes':
            return parent
    return Path.cwd()

ROOT = find_project_root()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

from hermes_core.harness_evolution import (
    ArchitecturalHarnessState,
    FullSystemHarnessEvolutionEngine,
    create_full_system_evolution_engine,
)
from hermes_core.web_grounding import WebGroundingEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Env-Harness Master Architectural Evolution")
    parser.add_argument("--trajectories", nargs="*", default=[], help="Paths to trajectory.jsonl files")
    parser.add_argument("--generations", type=int, default=10, help="Number of genetic generations")
    parser.add_argument("--population-size", type=int, default=12, help="Population size per generation")
    parser.add_argument(
        "--output",
        default=".hermes/rules/evolved_harness_architecture.json",
        help="Target output path for evolved architecture JSON",
    )
    args = parser.parse_args()

    print("🚀 Initializing Google Env-Harness Architectural Evolution Engine...")
    web_engine = WebGroundingEngine()
    engine = create_full_system_evolution_engine(
        historical_trajectories=args.trajectories,
        web_grounding_engine=web_engine,
    )

    print(f"🧬 Evolving harness architecture over {args.generations} generations (pop={args.population_size})...")
    evolved_state, fitness = engine.evolve_architecture(
        generations=args.generations,
        population_size=args.population_size,
    )

    out_path = engine.export_architecture(evolved_state, args.output)
    print(f"✅ Master Architecture Evolution Complete (Fitness: {fitness:.4f})")
    print(f"📁 Exported Evolved Architecture to: {out_path}")
    print("\n--- EVOLVED ARCHITECTURAL STATE ---")
    print(json.dumps(evolved_state.to_dict(), indent=2))


if __name__ == "__main__":
    main()
