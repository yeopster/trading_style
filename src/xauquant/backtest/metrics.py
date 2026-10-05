"""Trade-level performance metrics. Returns are in R (multiples of initial risk)
on a fixed-fractional account risking `risk_pct` per trade."""
from __future__ import annotations

import numpy as np
import pandas as pd


def equity_curve(r: pd.Series, risk_pct: float = 0.01) -> pd.Series:
    return (1 + risk_pct * r).cumprod()


def max_drawdown(eq: pd.Series) -> float:
    return float((eq / eq.cummax() - 1).min()) if len(eq) else 0.0


def summarize(trades: pd.DataFrame, r_col: str = "r_net", risk_pct: float = 0.01) -> dict:
    if trades.empty:
        return {"n_trades": 0}
    r = trades[r_col]
    eq = equity_curve(r, risk_pct)
    eq.index = trades["t1"].to_numpy()
    years = max((trades["t1"].max() - trades.index.min()).days / 365.25, 1e-9)
    daily = eq.groupby(eq.index.normalize()).last().pct_change().dropna()
    downside = daily[daily < 0].std()
    mdd = max_drawdown(eq)
    cagr = eq.iloc[-1] ** (1 / years) - 1
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    return {
        "n_trades": int(len(r)),
        "trades_per_year": float(len(r) / years),
        "total_return": float(eq.iloc[-1] - 1),
        "cagr": float(cagr),
        "sharpe": float(daily.mean() / daily.std() * np.sqrt(252)) if daily.std() > 0 else 0.0,
        "sortino": float(daily.mean() / downside * np.sqrt(252)) if downside and downside > 0 else 0.0,
        "max_drawdown": mdd,
        "calmar": float(cagr / abs(mdd)) if mdd < 0 else float("inf"),
        "win_rate": float((r > 0).mean()),
        "profit_factor": float(wins / losses) if losses > 0 else float("inf"),
        "expectancy_r": float(r.mean()),
        "expectancy_r_gross": float(trades["r_gross"].mean()) if "r_gross" in trades else None,
        "avg_bars_held": float(trades["bars_held"].mean()),
    }


def breakdown(trades: pd.DataFrame, by: pd.Series | str, r_col: str = "r_net") -> pd.DataFrame:
    key = trades[by] if isinstance(by, str) else by
    g = trades.groupby(key)[r_col]
    return pd.DataFrame({"n": g.size(), "expectancy_r": g.mean(), "win_rate": g.apply(lambda x: (x > 0).mean()),
                         "sum_r": g.sum()})


def bootstrap_expectancy(r: pd.Series, n: int = 2000, seed: int = 0) -> dict:
    """Bootstrap CI for mean R and P(mean R <= 0)."""
    rng = np.random.default_rng(seed)
    x = r.to_numpy()
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return {"exp_r_p05": float(np.percentile(means, 5)), "exp_r_p95": float(np.percentile(means, 95)),
            "p_exp_le_0": float((means <= 0).mean())}
