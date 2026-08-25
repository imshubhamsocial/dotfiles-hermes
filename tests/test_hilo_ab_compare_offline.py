"""Offline tests: hilo_ab_compare verdict engine (AB_PROTOCOL D.1)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bin import hilo_ab_compare as H  # noqa: E402


def _row(status, comp, wall=100.0, tokens=0):
    return {"tier": "hard", "status": status, "attempts": 1,
            "wall_s": wall, "tokens": tokens, "composite": comp}


def test_adopt_model_tier():
    b = {f"T{i}": _row("pass", 90.0) for i in range(1, 8)}
    c = {f"T{i}": _row("pass", 98.0) for i in range(1, 8)}
    v = H.verdict(c, b, tier="model")
    assert v["verdict"] == "ADOPT"
    assert v["mean_d_comp"] == 8.0


def test_reject_on_regression():
    b = {f"T{i}": _row("pass", 90.0) for i in range(1, 8)}
    c = {f"T{i}": _row("pass", 98.0) for i in range(1, 8)}
    c["T4"] = _row("exhausted", 0.0)
    v = H.verdict(c, b, tier="model")
    assert v["verdict"] == "REJECT"
    assert v["per_task"][3]["regressed"] is True


def test_reject_on_negative_mean():
    b = {f"T{i}": _row("pass", 90.0) for i in range(1, 8)}
    c = {f"T{i}": _row("pass", 88.0) for i in range(1, 8)}
    assert H.verdict(c, b, tier="model")["verdict"] == "REJECT"


def test_inconclusive_below_margin():
    b = {f"T{i}": _row("pass", 90.0) for i in range(1, 8)}
    c = {f"T{i}": _row("pass", 92.0) for i in range(1, 8)}
    assert H.verdict(c, b, tier="model")["verdict"] == "INCONCLUSIVE"


def test_speed_tier_adopts_on_wall_drop():
    b = {f"T{i}": _row("pass", 90.0, wall=400.0) for i in range(1, 8)}
    c = {f"T{i}": _row("pass", 90.0, wall=280.0) for i in range(1, 8)}
    v = H.verdict(c, b, tier="speed")
    assert v["verdict"] == "ADOPT"          # −30% wall, no regression


def test_speed_tier_blocks_on_composite_regression():
    b = {f"T{i}": _row("pass", 90.0, wall=400.0) for i in range(1, 8)}
    c = {f"T{i}": _row("pass", 80.0, wall=280.0) for i in range(1, 8)}
    assert H.verdict(c, b, tier="speed")["verdict"] == "REJECT"
