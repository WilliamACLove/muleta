import pytest

from muleta.corpus import Corpus, CorpusError


def test_load_authentic_corpus():
    c = Corpus.load()
    assert c.version == "1.0.0"
    assert "leverage" in c.terms()
    assert len(c.entries()) >= 100  # ~113 authentic headwords


def test_weight_anchors():
    c = Corpus.load()
    assert c.weight("global") == 1  # abused real word
    assert c.weight("leverage") == 8
    assert c.weight("envisioneer") == 10  # worst coinage


def test_weight_case_insensitive():
    assert Corpus.load().weight("LEVERAGE") == 8


def test_reject_bad_weight(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(
        'version: "0.0.1"\nentries:\n  - {term: x, weight: 11, source: user, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorpusError):
        Corpus.load(p)


def test_reject_duplicates(tmp_path):
    p = tmp_path / "dup.yaml"
    p.write_text(
        'version: "0.0.1"\nentries:\n'
        '  - {term: x, weight: 1, source: user, added: "2026-07-01"}\n'
        '  - {term: X, weight: 2, source: user, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorpusError):
        Corpus.load(p)


def test_add_and_save_roundtrip(tmp_path):
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "1.0.0"\nentries:\n  - {term: leverage, weight: 8, source: extracted, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    c = Corpus.load(src)
    c.add("bandwidth", weight=8, source="user", added="2026-07-02", note="test")
    c.save(src)
    assert Corpus.load(src).weight("bandwidth") == 8


def test_add_duplicate_raises():
    c = Corpus.load()
    with pytest.raises(CorpusError):
        c.add("leverage", weight=1, source="user", added="2026-07-02")


def test_remove_term(tmp_path):
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "1.0.0"\nentries:\n'
        '  - {term: leverage, weight: 8, source: extracted, added: "2026-07-01"}\n'
        '  - {term: synergy, weight: 8, source: extracted, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    c = Corpus.load(src)
    c.remove("synergy")
    assert c.weight("synergy") is None and c.weight("leverage") == 8
