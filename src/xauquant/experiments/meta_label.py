"""H02 — meta-labelling experiment, end to end, on DEVELOPMENT data only.

strategy setups -> triple-barrier labels -> purged walk-forward meta-model ->
filter at a pre-registered threshold -> net-of-cost backtest vs. unfiltered.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from xauquant.backtest.costs import apply_costs
from xauquant.backtest.metrics import bootstrap_expectancy, breakdown, summarize
from xauquant.data.lockbox import assert_no_lockbox
from xauquant.features.pipeline import MODEL_FEATURES, build_features
from xauquant.labeling.triple_barrier import triple_barrier
from xauquant.models.meta import classification_report, oos_predictions
from xauquant.strategy.bbma import generate_setups
from xauquant.validation.deflated_sharpe import deflated_sharpe
from xauquant.validation.purged import walk_forward_splits


def build_events(m15: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = build_features(m15, cfg)
    setups = generate_setups(m15, f)
    lab = cfg["labels"]
    ev = triple_barrier(m15, setups, f["atr"], lab["tp_atr"], lab["sl_atr"], lab["max_bars"])
    return ev, f


def run(m15_dev: pd.DataFrame, cfg: dict, n_prior_trials: int = 0) -> tuple[dict, pd.DataFrame]:
    assert_no_lockbox(m15_dev.index, cfg)
    ev, f = build_events(m15_dev, cfg)
    if ev.empty:
        return {"error": "no setups generated"}, ev

    X = f.loc[ev.index, MODEL_FEATURES].copy()
    X["side"] = ev["side"]
    y = ev["label"]
    v = cfg["validation"]
    embargo = pd.Timedelta(minutes=15 * v["embargo_bars"])
    splits = list(walk_forward_splits(ev, v["n_splits"], embargo, v["min_train_trades"]))
    if not splits:
        return {"error": f"not enough events ({len(ev)}) for walk-forward"}, ev

    ev["p_lgbm"] = oos_predictions(X, y, splits, "lgbm", cfg["meta_model"]["params"])
    ev["p_logit"] = oos_predictions(X, y, splits, "logit")
    ev["fold"] = np.nan
    for k, (_, test) in enumerate(splits):
        ev.iloc[test, ev.columns.get_loc("fold")] = k

    spread = m15_dev["spread"] if "spread" in m15_dev.columns else None
    costs = cfg["costs"]
    oos = apply_costs(ev[ev["p_lgbm"].notna()], costs, spread)
    oos2x = apply_costs(ev[ev["p_lgbm"].notna()], {k: 2 * v for k, v in costs.items()},
                        None if spread is None else 2 * spread)
    thr = cfg["meta_model"]["threshold"]
    take = oos["p_lgbm"] >= thr

    base_s, filt_s = summarize(oos), summarize(oos[take])
    per_fold = oos[take].groupby("fold")["r_net"].mean()
    metrics = {
        "n_events_total": int(len(ev)),
        "n_events_oos": int(len(oos)),
        "threshold": thr,
        "baseline": base_s,
        "filtered": filt_s,
        "filtered_2x_costs": summarize(oos2x[take]),
        "filtered_bootstrap": bootstrap_expectancy(oos.loc[take, "r_net"]) if take.sum() > 10 else {},
        "filtered_dsr": deflated_sharpe(oos.loc[take, "r_net"].to_numpy(), n_prior_trials + 1)
        if take.sum() > 10 else 0.0,
        "uplift": {"expectancy_r": filt_s.get("expectancy_r", 0) - base_s.get("expectancy_r", 0)},
        "model": {
            "lgbm": classification_report(oos["label"].to_numpy(), oos["p_lgbm"].to_numpy()),
            "logit": classification_report(oos["label"].to_numpy(), oos["p_logit"].to_numpy()),
        },
        "folds": {"expectancy_r": per_fold.round(4).to_dict(),
                  "frac_positive": float((per_fold > 0).mean()) if len(per_fold) else 0.0},
        "breakdowns": {
            "year": breakdown(oos[take], oos[take].index.year).round(4).to_dict("index"),
            "side": breakdown(oos[take], "side").round(4).to_dict("index"),
            "session_hour": breakdown(oos[take], pd.cut(oos[take].index.hour, [0, 7, 13, 21, 24],
                                                       right=False, labels=["asia", "london", "ny", "late"]))
            .round(4).to_dict("index"),
            "vol_regime": breakdown(oos[take], pd.qcut(f.loc[oos[take].index, "atr_pctile"], 3,
                                                       labels=["low", "mid", "high"], duplicates="drop"))
            .round(4).to_dict("index"),
            "h4_trend": breakdown(oos[take], f.loc[oos[take].index, "h4_trend"]).round(4).to_dict("index"),
        },
    }
    return metrics, oos
