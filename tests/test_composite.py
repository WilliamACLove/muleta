import pytest

from muleta.composite import FORMULA_VERSION, bull_composite


def test_formula_is_bfc_v2():
    assert FORMULA_VERSION == "bfc-v2"


def test_symmetric_inputs_average():
    # When BI == AF, Pb == Pf == 0.5, so BCI == that value.
    assert bull_composite(5.0, 5.0) == pytest.approx(5.0)
    assert bull_composite(10.0, 10.0) == pytest.approx(10.0)
    assert bull_composite(0.0, 0.0) == pytest.approx(0.0)


def test_worse_component_dominates():
    # The lower (worse) of BI/AF is weighted more heavily, so the composite falls
    # below the plain average of 5.0. Verified against the vendor formula -> ~4.8.
    assert bull_composite(2.0, 8.0) == pytest.approx(4.8, abs=0.05)
    assert bull_composite(2.0, 8.0) < 5.0
    # The weighting is symmetric: it punishes the worse score regardless of which it is.
    assert bull_composite(2.0, 8.0) == pytest.approx(bull_composite(8.0, 2.0))
