"""M6 input validation and the distinction between success and reliability."""

import pytest

from lab9 import stats

pytestmark = pytest.mark.student


@pytest.mark.parametrize("name", ["pass_at_k", "pass_hat_k"])
@pytest.mark.parametrize("counts", [
    (0, 0, 1), (-1, 0, 1), (5, -1, 1), (5, 6, 1), (5, 2, 0), (5, 2, 6),
    (5.0, 2, 1), (5, 2.0, 1), (5, 2, True),
])
def test_invalid_trial_counts_raise(name, counts):
    with pytest.raises(ValueError):
        getattr(stats, name)(*counts)


@pytest.mark.parametrize("n,c,k", [(5, 4, 5), (5, 2, 3), (10, 3, 5), (10, 8, 2)])
def test_pass_k_reliability_order(n, c, k):
    assert 0 <= stats.pass_hat_k(n, c, k) <= c / n <= stats.pass_at_k(n, c, k) <= 1
    assert stats.pass_at_k(n, c, 1) == pytest.approx(c / n)
    assert stats.pass_hat_k(n, c, 1) == pytest.approx(c / n)


def test_aggregate_reliability_blocks_one_bad_seed_when_mean_passes():
    from lab9.eval import aggregate
    from lab9.gate import check

    rows = [{"item_id": f"E-{item}", "seed": seed, "pass_rate": item == 0 or seed != 4, "cost": 1.0}
            for item in range(2) for seed in range(5)]
    base_rows = [{**row, "pass_rate": True} for row in rows]
    manifest = {"eval_set_sha": "same-set", "items": 2, "seeds": list(range(5))}
    current = {"manifest": manifest, "rows": rows, "evaluator_failures": [],
               "metrics": aggregate(rows, ["pass_rate"], k_values=[1, 3, 5])}
    baseline = {"manifest": manifest, "rows": base_rows, "evaluator_failures": [],
                "metrics": aggregate(base_rows, ["pass_rate"], k_values=[1, 3, 5])}
    spec = {"metrics": [
        {"id": "pass_rate", "threshold": {"min": 0.85, "no_significant_drop": True}, "blocking": True},
        {"id": "pass_hat_5", "threshold": {"min": 0.8}, "blocking": True},
    ]}
    assert current["metrics"]["pass_rate"] == 0.9
    assert current["metrics"]["pass_at_5"] == 1.0
    assert current["metrics"]["pass_hat_5"] == 0.5
    assert check(current, baseline, spec)[0] == ["pass_hat_5"]
