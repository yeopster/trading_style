"""Build the M15 feature matrix (D1/H4 context + M15 state). All features are
known at the close of the M15 bar they are indexed by."""
from __future__ import annotations

import numpy as np
import pandas as pd

from xauquant.data.loader import resample_ohlc
from xauquant.features import indicators as ind
from xauquant.features.htf import align_htf


def _tf_block(df: pd.DataFrame, ema_n: int, atr_n: int) -> pd.DataFrame:
    e = ind.ema(df["close"], ema_n)
    a = ind.atr(df, atr_n)
    return pd.DataFrame({
        "trend": np.sign(df["close"] - e),
        "ema_slope": e.diff(3) / a,
        "dist_ema_atr": (df["close"] - e) / a,
        "atr": a,
        "adx": ind.adx(df, 14),
        "ret_1": df["close"].pct_change(),
    }, index=df.index)


def build_features(m15: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    s = cfg["strategy"]
    lab = cfg["labels"]
    c = m15["close"]

    f = pd.DataFrame(index=m15.index)
    f = f.join(ind.bollinger(c, s["bb_period"], s["bb_std"]))
    f["lwma5_high"] = ind.lwma(m15["high"], s["lwma_fast"])
    f["lwma5_low"] = ind.lwma(m15["low"], s["lwma_fast"])
    f["lwma10_high"] = ind.lwma(m15["high"], s["lwma_slow"])
    f["lwma10_low"] = ind.lwma(m15["low"], s["lwma_slow"])
    f["ema_trend"] = ind.ema(c, s["ema_trend"])
    f["atr"] = ind.atr(m15, lab["atr_period"])
    f["atr_pctile"] = ind.rolling_percentile(f["atr"], 96 * 20)
    f["bb_width_pctile"] = ind.rolling_percentile(f["bb_width"], 96 * 20)
    f["rsi"] = ind.rsi(c, 14)
    f["adx"] = ind.adx(m15, 14)
    f["ema_slope"] = f["ema_trend"].diff(4) / f["atr"]
    f["dist_ema_atr"] = (c - f["ema_trend"]) / f["atr"]
    f["lwma5_slope"] = f["lwma5_high"].add(f["lwma5_low"]).diff(2) / (2 * f["atr"])
    f["lwma10_slope"] = f["lwma10_high"].add(f["lwma10_low"]).diff(2) / (2 * f["atr"])
    f["lwma_to_bbmid_atr"] = ((f["lwma5_high"] + f["lwma5_low"]) / 2 - f["bb_mid"]) / f["atr"]
    for k in (1, 4, 16):
        f[f"ret_{k}"] = c.pct_change(k)

    # Session / calendar (UTC). Adjust if your broker data is not UTC.
    hour = m15.index.hour
    f["hour"] = hour
    f["dow"] = m15.index.dayofweek
    f["sess_asia"] = ((hour >= 0) & (hour < 7)).astype(int)
    f["sess_london"] = ((hour >= 7) & (hour < 13)).astype(int)
    f["sess_ny"] = ((hour >= 13) & (hour < 21)).astype(int)

    # Distance to the current UTC day's running high/low (causal: expanding within day).
    day = m15.index.normalize()
    f["dist_day_high_atr"] = (m15.groupby(day)["high"].cummax() - c) / f["atr"]
    f["dist_day_low_atr"] = (c - m15.groupby(day)["low"].cummin()) / f["atr"]
    f["dist_swing_high_atr"] = (m15["high"].rolling(48).max() - c) / f["atr"]
    f["dist_swing_low_atr"] = (c - m15["low"].rolling(48).min()) / f["atr"]

    if "spread" in m15.columns:
        f["spread"] = m15["spread"]

    for rule, name in (("4h", "h4"), ("1D", "d1")):
        htf = resample_ohlc(m15, rule)
        block = _tf_block(htf, s["htf_ema"], lab["atr_period"])
        f = f.join(align_htf(m15, block, rule, prefix=f"{name}_"))

    f["htf_agree"] = (f["h4_trend"] == f["d1_trend"]).astype(int)
    return f


# Columns used as model inputs (raw price levels are excluded: non-stationary).
MODEL_FEATURES = [
    "bb_width", "bb_pctb", "atr_pctile", "bb_width_pctile", "rsi", "adx", "ema_slope",
    "dist_ema_atr", "lwma5_slope", "lwma10_slope", "lwma_to_bbmid_atr", "ret_1", "ret_4",
    "ret_16", "hour", "dow", "sess_asia", "sess_london", "sess_ny", "dist_day_high_atr",
    "dist_day_low_atr", "dist_swing_high_atr", "dist_swing_low_atr", "h4_trend",
    "h4_ema_slope", "h4_dist_ema_atr", "h4_adx", "d1_trend", "d1_ema_slope",
    "d1_dist_ema_atr", "d1_adx", "htf_agree",
]
