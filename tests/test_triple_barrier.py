import numpy as np
import pandas as pd

from xauquant.labeling.triple_barrier import triple_barrier


def bars(rows):
    idx = pd.date_range("2021-01-04", periods=len(rows), freq="15min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


def run(df, side=1, tp=2.0, sl=1.0, max_bars=10):
    setups = pd.Series([side], index=df.index[:1])
    atr = pd.Series(1.0, index=df.index)
    return triple_barrier(df, setups, atr, tp, sl, max_bars).iloc[0]


def test_tp_hit():
    df = bars([[100, 100, 100, 100], [100, 101, 99.5, 101], [101, 102.5, 100.5, 102]])
    r = run(df)
    assert r.outcome == "tp" and r.label == 1 and np.isclose(r.r_gross, 2.0)
    assert r.entry_time == df.index[1]  # next bar open, not signal bar


def test_sl_hit_short():
    df = bars([[100, 100, 100, 100], [100, 100.5, 99.8, 100.2], [100.2, 101.2, 100, 101]])
    r = run(df, side=-1)
    assert r.outcome == "sl" and r.label == 0 and np.isclose(r.r_gross, -1.0)


def test_same_bar_ambiguity_is_sl():
    df = bars([[100, 100, 100, 100], [100, 102.5, 98.5, 100]])
    r = run(df)
    assert r.outcome == "sl"


def test_gap_through_stop_fills_at_open():
    df = bars([[100, 100, 100, 100], [100, 100.2, 99.9, 100], [98, 98.5, 97.5, 98]])
    r = run(df)
    assert r.outcome == "sl" and np.isclose(r.exit, 98) and r.r_gross < -1


def test_time_barrier():
    df = bars([[100, 100, 100, 100]] + [[100, 100.5, 99.5, 100.3]] * 5)
    r = run(df, max_bars=3)
    assert r.outcome == "time" and r.bars_held == 3 and np.isclose(r.r_gross, 0.3)


def test_random_entries_have_no_edge_with_symmetric_barriers(m15):
    from xauquant.features.indicators import atr
    rng = np.random.default_rng(0)
    idx = m15.index[100:-100][rng.choice(len(m15) - 200, 1500, replace=False)]
    setups = pd.Series(rng.choice([-1, 1], len(idx)), index=idx).sort_index()
    ev = triple_barrier(m15, setups, atr(m15, 14), 1.0, 1.0, 10_000)
    se = ev.r_gross.std() / np.sqrt(len(ev))
    assert abs(ev.r_gross.mean()) < 3 * se + 0.02
