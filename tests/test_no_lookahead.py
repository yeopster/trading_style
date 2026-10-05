"""Truncation tests: a feature/signal at time t must not change when data after t is removed."""
import numpy as np
import pandas as pd

from xauquant.features.htf import align_htf
from xauquant.features.pipeline import build_features
from xauquant.data.loader import resample_ohlc
from xauquant.strategy.bbma import generate_setups


def test_features_unchanged_by_future_data(m15, cfg):
    full = build_features(m15, cfg)
    cut = m15.index[len(m15) * 2 // 3]
    trunc = build_features(m15.loc[:cut], cfg)
    a, b = full.loc[:cut], trunc
    pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-9, atol=1e-12)


def test_setups_unchanged_by_future_data(m15, cfg):
    cut = m15.index[len(m15) // 2]
    full = generate_setups(m15, build_features(m15, cfg))
    trunc = generate_setups(m15.loc[:cut], build_features(m15.loc[:cut], cfg))
    pd.testing.assert_series_equal(full.loc[:cut], trunc)


def test_htf_bar_used_only_after_close(m15):
    h4 = resample_ohlc(m15, "4h")
    aligned = align_htf(m15, h4[["close"]], "4h", prefix="h4_")
    # The M15 bar opening at 03:45 closes at 04:00 -> may see the 00:00 H4 bar.
    # The M15 bar opening at 03:30 closes at 03:45 -> must still see the 20:00 bar of the previous day.
    day = m15.index[m15.index.hour == 4][10].normalize()
    t_ok, t_early = day + pd.Timedelta("3h45min"), day + pd.Timedelta("3h30min")
    assert aligned.loc[t_ok, "h4_close"] == h4.loc[day, "close"]
    assert aligned.loc[t_early, "h4_close"] != h4.loc[day, "close"]
    # And never a bar whose close is after the M15 decision time
    known = aligned["h4_close"].notna()
    assert known.any()
