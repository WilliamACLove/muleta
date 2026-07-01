from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from muleta.corpus import Corpus, Entry
from muleta.text import words


@dataclass(frozen=True)
class Hit:
    term: str
    weight: int
    start: int
    end: int
    suggestions: tuple[str, ...] = field(default=())


def weight_factor(n_words: int) -> int:
    """Bull weight factor F, set by document length (per the vendor scorecard)."""
    if n_words < 1000:
        return 2
    if n_words < 10000:
        return 3
    if n_words < 50000:
        return 4
    return 5


def _entry_pattern(entry: Entry) -> re.Pattern:
    """Match any of the entry's explicit surface forms, word-bounded and
    space/hyphen-flexible. Longest forms first so the fullest match wins."""
    alts = []
    for surface in sorted(entry.surfaces(), key=len, reverse=True):
        tokens = re.split(r"[ \-]+", surface.strip())
        alts.append(r"[ \-]+".join(re.escape(t) for t in tokens if t))
    body = "(?:" + "|".join(alts) + ")"
    return re.compile(r"(?<![A-Za-z])" + body + r"(?![A-Za-z])", re.IGNORECASE)


def find_hits(text: str, corpus: Corpus) -> list[Hit]:
    """Word-bounded, case-insensitive matches of corpus terms and their forms."""
    hits: list[Hit] = []
    for entry in corpus.entries():
        for m in _entry_pattern(entry).finditer(text):
            hits.append(Hit(entry.term, entry.weight, m.start(), m.end(), entry.suggestions))
    hits.sort(key=lambda h: h.start)
    return hits


def bull_scores(text: str, corpus: Corpus):
    """Return (raw_bull_index BIr 0..100, bull_index BI 0..10, F, hits).

    Per the vendor formula: F set by word count; for each distinct jargon term with
    Ci occurrences, Wi = min(Ci/F, 1); BIr = 100 - Σ(Bi·Wi); BI = 0 if BIr<0 else BIr/10.
    """
    n = len(words(text))
    hits = find_hits(text, corpus)
    f = weight_factor(n)
    counts: dict[str, int] = defaultdict(int)
    weights: dict[str, int] = {}
    for h in hits:
        counts[h.term] += 1
        weights[h.term] = h.weight
    penalty = sum(weights[t] * min(counts[t] / f, 1.0) for t in counts)
    bir = 100.0 - penalty
    bi = 0.0 if bir < 0 else bir / 10.0
    return round(bir, 2), round(bi, 4), f, hits
