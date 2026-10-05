import asyncio
import json

import httpx
import pytest

from quant_research_mcp import perplexity, server


def fake_client(captured):
    def handler(request: httpx.Request):
        captured["body"] = request.read().decode()
        captured["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={
            "model": "sonar-pro",
            "choices": [{"message": {"content": "HMMs are fragile [1]."}}],
            "citations": ["https://arxiv.org/abs/1234"],
            "search_results": [{"title": "Paper", "url": "https://arxiv.org/abs/1234", "date": "2024-01-01"}],
        })
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_ask_builds_request(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "k")
    cap = {}
    res = perplexity.ask("q", academic=True, recency="year", client=fake_client(cap))
    assert res.citations == ["https://arxiv.org/abs/1234"]
    body = json.loads(cap["body"])
    assert body["search_mode"] == "academic" and body["search_recency_filter"] == "year"
    assert cap["auth"] == "Bearer k"


def test_missing_key(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    with pytest.raises(perplexity.PerplexityError):
        perplexity.ask("q")


def test_tool_archives_result(monkeypatch, tmp_path):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "k")
    monkeypatch.setattr(server, "ARCHIVE", tmp_path)
    monkeypatch.setattr(server, "ROOT", tmp_path.parent)
    real_ask = perplexity.ask
    monkeypatch.setattr(server, "ask", lambda p, **kw: real_ask(p, client=fake_client({}), **kw))
    out = server.find_counter_evidence("BBMA re-entries work in trending gold")
    assert "Sources:" in out and "arxiv.org" in out
    files = list(tmp_path.glob("*counter-evidence*.md"))
    assert len(files) == 1 and "## Sources" in files[0].read_text()


def test_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"deep_research", "find_counter_evidence", "research_algorithm"} <= names
