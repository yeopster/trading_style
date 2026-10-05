# H04 — Intraday momentum / noise-area breakout on gold

- **Status:** proposed
- **Version:** 1
- **Improves:** standalone strategy

## Statement (falsifiable)
The Zarattini–Aziz–Barbon "noise area" intraday momentum rule, transferred unchanged from SPY to
XAUUSD (session anchored at the 13:30 UTC NY open), has positive net expectancy on dev data and
beats random-entry placebos with the same holding time and trade count.

## Mechanism / economic rationale
Late-informed trading and dealer hedging create intraday continuation after abnormal moves from
the open. Documented for US index ETFs; gold is untested, so this is a genuine out-of-sample test
of the idea on a new asset.

## Literature
Supporting: Gao, Han, Li & Zhou; Zarattini, Aziz & Barbon (2024). Contradicting: none found for
gold yet — run `/adversarial H04` once Perplexity is reachable.

## Design
- Noise area = open ± average absolute move from the open at that time of day over the prior 14 days
  (paper's definition, not tuned). Enter when price closes outside the band on a 30-min check; exit at
  session close or trailing band stop. Flat overnight.
- Costs: config + 2x stress. Validation: walk-forward folds, placebo comparison, by-year breakdown.

## Kill criteria (written before the first run)
- Any failed applicable dev gate.
- Net expectancy <= 0 at 2x costs.
- Profitable in fewer than 4 of 6 folds.

## Scores (1-5)
| economic rationale | robustness | complexity | data needs | overfit risk | interpretability |
|---|---|---|---|---|---|
| 3 | 3 | 2 | 1 | 2 | 4 |

## Adversarial review
_Not yet run._

## Results log
| run | date | commit | verdict | note |
|---|---|---|---|---|
