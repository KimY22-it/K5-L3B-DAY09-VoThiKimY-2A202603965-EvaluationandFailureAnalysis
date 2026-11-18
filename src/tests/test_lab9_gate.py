"""M4 gate decisions on paired item/seed results."""

import pytest

from lab9.gate import check

pytestmark = pytest.mark.student


def report(rates):
    rows = [{"item_id": f"E-{item}", "seed": seed, "pass_rate": seed < round(rate * 10)}
            for item, rate in enumerate(rates) for seed in range(10)]
    return {"manifest": {"eval_set_sha": "same-set"}, "rows": rows,
            "metrics": {"pass_rate": sum(row["pass_rate"] for row in rows) / len(rows)}}


def spec(confidence=0.95, floor=0.85):
    return {"bootstrap": {"n_resamples": 1000, "rng": 2027, "confidence": confidence},
            "metrics": [{"id": "pass_rate", "blocking": True,
                         "threshold": {"min": floor, "no_significant_drop": True}}]}


def test_unchanged_paired_results_pass_gate():
    base = report([1, 0.8, 1, 1, 1])
    blocked, lines = check(base, base, spec())
    assert blocked == []
    assert "CI [+0.000, +0.000]" in lines[0]


def test_significant_drop_is_blocked_even_above_floor():
    blocked, lines = check(report([0.9] * 5), report([1] * 5), spec())
    assert blocked == ["pass_rate"]
    assert "CI [-0.100, -0.100]" in lines[0]


def test_gate_uses_confidence_from_shared_spec():
    pr = report([1, 0.8, 0.8, 0.6, 0.6])
    base = report([1, 1, 0.8, 1, 0.6])
    blocked_95, _ = check(pr, base, spec(confidence=0.95, floor=0.5))
    blocked_50, _ = check(pr, base, spec(confidence=0.5, floor=0.5))
    assert blocked_95 == []
    assert blocked_50 == ["pass_rate"]
