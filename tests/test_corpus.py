import pytest

from muleta.corpus import Corpus, CorpusError


def test_load_default_corpus():
    c = Corpus.load()
    assert c.version == "0.1.0"
    assert "leverage" in c.terms()


def test_severity_case_insensitive():
    assert Corpus.load().severity("LEVERAGE") == 5


def test_reject_bad_severity(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(
        'version: "0.0.1"\nentries:\n  - {term: x, severity: 9, source: user, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorpusError):
        Corpus.load(p)


def test_reject_duplicates(tmp_path):
    p = tmp_path / "dup.yaml"
    p.write_text(
        'version: "0.0.1"\nentries:\n'
        '  - {term: x, severity: 1, source: user, added: "2026-07-01"}\n'
        '  - {term: X, severity: 2, source: user, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorpusError):
        Corpus.load(p)


def test_add_and_save_roundtrip(tmp_path):
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "0.1.0"\nentries:\n  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    c = Corpus.load(src)
    c.add("bandwidth", severity=4, source="user", added="2026-07-02", note="test")
    c.save(src)
    assert Corpus.load(src).severity("bandwidth") == 4


def test_add_duplicate_raises():
    c = Corpus.load()
    with pytest.raises(CorpusError):
        c.add("leverage", severity=1, source="user", added="2026-07-02")


def test_remove_term(tmp_path):
    src = tmp_path / "c.yaml"
    src.write_text(
        'version: "0.1.0"\nentries:\n'
        '  - {term: leverage, severity: 5, source: reconstructed, added: "2026-07-01"}\n'
        '  - {term: synergy, severity: 4, source: reconstructed, added: "2026-07-01"}\n',
        encoding="utf-8",
    )
    c = Corpus.load(src)
    c.remove("synergy")
    assert c.severity("synergy") is None and c.severity("leverage") == 5
