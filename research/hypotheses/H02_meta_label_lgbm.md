# H02 — LightGBM meta-label filter for BBMA setups

- **Status:** proposed
- **Version:** 1
- **Improves:** setup filter

## Statement (falsifiable)
A LightGBM model trained on information available at the signal bar close can rank BBMA setups so
that taking only setups with P(TP before SL) >= 0.55 yields positive net expectancy that beats the
unfiltered strategy, in purged walk-forward out-of-sample tests on the development period (config `splits.dev_end`).

## Mechanism / economic rationale
The discretionary trader already filters setups by "feel" for context (session, distance from the
day's range, volatility, trend maturity). The meta-model tries to make that context explicit. The
primary model supplies the side; the meta-model only decides whether to take it and how much to bet
(López de Prado, *Advances in Financial ML*, ch.3).

## Literature
_To be filled by `/lit-review meta-labeling triple barrier gradient boosting`._

## Design
- Inputs: `MODEL_FEATURES` in `features/pipeline.py` + trade side.
- Target: triple-barrier label (TP 2 ATR / SL 1 ATR / 48 bars, SL-first on ambiguity).
- Model: LightGBM (config `meta_model.params`), benchmarked against L2 logistic regression.
- Decision rule: take the trade if p >= 0.55 (fixed in config before running).
- Validation: expanding purged walk-forward, 6 folds, 96-bar embargo. Costs: config `costs`, plus 2x stress.
- Implementation: `src/xauquant/experiments/meta_label.py`.

## Kill criteria (written before the first run)
- Any failed dev gate (`GATES_DEV`).
- LightGBM AUC not above logistic regression AUC (then use the simpler model or reject).

## Scores (1-5)
| economic rationale | robustness | complexity | data needs | overfit risk | interpretability |
|---|---|---|---|---|---|
| 4 | 3 | 2 | 2 | 3 (medium) | 3 |

## Adversarial review
_Not yet run._

## Results log
| run | date | commit | verdict | note |
|---|---|---|---|---|
