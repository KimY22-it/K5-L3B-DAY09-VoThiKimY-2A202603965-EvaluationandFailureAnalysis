"""M5 slice decisions, including paired regressions hidden by the overall mean."""

import pytest

from lab9.gate import slice_check

pytestmark = pytest.mark.student


def report(rates):
    return {"rows": [
        {"item_id": f"E-{item}", "seed": seed, "pass_rate": seed < successes,
         "slices": ["money_movement"]}
        for item, successes, seeds in rates for seed in range(seeds)
    ]}


def spec(**overrides):
    rule = {"name": "money_movement", "metric": "pass_rate", "min": 0.9, "blocking": True}
    rule.update(overrides)
    return {"slices": [rule]}


def test_slice_mean_weights_items_equally():
    current = report([(1, 4, 5), (2, 0, 1)])
    baseline = report([(1, 5, 5), (2, 1, 1)])
    blocked, _ = slice_check(current, baseline, spec(min=0.5))
    assert blocked == ["slice:money_movement/pass_rate"]  # Per-item mean is 0.4, row mean is 4/6.


def test_significant_slice_drop_blocks_even_above_floor():
    current = report([(1, 4, 5), (2, 4, 5), (3, 4, 5)])
    baseline = report([(1, 5, 5), (2, 5, 5), (3, 5, 5)])
    blocked, lines = slice_check(current, baseline, spec(min=0.7, no_significant_drop=True))
    assert blocked == ["slice:money_movement/pass_rate"]
    assert "CI [-0.200, -0.200]" in lines[0]


@pytest.mark.parametrize("current", [report([]), report([(1, 5, 5)])])
def test_missing_slice_items_block(current):
    baseline = report([(1, 5, 5), (2, 5, 5)])
    blocked, lines = slice_check(current, baseline, spec(no_significant_drop=True))
    assert blocked == ["slice:money_movement/pass_rate"]
    assert "missing or unmatched" in lines[0]


def test_nonblocking_slice_reports_warning():
    current = report([(1, 0, 5)])
    baseline = report([(1, 5, 5)])
    blocked, lines = slice_check(current, baseline, spec(blocking=False))
    assert blocked == []
    assert "warn" in lines[0]


def test_unchanged_slice_passes():
    baseline = report([(1, 5, 5), (2, 5, 5)])
    blocked, lines = slice_check(baseline, baseline, spec(no_significant_drop=True))
    assert blocked == []
    assert "CI [+0.000, +0.000]" in lines[0]
