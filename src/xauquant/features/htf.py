"""Align higher-timeframe features onto M15 bars without look-ahead.

Bars are indexed by OPEN time. A bar opened at t on timeframe `rule` is only
complete at t + rule. An M15 decision made at the close of bar s (s + 15min)
may use an HTF bar only if t + rule <= s + 15min.
"""
from __future__ import annotations

import pandas as pd


def align_htf(base: pd.DataFrame, htf: pd.DataFrame, htf_rule: str, base_rule: str = "15min",
              prefix: str = "") -> pd.DataFrame:
    left = pd.DataFrame({"_known": base.index + pd.Timedelta(base_rule)})
    right = htf.add_prefix(prefix).reset_index(drop=True)
    right["_known"] = htf.index + pd.Timedelta(htf_rule)
    merged = pd.merge_asof(left, right, on="_known", direction="backward", allow_exact_matches=True)
    merged.index = base.index
    return merged.drop(columns="_known")
