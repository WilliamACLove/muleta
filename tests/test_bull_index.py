import pytest

from muleta.bull_index import bull_scores, find_hits, weight_factor
from muleta.corpus import Corpus

C = Corpus.load()


def test_weight_factor_thresholds():
    assert weight_factor(5) == 2
    assert weight_factor(1500) == 3
    assert weight_factor(20000) == 4
    assert weight_factor(60000) == 5


def test_find_hits_terms_and_offsets():
    hits = find_hits("We must leverage synergy now.", C)
    terms = {h.term for h in hits}
    assert "leverage" in terms and "synergy" in terms
    lev = next(h for h in hits if h.term == "leverage")
    assert "We must leverage synergy now."[lev.start:lev.end].lower() == "leverage"


def test_find_hits_matches_forms_and_hyphen_variants():
    assert any(h.term == "leverage" for h in find_hits("We leveraged it.", C))
    assert any(h.term == "synergy" for h in find_hits("great synergies here", C))
    assert any(h.term == "best in class" for h in find_hits("a best-in-class result", C))


def test_hits_carry_suggestions():
    hits = find_hits("We leveraged it.", C)
    lev = next(h for h in hits if h.term == "leverage")
    assert "use" in lev.suggestions


def test_bull_scores_formula():
    # "leverage now": N=2 -> F=2; leverage weight 8, Ci=1, Wi=min(1/2,1)=0.5
    # penalty = 8*0.5 = 4; BIr = 96; BI = 9.6
    bir, bi, f, hits = bull_scores("leverage now", C)
    assert f == 2
    assert bir == pytest.approx(96.0)
    assert bi == pytest.approx(9.6)


def test_bull_scores_clean_text():
    bir, bi, f, hits = bull_scores("we write plainly and clearly for our readers", C)
    assert bir == pytest.approx(100.0)
    assert bi == pytest.approx(10.0)
    assert hits == []
