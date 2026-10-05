# H03 — Gold session seasonality (Asia up / New York down)

- **Status:** proposed
- **Version:** 1
- **Improves:** standalone strategy (new edge, not a BBMA filter)

## Statement (falsifiable)
On XAUUSD, being long during Asian hours (00:00–07:00 UTC) and flat (or short) during New York
hours (13:00–21:00 UTC) earns positive net expectancy per trade on the development period, with
the effect present in at least 4 of 6 walk-forward folds — including the most recent fold.

## Mechanism / economic rationale
Asian physical/investment demand concentrated in Asian hours; Western hedging and fixing flows in
London/NY hours. Documented on COMEX gold, spot, miners and ETFs (1985–2012), weakened since. See
`research/literature/20261005_edge-survey-websearch.md` [7][8].

## Literature
Supporting: Blose, Gondhalekar & Kort (2018); Applied Economics Letters (2014); RIETI.
Contradicting / risk: weakening over time; manipulation-era effects around London fixes.

## Design
- Rules are fixed from the literature, NOT searched: long at 00:00 UTC open, exit 07:00 UTC close.
  Variant B (pre-registered, counts as a second trial): short 13:00–21:00 UTC.
- No parameters to tune. Costs: config `costs` + 2x stress. No swap cost (no overnight hold in UTC terms; check broker rollover time).
- Validation: per-year and per-fold expectancy; bootstrap CI; compare to random-hour placebo windows of equal length.

## Kill criteria (written before the first run)
- Any failed applicable dev gate (no model gates: AUC/baseline gates do not apply).
- Net expectancy of the most recent two years of dev data <= 0 (decayed edge).
- Not better than the 95th percentile of random-window placebos.

## Scores (1-5)
| economic rationale | robustness | complexity | data needs | overfit risk | interpretability |
|---|---|---|---|---|---|
| 3 | 3 | 1 | 1 | 1 (low) | 5 |

## Adversarial review
_Not yet run._

## Results log
| run | date | commit | verdict | note |
|---|---|---|---|---|
