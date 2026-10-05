---
description: Implement and run a hypothesis on development data, record the verdict
argument-hint: <hypothesis id>
---
1. Read `CLAUDE.md` and `research/hypotheses/$ARGUMENTS*.md`. Confirm kill criteria are written
   and the adversarial review has been triaged; if not, stop and say so.
2. Implement the experiment under `src/xauquant/` (new module, do not edit others' experiments
   except shared, tested utilities). Add tests for any new labelling/feature code, especially
   a no-look-ahead test. Run `pytest -q`.
3. Commit, then run `python scripts/run_experiment.py --hypothesis $ARGUMENTS --notes "<what changed>"`.
4. Write `reports/$ARGUMENTS_run<id>.md`: gates table, baseline vs filtered, breakdowns by
   year / side / session / volatility regime / H4 trend, and an honest interpretation.
5. Update the hypothesis status. If rejected, record WHY and propose at most one follow-up
   hypothesis that addresses a different mechanism (not a parameter tweak).
Never touch the lockbox. Never change gates or thresholds to make a result pass.
