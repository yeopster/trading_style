"""Probabilistic & Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014).

DSR discounts the observed Sharpe for the number of experiments tried — which
is why every run, including failures, must be logged in the registry.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats


def probabilistic_sharpe(returns: np.ndarray, sr_benchmark: float = 0.0) -> float:
    r = np.asarray(returns, dtype=float)
    n = len(r)
    if n < 3 or r.std(ddof=1) == 0:
        return 0.0
    sr = r.mean() / r.std(ddof=1)
    skew, kurt = stats.skew(r), stats.kurtosis(r, fisher=False)
    denom = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4 * sr ** 2, 1e-12))
    return float(stats.norm.cdf((sr - sr_benchmark) * math.sqrt(n - 1) / denom))


def expected_max_sharpe(n_trials: int, sr_var: float) -> float:
    """Expected maximum per-period SR among n_trials unskilled strategies."""
    if n_trials <= 1:
        return 0.0
    g = 0.5772156649
    z1 = stats.norm.ppf(1 - 1 / n_trials)
    z2 = stats.norm.ppf(1 - 1 / (n_trials * math.e))
    return float(math.sqrt(sr_var) * ((1 - g) * z1 + g * z2))


def deflated_sharpe(returns: np.ndarray, n_trials: int, sr_var: float | None = None) -> float:
    r = np.asarray(returns, dtype=float)
    if sr_var is None:
        # Fallback: variance of SR estimator under the null, ~1/(n-1)
        sr_var = 1 / max(len(r) - 1, 1)
    return probabilistic_sharpe(r, expected_max_sharpe(n_trials, sr_var))
