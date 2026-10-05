"""quant-research MCP server: gives Claude Code a Perplexity-backed research department.

Every result is also archived to research/literature/ as Markdown (with sources),
so the research trail is versioned in git next to the hypotheses it produced.

Run:  python -m quant_research_mcp.server     (stdio; registered in .mcp.json)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from quant_research_mcp.perplexity import PerplexityError, ResearchResult, ask

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "research" / "literature"
PROMPTS = ROOT / "prompts"
PROJECT_CONTEXT = (
    "Context: automated XAUUSD (spot gold) system. D1/H4 for regime and trend, M15 for entries. "
    "Primary signals come from a BBMA-style rule set (Bollinger Bands 20,2; LWMA 5/10 on highs/lows; "
    "EMA trend filter). Machine learning is used only as a meta-model (P(setup succeeds)), regime "
    "filter, position sizer or exit model — not to forecast price directly."
)

mcp = FastMCP("quant-research")


def _slug(text: str, n: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n] or "query"


def _archive(kind: str, query: str, res: ResearchResult) -> Path:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    path = ARCHIVE / f"{ts:%Y%m%d-%H%M%S}_{kind}_{_slug(query)}.md"
    src = "\n".join(
        f"{i}. [{s.get('title') or s.get('url')}]({s.get('url')})" + (f" — {s['date']}" if s.get("date") else "")
        for i, s in enumerate(res.sources, 1)
    ) or "\n".join(f"{i}. {u}" for i, u in enumerate(res.citations, 1))
    path.write_text(
        f"---\nkind: {kind}\nmodel: {res.model}\nretrieved: {ts.isoformat()}\n---\n\n"
        f"# {kind}: {query}\n\n{res.content}\n\n## Sources\n\n{src}\n"
    )
    return path


def _run(kind: str, query: str, prompt: str, **kw) -> str:
    try:
        res = ask(prompt, **kw)
    except PerplexityError as e:
        return f"ERROR: {e}"
    path = _archive(kind, query, res)
    cites = "\n".join(f"[{i}] {u}" for i, u in enumerate(res.citations, 1))
    return f"{res.content}\n\n---\nSources:\n{cites}\n\n(archived: {path.relative_to(ROOT)})"


def _template(name: str, **fields) -> str:
    text = (PROMPTS / name).read_text()
    for k, v in fields.items():
        text = text.replace("{{" + k + "}}", v)
    return text


@mcp.tool()
def perplexity_search(query: str, recency: str | None = None, domains: list[str] | None = None) -> str:
    """Fast cited web search for a specific question (definitions, a paper's claims, library docs).
    recency: one of hour/day/week/month/year. domains: optional allow-list, e.g. ["arxiv.org", "ssrn.com"]."""
    return _run("search", query, query, mode="search", recency=recency, domains=domains)


@mcp.tool()
def find_academic_research(topic: str) -> str:
    """Search scholarly sources only (papers, preprints) on a topic. Returns findings with
    sample period, asset, validation method and whether costs were modelled."""
    prompt = (f"{PROJECT_CONTEXT}\n\nFind the most relevant academic research on: {topic}.\n"
              "For each paper give: citation, asset & sample period, method, validation scheme "
              "(in-sample / walk-forward / CV), whether transaction costs were included, headline result, "
              "and limitations. Group papers that agree and flag those that contradict each other.")
    return _run("academic", topic, prompt, mode="search", academic=True)


@mcp.tool()
def research_algorithm(algorithm: str) -> str:
    """Structured brief on one technique (e.g. 'Hidden Markov Model regime detection',
    'meta-labeling', 'triple-barrier labeling') as it applies to this XAUUSD project."""
    prompt = _template("perplexity_algorithm_brief.md", ALGORITHM=algorithm, CONTEXT=PROJECT_CONTEXT)
    return _run("algorithm", algorithm, prompt, mode="reasoning", academic=True)


@mcp.tool()
def find_counter_evidence(hypothesis: str) -> str:
    """Adversarial review: search for evidence that would DISPROVE a hypothesis (leakage,
    look-ahead, regime dependence, cost sensitivity, publication bias, known failures).
    Use on every hypothesis before implementation and on every survivor before paper trading."""
    prompt = _template("perplexity_adversarial_review.md", HYPOTHESIS=hypothesis, CONTEXT=PROJECT_CONTEXT)
    return _run("counter-evidence", hypothesis[:80], prompt, mode="reasoning")


@mcp.tool()
def critique_strategy(strategy: str) -> str:
    """Critique a full strategy/experiment design against the quant literature and list the
    most likely ways its backtest is overstating live performance."""
    prompt = (f"{PROJECT_CONTEXT}\n\nAct as a sceptical reviewer at a systematic fund. Critique this "
              f"strategy / experiment design:\n\n{strategy}\n\nList the most likely reasons a backtest of it "
              "would overstate live performance, ranked by severity, each with supporting citations, and "
              "the specific test that would detect each problem.")
    return _run("critique", strategy[:80], prompt, mode="reasoning")


@mcp.tool()
def deep_research(topic: str) -> str:
    """Long-form multi-source literature review (slow: minutes; costs more). Use for broad
    mandates such as the initial literature review, not for quick facts."""
    prompt = _template("perplexity_literature_review.md", TOPIC=topic, CONTEXT=PROJECT_CONTEXT)
    return _run("deep-research", topic, prompt, mode="deep")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
