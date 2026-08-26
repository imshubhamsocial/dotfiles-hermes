"""
Hermes Harness — Centralized Path Resolution (XDG-compliant)
=============================================================
Single source of truth for all filesystem locations. No hardcoded
paths anywhere else in the codebase. Respects:
  - XDG_CONFIG_HOME / XDG_DATA_HOME
  - HERMES_CONFIG_DIR override (highest priority)
  - Production install prefix (/opt/hermes-harness)
  - Development fallback (repo root)
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class HermesPaths:
    """All resolved paths for the harness."""

    # User config (XDG)
    config_dir: Path
    profiles_dir: Path
    skills_dir: Path
    soul_file: Path

    # Production install
    install_prefix: Path
    lib_dir: Path
    bin_dir: Path
    skills_builtin_dir: Path
    tests_dir: Path
    docs_dir: Path
    registry_file: Path

    # Runtime (RAMDisk)
    trajectory_path: Path
    lineage_path: Path

    # Model server
    default_base_url: str = "http://127.0.0.1:8138/v1"
    default_model: str = "gemma-4-E4B-it-Q4_K_M"


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME",
                Path.home() / ".config"))


def _xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME",
                Path.home() / ".local" / "share"))


def _detect_install_prefix() -> Path:
    """Detect production install prefix. Priority:
    1. HERMES_INSTALL_PREFIX env var
    2. /opt/hermes-harness (standard production)
    3. Development repo root (fallback)
    """
    if env := os.environ.get("HERMES_INSTALL_PREFIX"):
        return Path(env)

    prod = Path("/opt/hermes-harness")
    if prod.exists():
        return prod

    # Development fallback — walk up from this file
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "src" / "hermes_core").exists():
            return parent
    return prod  # default even if missing


def _detect_config_dir() -> Path:
    """Resolve user config directory. Priority:
    1. HERMES_CONFIG_DIR env var
    2. XDG_CONFIG_HOME/hermes
    3. ~/.hermes (legacy default)
    """
    if env := os.environ.get("HERMES_CONFIG_DIR"):
        return Path(env)

    xdg = _xdg_config_home() / "hermes"
    if xdg.exists() or not (Path.home() / ".hermes").exists():
        return xdg

    return Path.home() / ".hermes"


def get_paths() -> HermesPaths:
    """Get fully resolved paths singleton."""
    install_prefix = _detect_install_prefix()
    config_dir = _detect_config_dir()

    return HermesPaths(
        config_dir=config_dir,
        profiles_dir=config_dir / "profiles",
        skills_dir=config_dir / "skills",
        soul_file=config_dir / "SOUL.md",

        install_prefix=install_prefix,
        lib_dir=install_prefix / "lib",
        bin_dir=install_prefix / "bin",
        skills_builtin_dir=install_prefix / "skills",
        tests_dir=install_prefix / "tests",
        docs_dir=install_prefix / "docs",
        registry_file=install_prefix / "registry.yaml",

        trajectory_path=Path(
            os.environ.get("HERMES_TRAJECTORY_PATH",
                "/dev/shm/hermes_trajectory/trajectory.jsonl")),
        lineage_path=Path(
            os.environ.get("HERMES_LINEAGE_PATH",
                "/dev/shm/hermes_lineage/lineage_tree.jsonl")),
    )


# Backwards-compatible helpers for gradual migration
def get_config_dir() -> Path:
    return get_paths().config_dir


def get_profiles_dir() -> Path:
    return get_paths().profiles_dir


def get_skills_dir() -> Path:
    return get_paths().skills_dir


def get_trajectory_path() -> Path:
    return get_paths().trajectory_path


def get_lineage_path() -> Path:
    return get_paths().lineage_path


def get_registry_path() -> Path:
    return get_paths().registry_file


def get_install_prefix() -> Path:
    return get_paths().install_prefix


if __name__ == "__main__":
    p = get_paths()
    print("Hermes Paths:")
    for k, v in vars(p).items():
        print(f"  {k}: {v}")