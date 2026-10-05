# H05 — Diversified daily time-series momentum (trend following)

- **Status:** proposed
- **Version:** 1
- **Improves:** standalone portfolio strategy

## Statement (falsifiable)
A volatility-targeted 12-month (and blended 1/3/12-month) time-series momentum rule applied to a
basket of liquid CFDs (XAUUSD, XAGUSD, EURUSD, USDJPY, GBPUSD, AUDUSD, US500, US100, GER40, JP225, US
crude) delivers a net Sharpe > 0.5 over the dev period, and the portfolio beats the gold-only version.

## Mechanism / economic rationale
The best-documented edge in the literature: under-reaction then over-reaction, hedging flows, risk
premia; low turnover survives costs. Diversification is where most of the Sharpe comes from.

## Literature
Supporting: Hurst, Ooi & Pedersen (century of trend following); Moskowitz, Ooi & Pedersen;
Baltas & Kosowski. Contradicting: weak 2010s performance; crowding; CFD swap costs vs futures.

## Design
- Signals: sign of 12m return (variant: average sign of 1m/3m/12m). Fixed from literature, no tuning.
- Sizing: each instrument targets 10%/yr volatility (60-day EWMA), rebalanced weekly; cap leverage.
- Costs: spread on rebalance + **daily swap/financing** from the broker's swap table.
- Validation: dev period only; per-year, per-instrument, per-asset-class breakdown; bootstrap Sharpe CI.

## Kill criteria (written before the first run)
- Net Sharpe <= 0.5 or max drawdown worse than -30% at the 10% vol target.
- Net Sharpe after swap costs < 50% of gross Sharpe (financing eats the edge).

## Scores (1-5)
| economic rationale | robustness | complexity | data needs | overfit risk | interpretability |
|---|---|---|---|---|---|
| 5 | 5 | 2 | 3 | 1 (low) | 5 |

## Adversarial review
_Not yet run._

## Results log
| run | date | commit | verdict | note |
|---|---|---|---|---|
