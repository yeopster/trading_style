"""Leakage-aware cross-validation for overlapping trade labels.

* Purging: drop training samples whose [t0, t1] interval overlaps the test fold.
* Embargo: also drop training samples starting within `embargo` after the fold.
* Walk-forward: training data strictly precedes the test fold (deployment-like).
* CPCV: combinatorial purged CV (AFML ch.12) for a distribution of OOS paths.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterator

import numpy as np
import pandas as pd


def _purge(train_idx: np.ndarray, t0: pd.Index, t1: pd.Series, test_idx: np.ndarray,
           embargo: pd.Timedelta) -> np.ndarray:
    test_start = t0[test_idx].min()
    test_end = t1.iloc[test_idx].max() + embargo
    tr_t0 = t0[train_idx]
    tr_t1 = t1.iloc[train_idx].to_numpy()
    overlap = (tr_t0 <= test_end) & (tr_t1 >= test_start)
    return train_idx[~np.asarray(overlap)]


def walk_forward_splits(events: pd.DataFrame, n_splits: int, embargo: pd.Timedelta,
                        min_train: int = 100) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window walk-forward over events sorted by t0."""
    n = len(events)
    folds = np.array_split(np.arange(n), n_splits + 1)
    t0, t1 = events.index, events["t1"]
    for k in range(1, len(folds)):
        test = folds[k]
        train = _purge(np.concatenate(folds[:k]), t0, t1, test, embargo)
        if len(train) >= min_train and len(test):
            yield train, test


def cpcv_splits(events: pd.DataFrame, n_groups: int = 6, k_test: int = 2,
                embargo: pd.Timedelta = pd.Timedelta(0)) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    n = len(events)
    groups = np.array_split(np.arange(n), n_groups)
    t0, t1 = events.index, events["t1"]
    for test_groups in combinations(range(n_groups), k_test):
        test = np.concatenate([groups[g] for g in test_groups])
        train = np.arange(n)
        for g in test_groups:
            train = _purge(np.setdiff1d(train, test), t0, t1, groups[g], embargo)
        yield train, test
