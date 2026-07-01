import pytest

from muleta.flesch import adjusted_flesch, flesch_reading_ease


def test_flesch_simple_sentence():
    # "The cat sat." -> words=3, sentences=1, syllables=3
    # 206.835 - 1.015*(3/1) - 84.6*(3/3) = 119.19
    assert flesch_reading_ease("The cat sat.") == pytest.approx(119.19, abs=0.01)


def test_flesch_empty_is_zero():
    assert flesch_reading_ease("") == 0.0


def test_adjusted_flesch_midpoint():
    # AF = 10 * CDF(F, mu=40, sigma=25); at F=40 the CDF is 0.5 -> AF = 5.0
    assert adjusted_flesch(40.0) == pytest.approx(5.0, abs=0.001)


def test_adjusted_flesch_monotonic_and_bounded():
    assert 0.0 <= adjusted_flesch(-50.0) < adjusted_flesch(40.0) < adjusted_flesch(120.0) <= 10.0
