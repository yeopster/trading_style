"""BBMA setup generator — the *primary* model in the meta-labelling stack.

PLACEHOLDER RULES. These approximate a BBMA "re-entry" in the direction of the
higher-timeframe trend. Replace `generate_setups` with your exact discretionary
rules before drawing any conclusion: the meta-model only ever answers "given
that MY strategy fired, is this setup likely to work?".

Long re-entry (short is the mirror image):
  1. Context: H4 and D1 closes are above their EMAs (htf bias up) and the M15
     close is above the M15 EMA trend filter.
  2. Pullback: within the last `lookback` bars price traded down to the BB mid.
  3. Trigger: this bar closes back above LWMA5(high) after the previous bar
     closed at or below it.
Decision is made at the close of the signal bar; entry is the NEXT bar's open.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_setups(m15: pd.DataFrame, f: pd.DataFrame, lookback: int = 3) -> pd.Series:
    """Return a Series of {+1 long, -1 short} indexed by signal-bar time."""
    c = m15["close"]
    bias_up = (f["h4_trend"] > 0) & (f["d1_trend"] > 0) & (c > f["ema_trend"])
    bias_dn = (f["h4_trend"] < 0) & (f["d1_trend"] < 0) & (c < f["ema_trend"])

    touched_mid_dn = (m15["low"] <= f["bb_mid"]).rolling(lookback, min_periods=1).max().astype(bool)
    touched_mid_up = (m15["high"] >= f["bb_mid"]).rolling(lookback, min_periods=1).max().astype(bool)

    cross_up = (c > f["lwma5_high"]) & (c.shift(1) <= f["lwma5_high"].shift(1))
    cross_dn = (c < f["lwma5_low"]) & (c.shift(1) >= f["lwma5_low"].shift(1))

    side = pd.Series(0, index=m15.index, dtype=int)
    side[bias_up & touched_mid_dn & cross_up] = 1
    side[bias_dn & touched_mid_up & cross_dn] = -1
    valid = f[["bb_mid", "lwma5_high", "ema_trend", "h4_trend", "d1_trend", "atr"]].notna().all(axis=1)
    return side[(side != 0) & valid]
