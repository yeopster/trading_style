---
kind: edge-survey
model: web search (Perplexity API blocked by environment network policy)
retrieved: 2026-10-05
---

# Edge survey: what has survived out of sample, after costs?

Scope: edges a retail trader can automate on MT5-style instruments (spot gold, FX majors,
index CFDs), M15-to-daily horizons. Ranked by quality of evidence, not by reported return.

## Base rates first (read before anything else)
- 74–89% of retail CFD accounts lose money (ESMA, 2018). The default outcome is losing,
  mostly to costs and leverage. [1]
- Published anomalies return ~26% less out of sample and ~58% less after publication
  (McLean & Pontiff, 97 predictors). Expect any edge found in a paper to be weaker live. [2]
- Thousands of technical rules look profitable, but most of that disappears after
  data-snooping corrections (White's Reality Check / Hansen's SPA) in FX and equity
  indices. Searching rule space is how people fool themselves. [3][4]

## Candidate edges

| # | edge | evidence | structural reason | caveats |
|---|---|---|---|---|
| A | **Time-series momentum / trend following** (daily, multi-asset, vol-scaled) | Strongest: >100 years, dozens of markets, new out-of-sample assets and factors; low turnover survives costs [5][6] | Slow information diffusion, hedging flows, behavioural under/over-reaction | Works as a *diversified* portfolio; single-market (gold only) is lumpy; long flat periods (2010s) |
| B | **Gold intraday/overnight seasonality** (Asia hours up, NY hours down; overnight > day) | COMEX gold 1985–2012, plus spot (London fix), miners, ETFs; weakened but still present and "economically important after costs" (2018) [7][8] | Physical demand in Asia; Western hedging/fixing flows; inventory risk | Weakened over time; CFD overnight swap costs; alleged-manipulation period around fixes; must be re-tested post-2018 |
| C | **Intraday momentum** (first half-hour predicts last; "noise area" breakouts) | SPY 1993–2013 (Gao et al.); SPY 2007–2024 net of costs, Sharpe 1.33 (Zarattini, Aziz & Barbon 2024) [9][10] | Late-informed trading, gamma hedging by dealers, infrequent rebalancing | Strong for US equity index; **untested for gold/FX** (a real research question); spread-sensitive |
| D | **Overnight equity drift** (index return earned overnight) | Persistent since 1993, ~7%/yr gap [11] | Inventory/risk compensation, overnight news | CFD swap financing may eat most of it; tested on cash/futures, not CFDs |
| E | **Pre-FOMC drift** | Strong 1994–2011 | Uncertainty resolution | **Disappeared after 2015** (Kurov, Wolfe & Gilbert 2020) — reject [12] |
| F | Discretionary-pattern rules (BBMA etc.) + ML meta-filter | No direct literature | Depends on the rules | Existing H01/H02; keep as one candidate among several |

## Implications for this project
1. The most robust edge (A) is a **portfolio** edge: trade the same simple rule on many
   uncorrelated instruments with volatility targeting. One instrument is not enough.
2. Gold-specific timing edges (B, C) are cheap to test with the M15 data we already plan to load,
   and have a stated mechanism. They are the best *gold* candidates.
3. Higher turnover = more cost drag. M15 edges need to clear a ~$0.3–0.5/oz round trip.
4. Every strategy we try counts as a trial; the deflated-Sharpe gate gets stricter as we explore.

## Sources
1. [ESMA — restrict CFDs to protect retail investors](https://www.esma.europa.eu/node/84933)
2. [McLean & Pontiff — Does academic research destroy stock return predictability?](https://Www.Gwern.net/doc/economics/2016-mclean.pdf)
3. [Re-examining technical analysis with White's Reality Check and Hansen's SPA](https://c.mql5.com/forextsd/forum/211/Re-Examining%20the%20Profitability%20of%20Technical%20Analysis%20with%20Whitets%20Reality%20Check%20and%20Hansen9s%20SPA%20Tes.pdf)
4. [Technical trading rules in emerging FX markets and data snooping (EFMA 2008)](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2008-Athens/papers/Wang5.pdf)
5. [A Century of Evidence on Trend-Following Investing](https://www.TrendFollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf)
6. [Baltas & Kosowski — momentum strategies in futures markets (Imperial)](https://spiral.imperial.ac.uk/bitstream/10044/1/41472/4/SSRN-id2140091.pdf)
7. [Blose, Gondhalekar & Kort (2018) — gold overnight vs day returns, J. Economics & Finance](https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html)
8. [Gold night anomaly, Applied Economics Letters (2014)](https://ideas.repec.org/a/taf/apeclt/v21y2014i18p1269-1272.html); [Intraday seasonality in gold & platinum futures (RIETI)](https://www.rieti.go.jp/en/publications/summary/17110007.html)
9. [Gao, Han, Li & Zhou — Market intraday momentum](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)
10. [Zarattini, Aziz & Barbon (2024) — Beat the Market: intraday momentum for SPY](https://ideas.repec.org/p/chf/rpseri/rp2497.html)
11. [Does overnight news explain overnight returns? (arXiv 2025)](https://arxiv.org/pdf/2507.04481)
12. [Kurov, Wolfe & Gilbert — The disappearing pre-FOMC announcement drift](https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf)
