"""Generate a synthetic XAUUSD-like M15 series for smoke tests ONLY.
It has no edge by construction: any 'alpha' found on it is a pipeline bug."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def synthetic_m15(start="2018-01-01", end="2024-06-30", seed=42, s0=1300.0, sub=15) -> pd.DataFrame:
    """M15 bars aggregated from a 1-minute driftless random walk with GARCH-style
    volatility clustering and intraday seasonality. Building bars from a fine path
    keeps high/low consistent with a martingale, so TP/SL labels carry no edge."""
    idx = pd.date_range(start, end, freq="15min", tz="UTC")
    idx = idx[idx.dayofweek < 5]
    rng = np.random.default_rng(seed)
    n = len(idx)
    vol = np.empty(n)
    v = 0.0012
    z = rng.standard_normal(n)
    for i in range(n):
        if i:
            v = np.sqrt(1e-8 + 0.05 * (v * z[i - 1]) ** 2 + 0.94 * v ** 2)
        vol[i] = v
    season = 1 + 0.6 * np.isin(idx.hour, range(7, 17))
    step_sd = (vol * season / np.sqrt(sub))[:, None]
    steps = rng.standard_normal((n, sub)) * step_sd
    log_path = np.log(s0) + np.cumsum(steps.ravel()).reshape(n, sub)
    prev_close = np.r_[np.log(s0), log_path[:-1, -1]]
    px = np.exp(np.column_stack([prev_close, log_path]))
    return pd.DataFrame({"time": idx, "open": px[:, 0], "high": px.max(axis=1), "low": px.min(axis=1),
                         "close": px[:, -1], "tick_volume": rng.integers(200, 3000, n),
                         "spread": 0.25}).round({"open": 3, "high": 3, "low": 3, "close": 3})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw/XAUUSD_M15_synthetic.csv")
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    synthetic_m15().to_csv(a.out, index=False)
    print(f"wrote {a.out}")
