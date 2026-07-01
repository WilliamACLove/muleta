FORMULA_VERSION = "bfc-v1"
K_PENALTY = 30.0


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def bull_composite(flesch: float, bull_index: float) -> float:
    """Combine Flesch (higher=clearer) and Bull Index (higher=worse) into 1..10."""
    flesch_norm = _clamp(flesch / 100.0, 0.0, 1.0)
    jargon_penalty = _clamp(bull_index / K_PENALTY, 0.0, 1.0)
    return round(1.0 + 9.0 * (flesch_norm * (1.0 - jargon_penalty)), 1)
