# Prompt: literature → ranked hypotheses (used by /hypotheses)

You are the lead quantitative researcher for this project.
Input: the literature notes in `research/literature/` (and any file the user names).

My current XAUUSD method uses D1/H4 for directional context, M15 for entry,
Bollinger Bands 20,2, LWMA 5/10 High/Low and an EMA trend filter.

My objective is NOT to replace the strategy with an opaque AI model. I want to determine whether
machine learning can improve:
1. market regime classification
2. setup filtering
3. entry timing
4. position sizing
5. exit decisions

Critically evaluate every method in the research. Produce 10 testable hypotheses ranked by
economic rationale, expected robustness, implementation complexity, data requirements,
overfitting risk and interpretability (score each 1-5 and show the table).

Write each one as `research/hypotheses/HNN_<slug>.md` using `research/hypotheses/TEMPLATE.md`,
with kill criteria fixed now. Do not write production code yet.
