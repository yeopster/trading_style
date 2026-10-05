"""Thin Perplexity API client (OpenAI-compatible chat completions + citations).

Model names are configurable via env vars because Perplexity renames them over
time. Check https://docs.perplexity.ai if a call returns 400 'invalid model'.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import httpx

API_URL = os.environ.get("PPLX_API_URL", "https://api.perplexity.ai/chat/completions")
MODELS = {
    "search": os.environ.get("PPLX_MODEL_SEARCH", "sonar-pro"),
    "reasoning": os.environ.get("PPLX_MODEL_REASONING", "sonar-reasoning-pro"),
    "deep": os.environ.get("PPLX_MODEL_DEEP", "sonar-deep-research"),
}

SYSTEM = (
    "You are a sceptical quantitative-finance research analyst. Prefer peer-reviewed papers, "
    "SSRN/arXiv preprints by credible authors, and practitioner research with disclosed methodology. "
    "Cite every factual claim. Distinguish in-sample from out-of-sample evidence, report whether "
    "transaction costs were included, and state sample periods and assets. Say explicitly when "
    "evidence is weak, contradictory, or absent. Never recommend a method because of high reported returns."
)


class PerplexityError(RuntimeError):
    pass


@dataclass
class ResearchResult:
    content: str
    citations: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    model: str = ""
    usage: dict = field(default_factory=dict)


def ask(prompt: str, mode: str = "search", *, academic: bool = False, recency: str | None = None,
        domains: list[str] | None = None, system: str = SYSTEM, timeout: float | None = None,
        client: httpx.Client | None = None) -> ResearchResult:
    key = os.environ.get("PERPLEXITY_API_KEY")
    if not key:
        raise PerplexityError("PERPLEXITY_API_KEY is not set (see .env.example)")
    model = MODELS[mode]
    body: dict = {"model": model, "messages": [{"role": "system", "content": system},
                                               {"role": "user", "content": prompt}]}
    if academic:
        body["search_mode"] = "academic"
    if recency:
        body["search_recency_filter"] = recency
    if domains:
        body["search_domain_filter"] = domains[:20]
    if mode == "deep":
        body["reasoning_effort"] = os.environ.get("PPLX_DEEP_EFFORT", "medium")

    timeout = timeout or (900.0 if mode == "deep" else 120.0)
    own = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        r = client.post(API_URL, json=body, headers={"Authorization": f"Bearer {key}"})
    finally:
        if own:
            client.close()
    if r.status_code != 200:
        raise PerplexityError(f"Perplexity API {r.status_code}: {r.text[:500]}")
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    sources = data.get("search_results") or []
    citations = data.get("citations") or [s.get("url") for s in sources if s.get("url")]
    return ResearchResult(content=content, citations=citations, sources=sources, model=data.get("model", model),
                          usage=data.get("usage", {}))
