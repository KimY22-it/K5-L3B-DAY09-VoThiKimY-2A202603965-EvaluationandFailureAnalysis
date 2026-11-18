"""M7 traps that can otherwise hide behind green metrics or matching sets."""

import copy
import json
import subprocess
import sys

import pytest

from lab9.gate import check, integrity_check

pytestmark = pytest.mark.student


@pytest.fixture
def green_report():
    rows = [{"item_id": f"E-{item}", "seed": seed, "pass_rate": True,
             "secret_leak": False, "cost": 1.0, "slices": ["money_movement"] if item < 2 else []}
            for item in range(4) for seed in (1, 2)]
    return {"manifest": {"items": 4, "seeds": [1, 2], "eval_set_sha": "same-set"},
            "rows": rows, "evaluator_failures": [],
            "metrics": {"pass_rate": 1.0, "secret_leak": 0, "cost_per_success": 1.0}}


@pytest.fixture
def spec():
    return {"eval_set_version": "v2", "metrics": [
        {"id": "pass_rate", "kind": "capability", "blocking": True,
         "threshold": {"min": 0.8, "no_significant_drop": True}},
        {"id": "secret_leak", "kind": "safety", "blocking": True, "threshold": {"max": 0}},
        {"id": "cost_per_success", "kind": "system", "blocking": False,
         "threshold": {"max_increase": 0.1}},
    ], "slices": [{"name": "money_movement", "metric": "pass_rate", "min": 0.8,
                   "no_significant_drop": True, "blocking": True}]}


def test_clean_report_passes_integrity_and_gate(green_report, spec):
    assert integrity_check(green_report, green_report, spec, spec) == []
    assert check(green_report, green_report, spec, spec)[0] == []


@pytest.mark.parametrize("trap,reason", [
    ("duplicated_rows", "duplicate"),
    ("green_evaluator_failure", "evaluator_failures"),
    ("missing_assertion", "graded row value"),
    ("invalid_cost", "invalid cost"),
    ("forged_summary", "summary disagrees"),
    ("relabeled_slice", "slice tags"),
    ("substituted_seed", "item x seed"),
    ("duplicated_seeds", "duplicate manifest seeds"),
    ("missing_metric", "missing metrics"),
    ("invalid_k", "cannot recompute metrics"),
    ("overflowing_metric", "nonfinite value"),
])
def test_hidden_style_report_traps_block(green_report, spec, trap, reason):
    current = copy.deepcopy(green_report)
    if trap == "duplicated_rows":
        current["rows"] *= 2
        current["manifest"]["items"] *= 2  # Count and unique pair set alone can both look valid.
    elif trap == "green_evaluator_failure":
        current["evaluator_failures"] = ["grader crashed even though summary is green"]
    elif trap == "missing_assertion":
        current["rows"][0]["pass_rate"] = None
    elif trap == "invalid_cost":
        current["rows"][0]["cost"] = float("nan")
    elif trap == "forged_summary":
        current["rows"][0]["pass_rate"] = False
    elif trap == "relabeled_slice":
        current["rows"][0]["slices"] = []
    elif trap == "substituted_seed":
        current["rows"][0]["seed"] = 999
    elif trap == "duplicated_seeds":
        current["manifest"]["seeds"] = [1, 1]
    elif trap == "missing_metric":
        del current["metrics"]["pass_rate"]
    elif trap == "invalid_k":
        current["metrics"]["pass_at_0"] = 1.0
    elif trap == "overflowing_metric":
        current["metrics"]["pass_rate"] = 10 ** 400
    blocked, lines = check(current, green_report, spec)
    assert blocked == ["integrity"]
    assert any("INTEGRITY" in line and reason in line for line in lines)


@pytest.mark.parametrize("trap", [
    "lower_min", "raise_max", "raise_cost_limit", "remove_min", "remove_drop_check",
    "disable_metric", "remove_metric", "lower_slice_min", "remove_slice_drop_check",
    "disable_slice", "remove_slice", "change_slice_metric",
])
def test_ratchet_blocks_looser_same_version_rules(green_report, spec, trap):
    current = copy.deepcopy(spec)
    if trap == "lower_min":
        current["metrics"][0]["threshold"]["min"] = 0.7
    elif trap == "raise_max":
        current["metrics"][1]["threshold"]["max"] = 1
    elif trap == "raise_cost_limit":
        current["metrics"][2]["threshold"]["max_increase"] = 0.2
    elif trap == "remove_min":
        del current["metrics"][0]["threshold"]["min"]
    elif trap == "remove_drop_check":
        del current["metrics"][0]["threshold"]["no_significant_drop"]
    elif trap == "disable_metric":
        current["metrics"][0]["blocking"] = False
    elif trap == "remove_metric":
        current["metrics"].pop(1)
    elif trap == "lower_slice_min":
        current["slices"][0]["min"] = 0.7
    elif trap == "remove_slice_drop_check":
        del current["slices"][0]["no_significant_drop"]
    elif trap == "disable_slice":
        current["slices"][0]["blocking"] = False
    elif trap == "remove_slice":
        current["slices"] = []
    elif trap == "change_slice_metric":
        current["slices"][0]["metric"] = "secret_leak"
    blocked, lines = check(green_report, green_report, current, spec)
    assert blocked == ["integrity"]
    assert any("ratchet" in line for line in lines)


def test_ratchet_allows_tighter_rules(green_report, spec):
    tighter = copy.deepcopy(spec)
    tighter["metrics"][0]["threshold"]["min"] = 0.9
    tighter["metrics"][2]["threshold"]["max_increase"] = 0.05
    tighter["slices"][0]["min"] = 0.9
    assert integrity_check(green_report, green_report, tighter, spec) == []


def test_cli_reports_integrity_for_malformed_manifest(tmp_path, green_report, spec):
    import yaml

    current = tmp_path / "broken.json"
    baseline = tmp_path / "baseline.json"
    config = tmp_path / "spec.yaml"
    current.write_text(json.dumps({"manifest": None, "rows": [], "metrics": {}}), encoding="utf-8")
    baseline.write_text(json.dumps(green_report), encoding="utf-8")
    config.write_text(yaml.safe_dump(spec), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "lab9.gate", "--pr", str(current),
         "--baseline", str(baseline), "--spec", str(config)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 1
    assert "INTEGRITY" in result.stdout
    assert "Traceback" not in result.stderr
