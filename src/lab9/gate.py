"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite_number(value) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _report_problems(report: dict, spec: dict, name: str) -> list[str]:
    """Validate a report before reading its rows or recomputing its scores."""
    problems = []
    if not isinstance(report, dict):
        return [f"{name}: report must be an object"]
    manifest, rows, metrics = report.get("manifest"), report.get("rows"), report.get("metrics")
    if not isinstance(manifest, dict) or not isinstance(rows, list) or not isinstance(metrics, dict):
        return [f"{name}: manifest, rows or metrics has invalid structure"]
    items, seeds = manifest.get("items"), manifest.get("seeds")
    if type(items) is not int or items <= 0:
        problems.append("manifest items must be a positive integer")
    if not isinstance(seeds, list) or not seeds or any(type(seed) is not int for seed in seeds):
        problems.append("manifest seeds must be a nonempty list of integers")
    elif len(set(seeds)) != len(seeds):
        problems.append("duplicate manifest seeds")
    if not manifest.get("eval_set_sha"):
        problems.append("missing eval_set_sha")
    if spec.get("metric_spec_version") and manifest.get("metric_spec_version") != spec["metric_spec_version"]:
        problems.append("metric_spec_version differs from the supplied spec")
    failures = report.get("evaluator_failures")
    if not isinstance(failures, list) or failures:
        problems.append("evaluator_failures must be an empty list, including on green runs")
    if any(not _finite_number(value) for value in metrics.values()):
        problems.append("metrics contain a missing, nonnumeric or nonfinite value")
    required = {metric["id"] for metric in spec["metrics"]}
    if required - metrics.keys():
        problems.append(f"missing metrics: {sorted(required - metrics.keys())}")
    if any(not isinstance(row, dict) or not isinstance(row.get("item_id"), str)
           or not row["item_id"] or type(row.get("seed")) is not int for row in rows):
        problems.append("rows have invalid item_id or seed")
    if problems:
        return [f"{name}: {problem}" for problem in problems]

    pairs = Counter((row["item_id"], row["seed"]) for row in rows)
    item_ids = {item for item, _ in pairs}
    if len(rows) != items * len(seeds):
        problems.append("row count differs from manifest items x seeds")
    if any(count != 1 for count in pairs.values()):
        problems.append("duplicate (item_id, seed) rows")
    if len(item_ids) != items or set(pairs) != {(item, seed) for item in item_ids for seed in seeds}:
        problems.append("rows do not cover every item x seed exactly once")
    row_metrics = (required | metrics.keys()) & GRADERS.keys()
    for row in rows:
        identity = f"{row['item_id']}@{row['seed']}"
        if any(not isinstance(row.get(metric), (bool, int, float)) or row[metric] not in (0, 1)
               for metric in row_metrics):
            problems.append(f"{identity}: graded row value missing or not a binary assertion")
        if "cost_per_success" in metrics or "cost" in row:
            if not _finite_number(row.get("cost")) or row["cost"] < 0:
                problems.append(f"{identity}: invalid cost")
        tags = row.get("slices", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            problems.append(f"{identity}: invalid slice tags")
    if not problems:
        k_values = set(spec.get("pass_k", []))
        for metric in metrics:
            match = re.fullmatch(r"pass_(?:at|hat)_(\d+)", metric)
            if match:
                k_values.add(int(match[1]))
        try:
            recomputed = aggregate([{**row, "cost": row.get("cost", 0.0)} for row in rows],
                                   sorted(row_metrics), k_values=sorted(k_values))
        except (ValueError, TypeError, OverflowError) as error:
            return [f"{name}: cannot recompute metrics: {error}"]
        for metric, value in metrics.items():
            if metric in recomputed and (not _finite_number(recomputed[metric])
                                        or not math.isclose(value, recomputed[metric], rel_tol=1e-9, abs_tol=1e-4)):
                problems.append(f"{metric}: summary disagrees with row aggregates")
    return [f"{name}: {problem}" for problem in problems]


def _ratchet_thresholds(current: dict, previous: dict, label: str) -> list[str]:
    problems = []
    for bound in ("min", "max", "max_increase"):
        if bound not in previous:
            continue
        if not _finite_number(current.get(bound)):
            problems.append(f"ratchet {label}: removed or invalid {bound}")
        elif ((bound == "min" and current[bound] < previous[bound])
              or (bound != "min" and current[bound] > previous[bound])):
            problems.append(f"ratchet {label}: loosened {bound}")
    if previous.get("no_significant_drop") and not current.get("no_significant_drop"):
        problems.append(f"ratchet {label}: removed no_significant_drop")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = _report_problems(pr, spec, "PR") + _report_problems(base, base_spec or spec, "baseline")
    if not problems:
        if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
            problems.append("eval_set_sha differs from baseline")
        pr_pairs = Counter((row["item_id"], row["seed"]) for row in pr["rows"])
        base_pairs = Counter((row["item_id"], row["seed"]) for row in base["rows"])
        if pr_pairs != base_pairs:
            problems.append("PR item/seed coverage differs from baseline")
        baseline_tags = {(row["item_id"], row["seed"]): set(row.get("slices", [])) for row in base["rows"]}
        for row in pr["rows"]:
            pair = row["item_id"], row["seed"]
            if pair in baseline_tags and set(row.get("slices", [])) != baseline_tags[pair]:
                problems.append(f"{pair}: slice tags differ from baseline")
    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        for category in ("metrics", "slices"):
            current = {rule["id"] if category == "metrics" else (rule["name"], rule["metric"]): rule
                       for rule in spec.get(category, [])}
            for previous in base_spec.get(category, []):
                key = previous["id"] if category == "metrics" else (previous["name"], previous["metric"])
                label = f"{category}/{key}"
                if key not in current:
                    problems.append(f"ratchet {label}: removed rule")
                    continue
                rule = current[key]
                if previous.get("blocking") and not rule.get("blocking"):
                    problems.append(f"ratchet {label}: disabled blocking")
                before = previous.get("threshold", {}) if category == "metrics" else previous
                after = rule.get("threshold", {}) if category == "metrics" else rule
                problems += _ratchet_thresholds(after, before, label)
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bootstrap = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        identifier = f"slice:{name}/{metric}"
        current = per_item(pr, metric, slice_name=name)
        baseline = per_item(base, metric, slice_name=name)
        value = sum(current.values()) / len(current) if current else None
        failed = value is None or current.keys() != baseline.keys()
        note = "missing or unmatched slice items" if failed else ""
        if value is not None and "min" in rule and value < rule["min"]:
            failed = True
        if rule.get("no_significant_drop") and current and current.keys() == baseline.keys():
            keys = sorted(current)
            try:
                delta, low, high = stats.paired_bootstrap(
                    [current[key] for key in keys], [baseline[key] for key in keys],
                    n_resamples=bootstrap.get("n_resamples", 1000),
                    rng=bootstrap.get("rng", 2027), confidence=bootstrap.get("confidence", 0.95),
                )
                note = f"Δ {delta:+.3f} CI [{low:+.3f}, {high:+.3f}]"
                failed = failed or high < 0
            except ValueError as error:
                failed = True
                note = f"slice CI unavailable: {error}"
        if failed and rule.get("blocking"):
            blocked.append(identifier)
        verdict = "ok"
        if failed:
            verdict = "BLOCK" if rule.get("blocking") else "warn"
        lines.append(f"  {identifier:<38} {value!s:<8} {note:<36} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    if blocked == ["integrity"]:
        print("gate: INTEGRITY validation failed")
    else:
        print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
