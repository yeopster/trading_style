"""Triple-barrier labels (Lopez de Prado, AFML ch.3) for strategy setups.

For each setup: enter at the next bar's open; TP/SL set as ATR multiples
from the entry; vertical barrier after `max_bars`. If TP and SL are both
inside the same bar we cannot know the order from OHLC, so we assume the SL
hit first (pessimistic). The label is 1 iff TP was hit first.
`t1` (exit time) is kept for purging overlapping samples during CV.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def triple_barrier(m15: pd.DataFrame, setups: pd.Series, atr: pd.Series, tp_atr: float,
                   sl_atr: float, max_bars: int) -> pd.DataFrame:
    idx = m15.index
    o, h, l, c = (m15[k].to_numpy() for k in ("open", "high", "low", "close"))
    pos = idx.get_indexer(setups.index)
    rows = []
    for t, p, side in zip(setups.index, pos, setups.to_numpy()):
        e = p + 1
        if e >= len(idx):
            continue
        risk = sl_atr * atr.iloc[p]
        if not np.isfinite(risk) or risk <= 0:
            continue
        entry = o[e]
        tp = entry + side * tp_atr * atr.iloc[p]
        sl = entry - side * risk
        last = min(e + max_bars - 1, len(idx) - 1)
        exit_i, exit_px, outcome = last, c[last], "time"
        for j in range(e, last + 1):
            hit_sl = l[j] <= sl if side > 0 else h[j] >= sl
            hit_tp = h[j] >= tp if side > 0 else l[j] <= tp
            if hit_sl:
                # gap through the stop fills at the open, otherwise at the stop
                gap = (o[j] < sl) if side > 0 else (o[j] > sl)
                exit_i, exit_px, outcome = j, (o[j] if gap and j > e else sl), "sl"
                break
            if hit_tp:
                exit_i, exit_px, outcome = j, tp, "tp"
                break
        rows.append({
            "t0": t, "entry_time": idx[e], "t1": idx[exit_i], "side": int(side),
            "entry": entry, "tp": tp, "sl": sl, "exit": exit_px, "outcome": outcome,
            "risk": risk, "r_gross": side * (exit_px - entry) / risk,
            "bars_held": exit_i - e + 1, "label": int(outcome == "tp"),
        })
    return pd.DataFrame(rows).set_index("t0") if rows else pd.DataFrame()
