from muleta import mcp_server as S
from muleta.corpus import Corpus


def test_scan_candidates_tool():
    d = S.scan_candidates("We will circle back and facilitate this.")
    terms = {c["term"] for c in d["candidates"]}
    assert "circle back" in terms and "facilitate" in terms


def test_analyze_tool_returns_score_and_candidates():
    d = S.analyze("We will leverage synergy and circle back.")
    assert "score" in d and "candidates" in d and "instruction" in d
    assert any(h["term"] == "leverage" for h in d["score"]["hits"])
    assert "circle back" in {c["term"] for c in d["candidates"]}


def test_propose_review_approve_flow(tmp_path, monkeypatch):
    corpus = tmp_path / "c.yaml"
    corpus.write_text(
        'version: "1.1.0"\nentries:\n  - {term: leverage, weight: 8, source: extracted, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(S, "CORPUS_PATH", corpus)
    monkeypatch.setattr(S, "PENDING_PATH", tmp_path / "pending.yaml")

    S.propose_term("thought shower", example="let's have a thought shower", reason="buzzword")
    q = S.review_queue()
    assert q["count"] == 1 and q["pending"][0]["term"] == "thought shower"

    out = S.approve_term("thought shower", weight=7)
    assert out["ok"] is True
    assert Corpus.load(corpus).weight("thought shower") == 7  # now scored
    assert S.review_queue()["count"] == 0  # removed from queue


def test_usage_stats_tool():
    d = S.usage_stats()
    assert "documents" in d and "logging_enabled" in d
