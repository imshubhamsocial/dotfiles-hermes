"""
U18 Hermes Self-Evolution & AlphaEvolve Engine (Phase 4.4)
===========================================================
Offline genetic-Pareto evolution of prompts/skills (Nous GEPA pattern)
plus exact-rational numerical verification (DeepMind AlphaEvolve
pattern). Operates OUTSIDE the live agent runtime and consumes U6
trajectory streams — eliminating in-session self-congratulation bias
(roadmap §4.4).

Components:

  1. GEPA loop (`mutate_*`, `gepa_loss`, `pareto_frontier`):
     Deterministic mutation operators (whitespace prune, filler drop,
     line dedupe). Fitness follows the spec formula
         Loss = (1 - PassRate) + lambda * TokenCount
     where PassRate is the U7 replay deterministic-match rate over the
     provided historical streams — an external arbiter, never an LLM
     grading itself.

  2. Regression Sieve commit gate (`commit_skill_variant`):
     A variant is committed ONLY if every historical stream replays
     clean AND the variant does not grow the token footprint (Trap-1:
     Prompt Rot / Context Bloat).

  3. AlphaEvolve numerical sieve (`verify_rational_exact`,
     `run_numerical_sieve`): candidate snippets must prove their
     numeric claims in EXACT rational arithmetic (fractions.Fraction).
     Any IEEE-754 drift (e.g. 0.30000000000000004 vs 3/10) is rejected
     (Trap-2: Floating-Point Rounding Error Hallucination).
"""

import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from .presets import estimate_prompt_tokens
    from .replay import replay_trajectory
    from .gepa_optimizer import GEPALiteOptimizer, GEPACandidate, GEPAResult, create_gepa_optimizer
except ImportError:  # packageless loaders (integrity probes)
    from hermes_core.presets import estimate_prompt_tokens
    from hermes_core.replay import replay_trajectory
    from hermes_core.gepa_optimizer import GEPALiteOptimizer, GEPACandidate, GEPAResult, create_gepa_optimizer

LAMBDA_TOKEN_PENALTY = 0.01
FILLER_PHRASES = (
    "Please note that ", "It is important to ", "Kindly ",
    "As you know, ", "Make sure to ", "Be sure to ",
)


# ─── GEPA: deterministic mutations & Pareto selection ────────────────────────

def mutate_prune_whitespace(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: List[str] = []
    blank_run = 0
    for ln in lines:
        blank_run = blank_run + 1 if not ln.strip() else 0
        if blank_run > 1:
            continue
        out.append(ln)
    return "\n".join(out).strip() + "\n"


def mutate_drop_filler(text: str) -> str:
    for phrase in FILLER_PHRASES:
        text = text.replace(phrase, "")
    return text


def mutate_dedupe_lines(text: str) -> str:
    seen = set()
    out = []
    for ln in text.splitlines():
        key = ln.strip()
        if key and key in seen:
            continue
        seen.add(key)
        out.append(ln)
    return "\n".join(out).strip() + "\n"


MUTATION_OPERATORS = (mutate_prune_whitespace, mutate_drop_filler,
                      mutate_dedupe_lines)


def evolve_one_generation(text: str) -> List[str]:
    """All single-operator offspring of one genome (deterministic)."""
    variants = set()
    for op in MUTATION_OPERATORS:
        variants.add(op(text))
    return sorted(v for v in variants if v and v != text)


def gepa_loss(text: str, pass_rate: float,
              lam: float = LAMBDA_TOKEN_PENALTY) -> float:
    """Spec §4.4 Trap-1 fitness: Loss = (1-PassRate) + lambda*TokenCount."""
    return (1.0 - pass_rate) + lam * estimate_prompt_tokens(text)


def pareto_frontier(candidates: Sequence[Tuple[str, float]]) -> List[str]:
    """Non-dominated set over (pass_rate ↑, token_count ↓)."""
    scored = [(t, p, estimate_prompt_tokens(t)) for t, p in candidates]
    front = []
    for i, (t, p, n) in enumerate(scored):
        dominated = any(
            (p2 >= p and n2 < n) or (p2 > p and n2 <= n)
            for j, (_t2, p2, n2) in enumerate(scored) if j != i
        )
        if not dominated:
            front.append(t)
    return front


# ─── Regression Sieve commit gate ────────────────────────────────────────────

@dataclass
class CommitDecision:
    committed: bool
    reason: str
    tokens_before: int
    tokens_after: int
    history_replay_clean: bool


def commit_skill_variant(variant_text: str, original_text: str,
                         skill_name: str, history_streams: Sequence[Any],
                         skills_dir: Optional[Path] = None) -> CommitDecision:
    """Commit ONLY on: 100% clean replay of all historical streams AND
    zero token bloat AND syntactically sound output."""
    tb = estimate_prompt_tokens(original_text)
    ta = estimate_prompt_tokens(variant_text)

    if not variant_text.strip():
        return CommitDecision(False, "empty variant", tb, ta, False)

    all_clean = True
    detail = []
    for s in history_streams:
        rep = replay_trajectory(s)
        all_clean &= rep.deterministic_match
        detail.append(f"{Path(s).name}:{rep.drifted_steps}d")
    if history_streams and not all_clean:
        return CommitDecision(
            False, f"regression sieve failed (history drift: {', '.join(detail)})",
            tb, ta, False)

    if ta > tb:
        return CommitDecision(
            False, f"token bloat blocked ({ta} > {tb})", tb, ta, all_clean)

    target = Path(skills_dir) if skills_dir else Path.home() / ".hermes" / "skills"
    target.mkdir(parents=True, exist_ok=True)
    (target / skill_name).write_text(variant_text, encoding="utf-8")
    return CommitDecision(True, f"sieved clean (history: {detail or 'none'})",
                          tb, ta, all_clean)


# ─── AlphaEvolve exact-rational numerical sieve ──────────────────────────────

def verify_rational_exact(computed: str, expected: Fraction) -> Tuple[bool, str]:
    """Exact equality in rational arithmetic; ANY decimal drift rejects."""
    try:
        got = Fraction(computed.strip())
    except (ValueError, ZeroDivisionError) as e:
        return False, f"unparseable rational '{computed}': {e}"
    if got != expected:
        return False, f"precision drift: got {got}, proof requires {expected}"
    return True, f"exact match {got}"


def run_numerical_sieve(snippet_path: Path,
                        claims: Dict[str, Fraction]) -> Dict[str, Any]:
    """Execute a candidate snippet (subprocess, offline) that prints
    'KEY=VALUE' lines with exact rational VALUEs; verify every claim."""
    proc = subprocess.run([sys.executable, str(snippet_path)],
                          capture_output=True, text=True, timeout=30)
    results: Dict[str, Any] = {"returncode": proc.returncode,
                               "claims": {}, "accepted": proc.returncode == 0}
    if proc.returncode != 0:
        results["error"] = proc.stderr.splitlines()[-1] if proc.stderr else "nonzero exit"
        results["accepted"] = False
        return results
    for line in proc.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key not in claims:
            continue
        ok, msg = verify_rational_exact(val, claims[key])
        results["claims"][key] = {"ok": ok, "msg": msg}
        if not ok:
            results["accepted"] = False
    missing = set(claims) - set(results["claims"])
    if missing:
        results["accepted"] = False
        results["missing_claims"] = sorted(missing)
    return results
