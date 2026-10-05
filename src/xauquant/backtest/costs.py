from __future__ import annotations

import pandas as pd


def apply_costs(trades: pd.DataFrame, costs: dict, spread_col: pd.Series | None = None) -> pd.DataFrame:
    """Net R per trade after spread, commission and slippage (all in price units)."""
    t = trades.copy()
    spread = spread_col.reindex(t["entry_time"]).to_numpy() if spread_col is not None else costs["spread"]
    t["cost_px"] = spread + costs["commission"] + 2 * costs["slippage"]
    t["r_net"] = t["r_gross"] - t["cost_px"] / t["risk"]
    return t
