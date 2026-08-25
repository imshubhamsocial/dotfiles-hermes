"""verify_skills_config.py — pre-run gate: Hermes profile `skills.external_dirs`
must be a proper YAML list, never the quoted-string form that silently nulls
skill injection (EXTERNAL_DIRS_INTEGRITY_AUDIT_2026-08-17, Entry 72-ADD36).

The loader (`~/.hermes/hermes-agent/agent/skill_utils.py`) wraps a str value
as ONE literal path (`if isinstance(raw_dirs, str): raw_dirs = [raw_dirs]`),
so `external_dirs: '[/path]'` resolves to `[]` — zero external skills reach
the prompt while every run *looks* valid. That defect class produced a VOID
A/B #51 and a FALSE P2 premise. This gate refuses to launch until every
profile that declares external_dirs uses the YAML-list form.

Usage:
    python3 bin/verify_skills_config.py                 # exit 0 = go · 1 = FAIL
    python3 bin/verify_skills_config.py --verbose       # per-profile detail

Wired into bin/run_hilo_bench.sh as gate 1c (after grader resolution).
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

try:
    import yaml  # PyYAML (hermes venv / ws-ai)
except ImportError:  # pragma: no cover - environment-specific
    yaml = None  # type: ignore[assignment]


def _profile_home() -> pathlib.Path:
    """Resolve the Hermes profiles dir the way the gateway does."""
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        root = pathlib.Path(hermes_home)
        profiles = root / "profiles"
        if profiles.is_dir():
            return profiles
        return root
    return pathlib.Path.home() / ".hermes" / "profiles"


def load_config(path: pathlib.Path):
    if yaml is None:
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def profile_external_dirs(cfg_path: pathlib.Path):
    """Return (raw, ok, reason) — ok=False when external_dirs is broken.

    Broken = string form (the silent-null defect) or a list whose paths don't
    exist (the loader drops them -> same silent result).
    """
    cfg = load_config(cfg_path)
    if not isinstance(cfg, dict):
        return None, True, ""
    skills = cfg.get("skills")
    if not isinstance(skills, dict):
        return None, True, "no skills block"
    if "external_dirs" not in skills:
        return None, True, "not declared"
    raw = skills["external_dirs"]
    if isinstance(raw, str):
        return raw, False, "string form (loader wraps it as one literal path -> [])"
    if not isinstance(raw, list) or not all(isinstance(p, str) for p in raw):
        return raw, False, f"unexpected type {type(raw).__name__}"
    missing = [
        p for p in raw
        if not pathlib.Path(os.path.expandvars(os.path.expanduser(p))).is_dir()
    ]
    if missing:
        return raw, False, f"listed path(s) do not exist: {missing}"
    return raw, True, ""


def check_profiles(profiles: pathlib.Path, verbose: bool = False) -> bool:
    if not profiles.is_dir():
        print(f"SKIP: profiles dir not found ({profiles}) — nothing to check")
        return True
    ok_all = True
    found = 0
    for d in sorted(profiles.iterdir()):
        cfg = d / "config.yaml"
        if not cfg.is_file():
            continue
        found += 1
        raw, ok, reason = profile_external_dirs(cfg)
        if not ok:
            ok_all = False
            print(f"FAIL {d.name}: external_dirs broken — {reason}")
            if raw is not None:
                print(f"     value: {raw!r}")
        elif verbose:
            print(f"OK   {d.name}: external_dirs={raw}")
    if found == 0:
        print(f"SKIP: no config.yaml under {profiles}")
    return ok_all


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    profiles = _profile_home()
    ok = check_profiles(profiles, verbose=args.verbose)
    if ok:
        print("verify_skills_config: PASS — no profile carries a broken external_dirs")
        return 0
    print(
        "verify_skills_config: FAIL — external_dirs string form silently nulls "
        "skill injection (see EXTERNAL_DIRS_INTEGRITY_AUDIT_2026-08-17.md); "
        "fix the profile(s) above before any run"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
