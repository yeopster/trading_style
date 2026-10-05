"""Run the H02 meta-labelling experiment on development data and log it.

    python scripts/run_experiment.py --hypothesis H02 --csv data/raw/XAUUSD_M15.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xauquant.config import ROOT, load_config  # noqa: E402
from xauquant.data.loader import load_ohlc_csv  # noqa: E402
from xauquant.data.lockbox import dev_slice  # noqa: E402
from xauquant.experiments import meta_label, registry  # noqa: E402
from xauquant.experiments.gates import evaluate_gates  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypothesis", default="H02")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--notes", default="")
    ap.add_argument("--no-log", action="store_true", help="dry run: do not write to the registry")
    a = ap.parse_args()

    cfg = load_config(a.config)
    m15 = dev_slice(load_ohlc_csv(a.csv or ROOT / cfg["data"]["m15_csv"], cfg["data"]["timezone"]), cfg)

    con = registry.connect()
    if not a.no_log:
        registry.register_from_file(con, a.hypothesis)
    metrics, trades = meta_label.run(m15, cfg, n_prior_trials=registry.n_trials(con))
    if "error" in metrics:
        print(metrics["error"])
        verdict, gates = "error", {}
    else:
        gates, passed = evaluate_gates(metrics)
        verdict = "survive" if passed else "reject"

    data_range = f"{m15.index.min()} .. {m15.index.max()}"
    if not a.no_log:
        run_id = registry.log_run(con, a.hypothesis, cfg, metrics, gates, verdict, data_range, a.notes)
        out = ROOT / "experiments" / "runs" / f"{run_id:04d}_{a.hypothesis}"
        out.mkdir(parents=True, exist_ok=True)
        (out / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
        (out / "gates.json").write_text(json.dumps(gates, indent=2, default=str))
        if len(trades):
            trades.to_csv(out / "oos_trades.csv")
        print(f"run {run_id} logged -> {out}")

    for k in ("baseline", "filtered", "filtered_2x_costs"):
        if k in metrics:
            s = metrics[k]
            print(f"{k:>18}: n={s.get('n_trades')} expR={s.get('expectancy_r', 0):+.3f} "
                  f"PF={s.get('profit_factor', 0):.2f} MDD={s.get('max_drawdown', 0):.1%} "
                  f"Sharpe={s.get('sharpe', 0):.2f}")
    if "model" in metrics:
        print(f"{'AUC':>18}: lgbm={metrics['model']['lgbm'].get('auc', float('nan')):.3f} "
              f"logit={metrics['model']['logit'].get('auc', float('nan')):.3f}")
    for name, g in gates.items():
        print(f"  [{'PASS' if g['pass'] else 'FAIL'}] {name}: {g['value']} ({g['rule']})")
    print(f"VERDICT: {verdict.upper()}")


if __name__ == "__main__":
    main()
