import pytest

from muleta.flesch import flesch_reading_ease


def test_flesch_simple_sentence():
    # "The cat sat." -> words=3, sentences=1, syllables=3
    # 206.835 - 1.015*(3/1) - 84.6*(3/3) = 119.19
    assert flesch_reading_ease("The cat sat.") == pytest.approx(119.19, abs=0.01)


def test_flesch_empty_is_zero():
    assert flesch_reading_ease("") == 0.0
