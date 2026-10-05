# HNN — <title>

- **Status:** proposed | testing | rejected | survived | lockbox_pass | lockbox_fail | paper | live
- **Version:** 1
- **Improves:** regime | setup filter | entry timing | sizing | exits

## Statement (falsifiable)
<One sentence: "Conditioning on X improves net expectancy of BBMA setups by more than Y.">

## Mechanism / economic rationale
<Why should this work in gold? Who is on the other side of the trade?>

## Literature
<Links to files in research/literature/ — supporting AND contradicting.>

## Design
- Inputs / features:
- Target / label:
- Model:
- Decision rule (threshold fixed in config before running):
- Validation: purged walk-forward (n_splits, embargo) on dev data only; CPCV as robustness check.

## Kill criteria (written before the first run)
Any failed gate in `gates.py` rejects. Additional hypothesis-specific criteria:
-

## Scores (1-5)
| economic rationale | robustness | complexity | data needs | overfit risk | interpretability |
|---|---|---|---|---|---|

## Adversarial review
| # | criticism | class | response / redesign |
|---|---|---|---|

## Results log
| run | date | commit | verdict | note |
|---|---|---|---|---|
