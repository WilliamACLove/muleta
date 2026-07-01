from muleta.report import score, Report


def test_score_all_fields():
    r = score("We must leverage synergy to win.")
    assert isinstance(r, Report)
    assert r.corpus_version == "0.1.0" and r.formula_version == "bfc-v1"
    assert r.word_count == 6
    assert any(h.term == "leverage" for h in r.hits)
    assert 1.0 <= r.composite <= 10.0


def test_to_dict_json_ready():
    d = score("leverage now").to_dict()
    assert set(d) >= {
        "composite",
        "bull_index",
        "flesch",
        "word_count",
        "hits",
        "corpus_version",
        "formula_version",
    }
    assert d["hits"][0]["term"] == "leverage"


def test_public_api():
    import muleta

    assert hasattr(muleta, "score")
