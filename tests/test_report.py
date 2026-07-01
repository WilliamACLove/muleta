from muleta.report import Report, score


def test_score_all_fields():
    r = score("We must leverage synergy to win.")
    assert isinstance(r, Report)
    assert r.corpus_version == "1.0.0"
    assert r.formula_version == "bfc-v2"
    assert r.word_count == 6
    assert any(h.term == "leverage" for h in r.hits)
    assert 0.0 <= r.composite <= 10.0
    assert r.weight_factor == 2


def test_to_dict_json_ready():
    d = score("leverage now").to_dict()
    assert set(d) >= {
        "composite",
        "bull_index",
        "bull_index_raw",
        "flesch",
        "flesch_adjusted",
        "word_count",
        "weight_factor",
        "hits",
        "corpus_version",
        "formula_version",
    }
    assert d["hits"][0]["term"] == "leverage"
    assert d["hits"][0]["weight"] == 8


def test_public_api():
    import muleta

    assert hasattr(muleta, "score")
