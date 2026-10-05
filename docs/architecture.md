# V1 research architecture — XAUUSD BBMA + meta-labelling

## 1. Pipeline

```
 MT5 M15 export ──► loader.validate ──► dev_slice ───────────────┐      (lockbox: untouched)
                                         │                       │
                          resample H4 / D1 (open-time labelled)  │
                                         │                       │
                    features.pipeline (M15 + align_htf, causal)  │
                                         │                       │
                    strategy.bbma.generate_setups  (PRIMARY: side)
                                         │
                    labeling.triple_barrier (next-bar entry, TP/SL/time, SL-first)
                                         │
              validation.purged.walk_forward_splits (purge + embargo)
                                         │
                models.meta: LightGBM vs logistic benchmark ─► OOS P(success)
                                         │
                   threshold (pre-registered) ─► take / skip
                                         │
                 backtest.costs (spread + commission + slippage, 2x stress)
                                         │
       backtest.metrics + breakdowns + bootstrap + deflated Sharpe
                                         │
                  experiments.gates ─► verdict ─► experiments/registry.db
```

## 2. Data

| dataset | source | notes |
|---|---|---|
| XAUUSD M15 OHLC + spread | MT5 History Center export (or broker/Dukascopy) | the only required input; H4/D1 are resampled from it so that all timeframes share one clock |
| Tick / M1 (later) | Dukascopy / broker | for realistic same-bar TP/SL resolution and slippage estimation |
| Economic calendar (later) | e.g. Forex Factory export | news-window flag; spreads blow out around NFP/CPI/FOMC |
| DXY, US real yields (later) | FRED / broker | candidate regime features, D1 only |

Timezone: store UTC. If the broker server is UTC+2/+3, convert on load, otherwise session features and
D1 bars are wrong. Recommended split: dev = start..2022-12-31, lockbox = 2023-01-01..today (`config.yaml`).
Gold changed character after 2022 (central-bank buying, record highs), so the lockbox is a genuine regime test.

## 3. Storage schema

V1 keeps market data as CSV/Parquet files and the experiment registry in SQLite (`experiments/registry.db`,
schema in `src/xauquant/experiments/registry.py`):

- `hypotheses(hypothesis_id, title, statement, rationale, kill_criteria, status, created_at)`
- `runs(run_id, hypothesis_id, started_at, git_commit, git_dirty, data_range, config_json, metrics_json, gates_json, verdict, notes)`
- `experiments/lockbox_log.jsonl` — append-only audit log of every lockbox opening (committed to git).
- `experiments/runs/NNNN_HID/` — metrics.json, gates.json, oos_trades.csv per run (local).

Scale-up path: move bars to DuckDB/Parquet (`bars(symbol, tf, time, o, h, l, c, spread, volume)`),
set `MLFLOW_TRACKING_URI` to mirror runs into MLflow, keep SQLite as the source of truth for trial counts.

## 4. Features (all known at the M15 bar close)

M15: BB width / %B, ATR + ATR percentile, BB-width percentile, RSI, ADX, EMA slope & distance (in ATR),
LWMA5/10 slopes, LWMA-to-BB-mid distance, 1/4/16-bar returns, session flags, hour, day of week,
distance from UTC-day high/low and 48-bar swing high/low (in ATR), spread.
H4 and D1: trend sign vs EMA, EMA slope, distance from EMA, ADX — via `align_htf`, which only exposes a
higher-timeframe bar after it has closed. `tests/test_no_lookahead.py` enforces this by truncation.

## 5. Labels

Triple barrier per setup: entry = next bar open; TP = 2 ATR, SL = 1 ATR, vertical barrier 48 bars.
SL-first on same-bar ambiguity; stop gaps fill at the open. Label = TP hit first. `t1` (exit time) is kept
for purging. Gross R is recorded; net R is computed in the backtester so cost assumptions can be stressed.

## 6. Models

1. Logistic regression (benchmark — if LightGBM can't beat it, the extra complexity isn't earned).
2. LightGBM with conservative regularisation (`config.yaml: meta_model.params`).
Later: CatBoost/XGBoost comparison, isotonic calibration inside training folds, bet sizing from p.

## 7. Validation ladder

| stage | data | purpose | who may look |
|---|---|---|---|
| purged walk-forward | dev | model selection, all iteration | Claude + human |
| CPCV (`cpcv_splits`) | dev | distribution of OOS paths, robustness | Claude + human |
| bootstrap + DSR | dev OOS trades | uncertainty, multiple-testing penalty | automatic |
| 2x cost stress | dev OOS trades | execution robustness | automatic |
| lockbox | 2023+ | one-shot confirmation of a frozen design | human-triggered, logged |
| paper trading | live feed | real spreads, slippage, latency | ≥ 8 weeks |

## 8. Promotion criteria

Dev gates (`GATES_DEV`): ≥100 OOS filtered trades; net expectancy > 0 with bootstrap P(E[R] ≤ 0) ≤ 5%;
profit factor ≥ 1.2; beats unfiltered baseline; AUC ≥ 0.53; positive in ≥ 60% of folds; max DD ≥ −25%
at 1% risk; still positive at 2x costs; deflated Sharpe ≥ 0.90 given all trials so far.

Lockbox: net expectancy > 0 and inside the dev bootstrap CI; no gate other than trade count may fail.

Paper (`GATES_PAPER`): ≥ 8 weeks and ≥ 40 trades; realised expectancy inside dev CI; mean slippage vs
model ≤ $0.15/oz. Only then a small live allocation.

## 9. Roadmap

- V1 (this repo): H01 rule filter vs H02 LightGBM meta-label on placeholder BBMA rules.
- V1.1: replace placeholder rules with the exact discretionary rules; import a log of real past trades
  as a second label source.
- V2: regime models (HMM / change-point) as features, not as standalone strategies; sizing from p.
- V3: exit model (dynamic TP/SL), M1 data for exact barrier resolution, paper-trading bridge to MT5.
