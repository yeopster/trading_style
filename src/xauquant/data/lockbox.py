"""The lockbox: the untouched out-of-sample period.

All research code must obtain data through `dev_slice`. `open_lockbox` exists
for the final, one-shot evaluation of a frozen hypothesis and records every
opening in `experiments/lockbox_log.jsonl` so that peeking is auditable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from xauquant.config import ROOT

LOG = ROOT / "experiments" / "lockbox_log.jsonl"


class LockboxViolation(RuntimeError):
    pass


def _ts(value: str, index: pd.DatetimeIndex) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if index.tz is not None and ts.tz is None:
        ts = ts.tz_localize(index.tz)
    return ts


def dev_slice(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Development data only. Also asserts the configured split is sane."""
    dev_end = _ts(cfg["splits"]["dev_end"], df.index)
    lock_start = _ts(cfg["splits"]["lockbox_start"], df.index)
    if lock_start <= dev_end:
        raise LockboxViolation("lockbox_start must be after dev_end")
    return df.loc[:dev_end]


def assert_no_lockbox(index: pd.DatetimeIndex, cfg: dict) -> None:
    lock_start = _ts(cfg["splits"]["lockbox_start"], index)
    if len(index) and index.max() >= lock_start:
        raise LockboxViolation(f"data reaches into the lockbox (max {index.max()} >= {lock_start})")


def open_lockbox(df: pd.DataFrame, cfg: dict, *, hypothesis_id: str, frozen_commit: str,
                 reason: str, log_path: Path = LOG) -> pd.DataFrame:
    """Return lockbox data for a one-shot final test. Refuses a second opening for
    the same hypothesis: any change after seeing lockbox results needs a new ID."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            if line.strip() and json.loads(line)["hypothesis_id"] == hypothesis_id:
                raise LockboxViolation(
                    f"lockbox already opened for {hypothesis_id}; register a new hypothesis instead")
    entry = {
        "hypothesis_id": hypothesis_id,
        "frozen_commit": frozen_commit,
        "reason": reason,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return df.loc[_ts(cfg["splits"]["lockbox_start"], df.index):]
