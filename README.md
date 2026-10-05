# xauusd-quant — AI-assisted research lab for an XAUUSD BBMA strategy

Perplexity finds the knowledge, Claude turns it into hypotheses and code, Python judges, and
paper trading gives the final verdict. Claude never gets to decide whether its own idea works.

```
Perplexity (MCP) ──► Claude Code ──► hypothesis file (kill criteria) ──► adversarial review
       ▲                                                                       │
       └──────── new hypothesis ◄── REJECT ◄── gates ◄── purged walk-forward ◄─┘
                                      SURVIVE ──► lockbox (once) ──► paper ──► live
```

The first experiment is **meta-labelling**: the BBMA rules generate the trade, and LightGBM estimates
`P(TP before SL)` for that setup. It does not try to forecast the gold price.

## Setup (Windows / macOS / Linux)

```bash
git clone <this repo> && cd trading_style
python -m venv .venv && .venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -e ".[mcp,dev]"                            # add ,tracking for MLflow
pytest -q                                              # 21 tests, includes look-ahead checks
```

**Perplexity API key.** Create one at perplexity.ai → Settings → API (billed separately from a
Perplexity Pro subscription). Set it in your shell before starting Claude Code:

```bash
setx PERPLEXITY_API_KEY "pplx-..."      # Windows (new terminal afterwards)
export PERPLEXITY_API_KEY="pplx-..."    # macOS/Linux
```

**Connect it to Claude Code.** `.mcp.json` registers the `quant-research` server for this project.
Start `claude` in the repo root, approve the server when prompted, and check it with `/mcp`.
Alternatively: `claude mcp add quant-research -- python -m quant_research_mcp.server`.
If Perplexity has renamed its models, set `PPLX_MODEL_SEARCH` / `PPLX_MODEL_REASONING` / `PPLX_MODEL_DEEP`.

| tool | use |
|---|---|
| `deep_research` | broad literature review (slow, more expensive) |
| `find_academic_research` | scholarly sources only |
| `research_algorithm` | structured brief on one technique |
| `find_counter_evidence` | adversarial search for reasons a hypothesis fails |
| `critique_strategy` | how a backtest of a design is likely overstating performance |
| `perplexity_search` | quick cited lookup |

Every result is saved to `research/literature/` with its sources.

**Data.** Export XAUUSD M15 from MT5 (History Center or a script) to `data/raw/XAUUSD_M15.csv`
with columns `time,open,high,low,close,tick_volume,spread` in UTC (the raw MT5 `<DATE>\t<TIME>` format
also works). Data is git-ignored. To try the pipeline without data:

```bash
python scripts/make_synthetic_data.py      # driftless random walk: must be REJECTED
python scripts/run_experiment.py --hypothesis H02 --csv data/raw/XAUUSD_M15_synthetic.csv --no-log
```

## The research loop in Claude Code

| step | command |
|---|---|
| literature | `/lit-review meta-labeling and triple-barrier labeling for FX/gold` |
| hypotheses | `/hypotheses` → `research/hypotheses/HNN_*.md` with kill criteria |
| attack | `/adversarial H02` → Perplexity critique + CRITICAL/IMPORTANT/MINOR triage |
| test | `/run-hypothesis H02` → code, tests, run, report, registry entry |
| status | `/status` |

Rules Claude follows are in [`CLAUDE.md`](CLAUDE.md): lockbox never touched, no look-ahead, no optimising
toward a metric, costs always on, every trial counted. The design is in [`docs/architecture.md`](docs/architecture.md).

## Before trusting any result

1. **Replace the placeholder BBMA rules** in `src/xauquant/strategy/bbma.py` with your exact rules.
2. Check your broker timezone and spreads. Costs in `config.yaml` are in USD per ounce.
3. Fix the lockbox date before you look at any results, and leave it fixed.
