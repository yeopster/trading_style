"""Promotion gates. A hypothesis survives development testing only if EVERY gate
passes. Thresholds are fixed here, in code, before experiments are run;
changing them requires a commit that explains why (see CLAUDE.md)."""
from __future__ import annotations

GATES_DEV = {
    # name: (metric path, comparator, threshold)
    "enough_trades":        ("filtered.n_trades", ">=", 100),
    "positive_expectancy":  ("filtered.expectancy_r", ">", 0.0),
    "expectancy_ci":        ("filtered_bootstrap.p_exp_le_0", "<=", 0.05),
    "profit_factor":        ("filtered.profit_factor", ">=", 1.2),
    "beats_baseline":       ("uplift.expectancy_r", ">", 0.0),
    "model_has_signal":     ("model.lgbm.auc", ">=", 0.53),
    "fold_consistency":     ("folds.frac_positive", ">=", 0.6),
    "drawdown":             ("filtered.max_drawdown", ">=", -0.25),
    "cost_stress_2x":       ("filtered_2x_costs.expectancy_r", ">", 0.0),
    "deflated_sharpe":      ("filtered_dsr", ">=", 0.90),
}

# Applied to paper trading before any live capital (checked by hand / report).
GATES_PAPER = {
    "min_weeks": 8,
    "min_trades": 40,
    "expectancy_within_dev_ci": True,
    "max_slippage_vs_model_px": 0.15,
}


def _get(metrics: dict, path: str):
    cur = metrics
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def evaluate_gates(metrics: dict, gates: dict = GATES_DEV) -> tuple[dict, bool]:
    results = {}
    for name, (path, op, thr) in gates.items():
        v = _get(metrics, path)
        ok = v is not None and (v >= thr if op == ">=" else v > thr if op == ">" else v <= thr)
        results[name] = {"value": v, "rule": f"{op} {thr}", "pass": bool(ok)}
    return results, all(r["pass"] for r in results.values())
