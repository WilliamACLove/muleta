from pathlib import Path

import pytest

from muleta.report import score

SAMPLES = Path(__file__).parent / "samples"

# Locked literals — authentic Bullfighter scoring (bfc-v2) + corpus 1.0.0. If the
# engine or corpus changes intentionally, update these in the same commit (never silently).
EXPECTED = {
    "jargon_heavy": {"composite": 5.5, "bull_index_raw": 84.5, "hit_terms": {"leverage", "synergy", "bandwidth", "value add"}},
    "clean": {"composite": 9.9, "bull_index_raw": 100.0, "hit_terms": set()},
}


@pytest.mark.parametrize("name", ["jargon_heavy", "clean"])
def test_scores_stable(name):
    r = score((SAMPLES / f"{name}.txt").read_text(encoding="utf-8"))
    exp = EXPECTED[name]
    assert r.composite == exp["composite"]
    assert r.bull_index_raw == exp["bull_index_raw"]
    assert {h.term for h in r.hits} == exp["hit_terms"]
