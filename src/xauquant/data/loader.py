"""Load and validate MT5-style OHLC exports and build higher timeframes."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OHLC = ["open", "high", "low", "close"]


def load_ohlc_csv(path: str | Path, tz: str = "UTC") -> pd.DataFrame:
    """Read an OHLC CSV with a time column. Accepts MT5 exports
    (`<DATE>`,`<TIME>` tab-separated) or a plain `time,open,high,low,close,...` file."""
    path = Path(path)
    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip("<>").lower() for c in df.columns]
    if "date" in df.columns and "time" in df.columns:
        df["time"] = df["date"].astype(str) + " " + df["time"].astype(str)
        df = df.drop(columns=["date"])
    if "vol" in df.columns and "volume" not in df.columns:
        df = df.rename(columns={"vol": "volume"})
    df["time"] = pd.to_datetime(df["time"])
    if df["time"].dt.tz is None:
        df["time"] = df["time"].dt.tz_localize(tz)
    df = df.set_index("time").sort_index()
    return validate_ohlc(df)


def validate_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in OHLC if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    if df.index.has_duplicates:
        df = df[~df.index.duplicated(keep="last")]
    bad = (df["high"] < df[["open", "close", "low"]].max(axis=1)) | (
        df["low"] > df[["open", "close", "high"]].min(axis=1)
    )
    if bad.any():
        raise ValueError(f"{int(bad.sum())} bars violate high/low bounds, first at {df.index[bad][0]}")
    return df


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample to a higher timeframe. Bars are labelled by their OPEN time, so a
    bar is only known after `index + rule`; see features.htf for safe alignment."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    for extra, how in (("tick_volume", "sum"), ("volume", "sum"), ("spread", "mean")):
        if extra in df.columns:
            agg[extra] = how
    out = df.resample(rule, label="left", closed="left").agg(agg)
    return out.dropna(subset=["open"])
