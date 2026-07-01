from muleta.corpus import Corpus
from muleta.watchlist import Watchlist

C = Corpus.load()
W = Watchlist.load()


def test_watchlist_loads():
    assert W.version
    assert len(W.entries()) > 50


def test_scan_flags_non_corpus_jargon():
    cands = W.scan("We should circle back and facilitate this going forward.", C)
    terms = {c.term for c in cands}
    assert "circle back" in terms
    assert "facilitate" in terms


def test_candidates_carry_suggestions():
    cands = W.scan("please facilitate the form", C)
    fac = next(c for c in cands if c.term == "facilitate")
    assert "help" in fac.suggestions


def test_scan_excludes_corpus_terms():
    # Corpus terms are scored, not candidates. None of the scan results is a corpus term.
    cands = W.scan("leverage synergy and circle back", C)
    assert all(C.weight(c.term) is None for c in cands)
