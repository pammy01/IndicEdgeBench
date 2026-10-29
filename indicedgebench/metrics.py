"""Statistics: accuracy with bootstrap CIs, paired deltas vs. a baseline, and flip rates."""

from __future__ import annotations

import numpy as np


def bootstrap_ci(correct, n_resamples: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Percentile bootstrap CI for the mean of a 0/1 vector."""
    x = np.asarray(correct, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), size=(n_resamples, len(x)))].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def paired_delta(correct_a, correct_b, n_resamples: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Accuracy(a) - accuracy(b) on the same items, with a paired bootstrap CI.

    Resampling items (not configs) keeps the pairing, so item difficulty cancels out.
    """
    a = np.asarray(correct_a, dtype=float)
    b = np.asarray(correct_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("paired_delta needs results on the same items")
    d = a - b
    lo, hi = bootstrap_ci(d, n_resamples, seed, alpha)
    return float(d.mean()), lo, hi


def flip_rate(pred_a, pred_b) -> float:
    """Fraction of items whose predicted answer changes between two configs.

    Accuracy can stay flat while many answers flip (errors fixed and introduced in equal
    numbers); the flip rate exposes that hidden instability under quantization.
    """
    a, b = np.asarray(pred_a), np.asarray(pred_b)
    return float((a != b).mean()) if len(a) else float("nan")
