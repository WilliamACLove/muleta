import math

from muleta.text import count_syllables, sentences, words


def flesch_reading_ease(text: str) -> float:
    """Raw Flesch Reading Ease (higher = easier); can exceed 100 or go negative."""
    w = words(text)
    s = sentences(text)
    if not w or not s:
        return 0.0
    syl = sum(count_syllables(x) for x in w)
    score = 206.835 - 1.015 * (len(w) / len(s)) - 84.6 * (syl / len(w))
    return round(score, 2)


def _normal_cdf(x: float, mu: float, sigma: float) -> float:
    """CDF of a normal(mu, sigma) at x, via the error function."""
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def adjusted_flesch(raw_flesch: float) -> float:
    """Bullfighter's Adjusted Flesch (AF), 0..10.

    The vendor transforms the raw Flesch through a normal CDF (mu=40, sigma=25) to
    account for an above-average-education readership: AF = CDF(F, 40, 25). We scale
    to 0..10 so AF shares the Bull Index's range for the composite.
    """
    return round(10.0 * _normal_cdf(raw_flesch, 40.0, 25.0), 2)
