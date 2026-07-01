from pathlib import Path

import pytest

from muleta.report import score

SAMPLES = Path(__file__).parent / "samples"

# Locked literals — computed from the bfc-v1 formula + corpus 0.1.0. If the engine
# or corpus changes intentionally, update these in the same commit (never silently).
EXPECTED = {
    "jargon_heavy": {"composite": 1.0, "bull_index": 1750.0},
    "clean": {"composite": 9.6, "bull_index": 0.0},
}


@pytest.mark.parametrize("name", ["jargon_heavy", "clean"])
def test_scores_stable(name):
    r = score((SAMPLES / f"{name}.txt").read_text(encoding="utf-8"))
    assert r.composite == EXPECTED[name]["composite"]
    assert r.bull_index == EXPECTED[name]["bull_index"]
