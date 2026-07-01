import pytest

from muleta.bull_index import bull_index, find_hits
from muleta.corpus import Corpus

C = Corpus.load()


def test_find_hits_terms_and_offsets():
    hits = find_hits("We must leverage synergy now.", C)
    terms = [(h.term, h.severity) for h in hits]
    assert ("leverage", 5) in terms and ("synergy", 4) in terms
    lev = next(h for h in hits if h.term == "leverage")
    assert "We must leverage synergy now."[lev.start:lev.end].lower() == "leverage"


def test_find_hits_word_bounded():
    assert len(find_hits("Leverage the leverages.", C)) == 1


def test_bull_index_zero_when_clean():
    assert bull_index("plain honest words here", C) == 0.0


def test_bull_index_weighted_density():
    # "leverage" sev 5 in 2 words -> 1000 * 5 / 2 = 2500.0
    assert bull_index("leverage now", C) == pytest.approx(2500.0)
