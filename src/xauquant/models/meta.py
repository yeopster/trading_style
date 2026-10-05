"""Meta-model: P(setup succeeds | features at signal time).

LightGBM baseline, with a plain logistic-regression benchmark it must beat.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


def make_model(kind: str, params: dict | None = None, seed: int = 7):
    if kind == "lgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(random_state=seed, verbose=-1, **(params or {}))
    if kind == "logit":
        return make_pipeline(SimpleImputer(), StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))
    raise ValueError(kind)


def classification_report(y: np.ndarray, p: np.ndarray) -> dict:
    out = {"n": int(len(y)), "base_rate": float(np.mean(y)), "brier": float(brier_score_loss(y, p))}
    if len(np.unique(y)) == 2:
        out["auc"] = float(roc_auc_score(y, p))
        out["log_loss"] = float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)))
    return out


def oos_predictions(X: pd.DataFrame, y: pd.Series, splits, kind: str, params: dict | None = None) -> pd.Series:
    """Out-of-fold probabilities: each prediction comes from a model that never
    saw that sample (or any sample overlapping it, thanks to purging)."""
    pred = pd.Series(np.nan, index=X.index)
    for train, test in splits:
        m = make_model(kind, params)
        m.fit(X.iloc[train], y.iloc[train])
        pred.iloc[test] = m.predict_proba(X.iloc[test])[:, 1]
    return pred
