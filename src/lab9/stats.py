"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge must have the same number of labels")
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    outcomes = {
        (POS, POS): "tp",
        ("PASS", POS): "fp",
        (POS, "PASS"): "fn",
        ("PASS", "PASS"): "tn",
    }
    for actual, predicted in zip(human, judge):
        if actual not in ("PASS", POS) or predicted not in ("PASS", POS):
            raise ValueError("labels must be PASS or FAIL")
        counts[outcomes[actual, predicted]] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    counts = confusion(human, judge)
    predicted_failures = counts["tp"] + counts["fp"]
    actual_failures = counts["tp"] + counts["fn"]
    precision = counts["tp"] / predicted_failures if predicted_failures else 0.0
    recall = counts["tp"] / actual_failures if actual_failures else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    counts = confusion(human, judge)
    n = len(human)
    if n == 0:
        raise ValueError("kappa is undefined for empty labels")
    observed = (counts["tp"] + counts["tn"]) / n
    human_fail_rate = (counts["tp"] + counts["fn"]) / n
    judge_fail_rate = (counts["tp"] + counts["fp"]) / n
    expected = (human_fail_rate * judge_fail_rate
                + (1 - human_fail_rate) * (1 - judge_fail_rate))
    if expected == 1:
        raise ValueError("kappa is undefined when chance agreement is 1")
    return (observed - expected) / (1 - expected)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    rates = (observed_rate, sensitivity, specificity)
    if any(not math.isfinite(rate) or not 0 <= rate <= 1 for rate in rates):
        raise ValueError("rates must be finite values between 0 and 1")
    denominator = sensitivity + specificity - 1
    if denominator <= 0:
        raise ValueError("Rogan-Gladen requires sensitivity + specificity > 1")
    corrected = (observed_rate + specificity - 1) / denominator
    return min(1.0, max(0.0, corrected))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    first = np.asarray(a, dtype=float)
    second = np.asarray(b, dtype=float)
    if first.ndim != 1 or second.ndim != 1 or len(first) != len(second) or len(first) == 0:
        raise ValueError("paired samples must be nonempty, one-dimensional and equal in length")
    if not np.isfinite(first).all() or not np.isfinite(second).all():
        raise ValueError("paired samples must contain only finite values")
    if not isinstance(n_resamples, int) or n_resamples <= 0 or not 0 < confidence < 1:
        raise ValueError("n_resamples must be a positive integer and confidence must be between 0 and 1")
    if np.array_equal(first, second):
        return 0.0, 0.0, 0.0
    if len(first) < 2:
        raise ValueError("bootstrap requires at least two paired observations")

    def mean_difference(x, y, axis=-1):
        return np.mean(x - y, axis=axis)

    result = bootstrap(
        (first, second), mean_difference, paired=True, method="percentile",
        n_resamples=n_resamples, confidence_level=confidence,
        rng=np.random.default_rng(rng),
    )
    return (float(np.mean(first - second)),
            float(result.confidence_interval.low), float(result.confidence_interval.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
