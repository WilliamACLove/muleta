from muleta import mcp_server as S


def test_score_text_tool_returns_report_dict():
    d = S.score_text("We must leverage synergy to win.")
    assert d["formula_version"] == "bfc-v1"
    assert d["corpus_version"] == "0.1.0"
    assert any(h["term"] == "leverage" for h in d["hits"])
    assert 1.0 <= d["composite"] <= 10.0


def test_find_jargon_tool_lists_hits():
    d = S.find_jargon("leverage bandwidth")
    assert d["count"] == 2
    assert {h["term"] for h in d["hits"]} == {"leverage", "bandwidth"}


def test_corpus_list_tool():
    d = S.corpus_list()
    assert "leverage" in [e["term"] for e in d["entries"]]
    assert d["version"] == "0.1.0"


def test_corpus_add_tool_writes(tmp_path, monkeypatch):
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "0.1.0"\nentries:\n  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(S, "CORPUS_PATH", src)
    out = S.corpus_add("bandwidth", severity=4, source="user", note="x")
    assert out["ok"] is True
    from muleta.corpus import Corpus

    assert Corpus.load(src).severity("bandwidth") == 4


def test_server_object_is_fastmcp():
    from mcp.server.fastmcp import FastMCP

    assert isinstance(S.mcp, FastMCP)
