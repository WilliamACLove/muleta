import pytest

from muleta.composite import FORMULA_VERSION, K_PENALTY, bull_composite


def test_formula_pinned():
    assert FORMULA_VERSION == "bfc-v1" and K_PENALTY == 30.0


def test_clear_text_high():
    # flesch 80 -> 0.8; bull_index 0 -> penalty 0; 1 + 9*0.8 = 8.2
    assert bull_composite(80.0, 0.0) == pytest.approx(8.2)


def test_heavy_jargon_penalized():
    # flesch 80 -> 0.8; bull_index 30 -> penalty 1.0; 1 + 9*0 = 1.0
    assert bull_composite(80.0, 30.0) == pytest.approx(1.0)


def test_clamped():
    assert bull_composite(200.0, 0.0) == pytest.approx(10.0)
    assert bull_composite(-50.0, 0.0) == pytest.approx(1.0)
