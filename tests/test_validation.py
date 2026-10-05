import numpy as np
import pandas as pd

from xauquant.validation.deflated_sharpe import deflated_sharpe, probabilistic_sharpe
from xauquant.validation.purged import cpcv_splits, walk_forward_splits


def events(n=600):
    t0 = pd.date_range("2021-01-01", periods=n, freq="1h", tz="UTC")
    t1 = t0 + pd.to_timedelta(np.random.default_rng(0).integers(1, 30, n), unit="h")
    return pd.DataFrame({"t1": t1}, index=t0)


def _no_overlap(ev, train, test, embargo):
    start, end = ev.index[test].min(), ev["t1"].iloc[test].max() + embargo
    tr0, tr1 = ev.index[train], ev["t1"].iloc[train]
    return not ((tr0 <= end) & (tr1.to_numpy() >= start)).any()


def test_walk_forward_is_purged_and_causal():
    ev = events()
    emb = pd.Timedelta("6h")
    splits = list(walk_forward_splits(ev, 5, emb, min_train=10))
    assert len(splits) == 5
    for train, test in splits:
        assert train.max() < test.min()
        assert _no_overlap(ev, train, test, emb)


def test_cpcv_is_purged():
    ev = events()
    splits = list(cpcv_splits(ev, 6, 2, pd.Timedelta("2h")))
    assert len(splits) == 15
    for train, test in splits:
        assert not set(train) & set(test)
        # purged against each contiguous test block
        for block in np.split(test, np.where(np.diff(test) != 1)[0] + 1):
            assert _no_overlap(ev, train, block, pd.Timedelta("2h"))


def test_dsr_penalises_many_trials():
    r = np.random.default_rng(1).normal(0.05, 1, 500)
    assert deflated_sharpe(r, 1000) < deflated_sharpe(r, 1) <= probabilistic_sharpe(r) + 1e-12
