"""M2 calibration regressions through the judge's normal entry point."""

import csv
import math
from pathlib import Path

import pytest

from lab9.judge import calibrate

pytestmark = pytest.mark.student


@pytest.mark.parametrize("name,passed,precision,recall,kappa", [
    ("tone", True, 0.857, 0.8, 0.757),
    ("helpful", False, 1.0, 0.3, 0.375),
])
def test_public_judge_calibration(name, passed, precision, recall, kappa):
    result = calibrate(Path(f"data/eval/judge_{name}_public.csv"))
    assert result["passed"] is passed
    assert (result["precision"], result["recall"], result["kappa"]) == (precision, recall, kappa)
    assert result["corrected_fail_rate"] == 0.3


@pytest.mark.parametrize("human", [("PASS", "PASS"), ("PASS", "FAIL")])
def test_constant_pass_judge_fails_without_crashing(tmp_path, human):
    path = tmp_path / "constant.csv"
    with path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source)
        writer.writerow(["item_id", "reply", "human", "judge"])
        for i, label in enumerate(human):
            writer.writerow([str(i), "reply", label, "PASS"])
    result = calibrate(path)
    assert result["passed"] is False
    assert math.isnan(result["corrected_fail_rate"])
    assert math.isnan(result["kappa"]) or result["kappa"] == 0.0


def test_calibration_compares_floor_before_rounding(tmp_path):
    path = tmp_path / "near_floor.csv"
    with path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source)
        writer.writerow(["item_id", "reply", "human", "judge"])
        for actual, predicted, count in [("FAIL", "FAIL", 1999), ("PASS", "FAIL", 501),
                                         ("PASS", "PASS", 5000)]:
            writer.writerows([f"{actual}-{predicted}-{i}", "reply", actual, predicted]
                             for i in range(count))
    result = calibrate(path)
    assert result["precision"] == 0.8  # 1999/2500 = 0.7996 only rounds up for display.
    assert result["kappa"] >= 0.6 and result["recall"] >= 0.7
    assert result["passed"] is False
