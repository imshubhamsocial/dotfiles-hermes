"""Deterministic Machine Verification Gate for Phase 27 (Selective Decision Router & Attractor)."""

import json
import os
import pathlib
import subprocess
import sys

# Ensure .hermes is importable
hermes_dir = pathlib.Path(__file__).resolve().parents[2] / ".hermes"
if str(hermes_dir) not in sys.path:
    sys.path.insert(0, str(hermes_dir))

from mcp_openjev import jev_decide, jev_latent_deliberate


def test_phase27_read_only_recon_bypass():
    """Asserts that read_only actions short-circuit with 0 LLM calls."""
    res = jev_decide(
        premise="Read file outline",
        hypothesis_a="npx ast-grep outline scenario/rate_limiter.py",
        hypothesis_b="cat scenario/rate_limiter.py",
        action_type="read_only"
    )
    assert res["gate_bypassed"] is True, f"Read-only action not bypassed: {res}"
    assert res["llm_calls"] == 0, f"Expected 0 LLM calls, got {res['llm_calls']}"
    assert res["cache_preserved"] is True
    print("✅ Phase 27 Read-Only Bypass Verified (0 LLM overhead)")


def test_phase27_uncertainty_gated_probe():
    """Asserts that mutating/high-blast actions trigger Port 8138 logprob probe."""
    res = jev_decide(
        premise="Fix timestamp bug in TokenBucketRateLimiter",
        hypothesis_a="Update self.last_refill = now unconditionally",
        hypothesis_b="Only update when tokens > 0",
        focus_uri="scenario/rate_limiter.py",
        action_type="mutate",
        strike_count=1,
        ast_callers=4
    )
    assert res["gate_triggered"] is True, f"Gate not triggered: {res}"
    assert res["decision"] in ("A", "B"), f"Invalid decision: {res}"
    assert res["cache_preserved"] is True, "KV slot cache not preserved"
    assert res["focus_scoped"] is True, "Focus boundary check failed"
    print(f"✅ Phase 27 Uncertainty Gated Probe Verified: Decision {res['decision']}, Prob {res['prob']}")


def test_phase27_contractive_latent_deliberation():
    """Asserts that jev_latent_deliberate converges in <= 6 steps with Lipschitz bound < 1."""
    res = jev_latent_deliberate([0.5, -0.3, 0.8, 0.1], epsilon=0.01, max_loops=6)
    assert res["converged"] is True, f"Latent attractor failed to converge: {res}"
    assert res["steps"] <= 6, f"Expected <= 6 steps, took {res['steps']}"
    assert res["lipschitz_bound"] < 1.0, f"Lipschitz bound not contractive: {res['lipschitz_bound']}"
    print(f"✅ Phase 27 Latent Deliberation Verified: Converged in {res['steps']} steps (factor={res['lipschitz_bound']})")


def test_phase27_rate_limiter_repair_and_receipt():
    """Asserts surgical patch application and cryptographic receipt sealing."""
    testbed_root = pathlib.Path(__file__).resolve().parent
    limiter_file = testbed_root / "scenario" / "rate_limiter.py"

    cmd = ["pytest", str(testbed_root / "scenario" / "test_rate_limiter.py"), "-q"]
    proc = subprocess.run(cmd, cwd=str(testbed_root), capture_output=True, text=True)
    assert proc.returncode == 0, f"pytest failed with code {proc.returncode}: {proc.stderr}"

    receipt_file = pathlib.Path("/tmp/hermes_verified_receipt.json")
    assert receipt_file.exists(), "Cryptographic receipt /tmp/hermes_verified_receipt.json not found"
    receipt = json.loads(receipt_file.read_text())
    assert receipt["exitstatus"] == 0, "Receipt exitstatus is non-zero"
    assert "scenario/rate_limiter.py" in receipt["modified"], "Modified file not listed in receipt"
    print(f"✅ Epistemic Closure Verified: Receipt validated with SHA256 {receipt['git_diff_sha256'][:8]}")


if __name__ == "__main__":
    test_phase27_read_only_recon_bypass()
    test_phase27_uncertainty_gated_probe()
    test_phase27_contractive_latent_deliberation()
    test_phase27_rate_limiter_repair_and_receipt()
    print("\n🎉 ALL PHASE 27 VERIFICATION CHECKS PASSED (EXIT 0)!")
