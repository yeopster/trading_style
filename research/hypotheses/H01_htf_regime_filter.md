# H01 — HTF trend + volatility regime filter

- **Status:** proposed
- **Version:** 1
- **Improves:** regime, setup filter

## Statement (falsifiable)
BBMA setups taken when H4 and D1 trend agree with the trade direction AND the M15 ATR percentile is
in the middle tercile have higher net expectancy than all setups, by at least 0.10R, out of sample.

## Mechanism / economic rationale
Re-entry setups are continuation trades; they should work when a higher-timeframe trend exists and
volatility is high enough to reach TP but not so high that stops get hit by noise (news spikes).

## Literature
_To be filled by `/lit-review regime detection volatility filter gold`._

## Design
- Inputs: `h4_trend`, `d1_trend`, `atr_pctile` (all causal).
- Target: triple-barrier label (TP 2 ATR / SL 1 ATR / 48 bars).
- Model: none — a rule-based filter. This is the interpretable benchmark that H02 must beat.
- Validation: same walk-forward folds as H02; compare filtered vs unfiltered per fold.

## Kill criteria (written before the first run)
- Any failed dev gate.
- Uplift not positive in at least 4 of 6 folds.

## Scores (1-5)
| economic rationale | robustness | complexity | data needs | overfit risk | interpretability |
|---|---|---|---|---|---|
| 4 | 4 | 1 | 1 | 1 (low) | 5 |

## Adversarial review
_Not yet run._

## Results log
| run | date | commit | verdict | note |
|---|---|---|---|---|
