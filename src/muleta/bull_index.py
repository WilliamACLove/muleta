from __future__ import annotations

import re
from dataclasses import dataclass

from muleta.corpus import Corpus
from muleta.text import words


@dataclass(frozen=True)
class Hit:
    term: str
    severity: int
    start: int
    end: int


def find_hits(text: str, corpus: Corpus) -> list[Hit]:
    """Word-bounded, case-insensitive matches of corpus terms."""
    hits: list[Hit] = []
    for entry in corpus.entries():
        pattern = re.compile(
            r"(?<![A-Za-z])" + re.escape(entry.term) + r"(?![A-Za-z])", re.IGNORECASE
        )
        for m in pattern.finditer(text):
            hits.append(Hit(entry.term, entry.severity, m.start(), m.end()))
    hits.sort(key=lambda h: h.start)
    return hits


def bull_index(text: str, corpus: Corpus) -> float:
    n = len(words(text))
    if n == 0:
        return 0.0
    total = sum(h.severity for h in find_hits(text, corpus))
    return round(1000.0 * total / n, 2)
