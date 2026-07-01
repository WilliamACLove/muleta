"""Bull Composite Index — the authentic Bullfighter scoring (bfc-v2).

Recovered verbatim from the vendor scorecard (fightthebull.com/bullscorecard.asp,
Wayback 2009-06-25). The composite weights the Bull Index more heavily as it
worsens (approaches zero), so jargon-laden documents are punished hardest.

bfc-v1 (a transparent flesch*(1-penalty) approximation used before the original
formula was recovered) is preserved below for provenance; bfc-v2 is the default.
"""

import math

FORMULA_VERSION = "bfc-v2"


def bull_composite(bull_index: float, adjusted_flesch: float) -> float:
    """BCI = Pb·BI + Pf·AF, with Pb weighting BI more heavily as BI -> 0.

    BI and AF are both on 0..10. Pb = (15-√BI)/(30-√BI-√AF); Pf is symmetric; Pb+Pf=1.
    """
    sb = math.sqrt(max(bull_index, 0.0))
    sf = math.sqrt(max(adjusted_flesch, 0.0))
    denom = 30.0 - sb - sf
    pb = (15.0 - sb) / denom
    pf = (15.0 - sf) / denom
    return round(pb * bull_index + pf * adjusted_flesch, 1)


# --- bfc-v1 (historical approximation; not used by default) ---
FORMULA_VERSION_V1 = "bfc-v1"
K_PENALTY = 30.0


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def bull_composite_v1(flesch: float, bull_index_density: float) -> float:
    """Original transparent approximation: Flesch normalized, penalized by jargon
    density (1000·Σweight/words). Kept for provenance; superseded by bfc-v2."""
    flesch_norm = _clamp(flesch / 100.0, 0.0, 1.0)
    jargon_penalty = _clamp(bull_index_density / K_PENALTY, 0.0, 1.0)
    return round(1.0 + 9.0 * (flesch_norm * (1.0 - jargon_penalty)), 1)
